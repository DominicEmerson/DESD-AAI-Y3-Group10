# Backend/utils/preprocessing.py
"""
Preprocessing utilities for single claim prediction, based on original script.

Handles data cleaning, encoding, scaling, and feature preparation.
Requires 'robust_scaler_fitted.joblib' and 'final_feature_order.json'
to be present in this 'utils' directory for successful execution.
"""
import json
import logging
import os
import warnings 
import numpy as np
import pandas as pd
from django.conf import settings

# Import models directly from the claims app within the backend
from claims.models import Claim, Driver, Accident, Vehicle, Injury

logger = logging.getLogger(__name__)

# --- Constants (from notebook) ---
NOTEBOOK_REMOVE_VALUES_FROM = [
    'specialhealthexpenses', 'specialfixes', 'specialrehabilitation', 'specialadditionalinjury'
]
NOTEBOOK_DROP_COLUMNS = [
    'driverage', 'vehicleage', 'accidentdate', 'claimdate', 'policereportfiled',
    'witnesspresent', 'dominantinjury', 'vehicletype', 'weatherconditions', 'gender',
    'numberofpassengers', 'accidentdescription', 'injurydescription'
]
NOTEBOOK_EXPLICIT_CAT_DROP = [
    'accidenttype', 'exceptionalcircumstances', 'minorpsychologicalinjury', 'whiplash'
]
FINAL_FEATURE_COLUMNS_ORDERED = [
    'injuryprognosis', 'generalfixed', 'generaluplift', 'generalrest', 'specialhealthexpenses',
    'specialtherapy', 'specialrehabilitation', 'specialmedications', 'specialadditionalinjury',
    'specialearningsloss', 'specialusageloss', 'specialreduction', 'specialoverage',
    'specialassetdamage', 'specialfixes', 'specialloanervehicle', 'specialtripcosts', 'specialjourneyexpenses'
]

# --- Feature Order Loading ---
# ** IMPORTANT: Create 'final_feature_order.json' **
FINAL_FEATURE_ORDER = None
EXPECTED_FEATURE_COUNT = 54 
try:
    utils_dir = os.path.dirname(os.path.abspath(__file__))
    final_features_path = os.path.join(utils_dir, 'final_feature_order.json')
    with open(final_features_path, 'r') as f:
        FINAL_FEATURE_ORDER = json.load(f)
    EXPECTED_FEATURE_COUNT = len(FINAL_FEATURE_ORDER)
    logger.info("Loaded final feature order (%d features) from utils/final_feature_order.json.", EXPECTED_FEATURE_COUNT)
except FileNotFoundError:
    logger.error( # Changed to ERROR as this file is critical
        "*** CRITICAL: 'final_feature_order.json' not found in utils directory! "
        "Cannot guarantee correct feature order for prediction. "
        "Prediction will likely fail or be incorrect. "
        "Using feature count %d as fallback check.", EXPECTED_FEATURE_COUNT
    )
except Exception as e:
    logger.error("Error loading final_feature_order.json: %s. Feature order check might fail.", e, exc_info=True)


# --- Helper Functions ---d

def extract_int_from_string(df: pd.DataFrame, col: str) -> pd.DataFrame:
    """Extracts first integer from a string column, converts to Int64."""
    if col in df.columns:
        df.loc[:, col] = pd.to_numeric(
            df[col].astype(str).str.extract(r'(\d+)', expand=False), errors='coerce'
        ).astype('Int64')
    else:
        logger.warning("Column '%s' not found for integer extraction.", col)
    return df

def binary_encode(df: pd.DataFrame, columns: list, positive_value: str = 'Yes') -> pd.DataFrame:
    """Converts specified columns to 0/1 based on positive_value."""
    for column in columns:
        if column in df.columns:
            df.loc[:, column] = df[column].fillna('No').astype(str)
            df.loc[:, column] = df[column].apply(
                lambda x: 1 if x == positive_value else 0
            ).astype('Int8')
        else:
            logger.warning("Column '%s' not found for binary encoding.", column)
    return df

def one_hot_encode(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """Performs one-hot encoding (as int type) and drops original columns."""
    df_processed = df.copy()
    for column in columns:
        if column in df_processed.columns:
            df_processed.loc[:, column] = df_processed[column].fillna('Unknown').astype(str)
            try:
                dummies = pd.get_dummies(
                    df_processed[column], prefix=column, dummy_na=False, dtype=int
                )
                dummies.index = df_processed.index
                df_processed = pd.concat([df_processed, dummies], axis=1)
                df_processed = df_processed.drop(column, axis=1)
            except Exception as e:
                logger.error("Error during one-hot encoding for column '%s': %s", column, e, exc_info=True)
                raise ValueError(f"One-hot encoding failed for {column}") from e
        else:
            logger.warning("Column '%s' not found for one-hot encoding.", column)
    return df_processed

def zero_fill_num_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Fills NaN values in *all* present numeric columns with 0."""
    numeric_cols = df.select_dtypes(include=np.number).columns
    if not numeric_cols.empty:
        df.loc[:, numeric_cols] = df[numeric_cols].fillna(0)
        logger.debug("Filled NaNs with 0 in %d numeric columns.", len(numeric_cols))
    return df


# --- Preprocessing Functions (from notebook, adapted) ---
def apply_tariff_bands_cw(df_: pd.DataFrame):
    df = df_.copy()
    col_name = 'injuryprognosis'
    if col_name not in df.columns:
        warnings.warn(f"Column '{col_name}' not found for tariff banding. Skipping.")
        return df
    df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
    df[col_name] = df[col_name].fillna(25)
    conditions = [
        (df[col_name] <= 3),
        (df[col_name] >= 4) & (df[col_name] <= 6),
        (df[col_name] >= 7) & (df[col_name] <= 9),
        (df[col_name] >= 10) & (df[col_name] <= 12),
        (df[col_name] >= 13) & (df[col_name] <= 15),
        (df[col_name] >= 16) & (df[col_name] <= 18),
        (df[col_name] >= 19) & (df[col_name] <= 24),
        (df[col_name] >= 25)
    ]
    choices = [0, 1, 2, 3, 4, 5, 6, 7]
    df[col_name] = np.select(conditions, choices, default=7)
    df[col_name] = df[col_name].astype(int)
    return df

def drop_unwanted_columns_cw(df_: pd.DataFrame, cols_to_drop_list: list):
    df = df_.copy()
    existing_cols_to_drop = [col for col in cols_to_drop_list if col in df.columns]
    if existing_cols_to_drop:
        df = df.drop(columns=existing_cols_to_drop)
        logger.debug(f"Dropped columns: {existing_cols_to_drop}")
    return df

# --- Main Internal Preprocessing Function ---
def _preprocess_dataframe_for_prediction(raw_df: pd.DataFrame) -> pd.DataFrame:
    logger.debug("Starting internal preprocessing for prediction.")
    df = raw_df.copy()
    df.columns = df.columns.str.lower()
    # Warn if any outlier columns are non-zero
    for col in NOTEBOOK_REMOVE_VALUES_FROM:
        if col in df.columns and (df[col] != 0).any():
            warnings.warn(f"Column '{col}' has non-zero value(s) for prediction. Model was trained with these as outliers.")
            logger.warning(f"Column '{col}' has non-zero value(s) for prediction. Model was trained with these as outliers.")
    # Drop columns as per notebook
    df = drop_unwanted_columns_cw(df, NOTEBOOK_DROP_COLUMNS)
    df = apply_tariff_bands_cw(df)
    df = drop_unwanted_columns_cw(df, NOTEBOOK_EXPLICIT_CAT_DROP)
    # Fill NaNs in numeric features with 0 (optionally, use medians from training)
    for col in df.columns:
        if col in FINAL_FEATURE_COLUMNS_ORDERED and df[col].isnull().any():
            logger.warning(f"Filling NaNs in '{col}' with 0 for prediction.")
            df[col] = df[col].fillna(0)
    # Ensure all features are numeric
    for col in FINAL_FEATURE_COLUMNS_ORDERED:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    # Select and order final features
    missing_cols = [col for col in FINAL_FEATURE_COLUMNS_ORDERED if col not in df.columns]
    for col in missing_cols:
        df[col] = 0
        logger.warning(f"Added missing feature column '{col}' with 0.")
    df = df[FINAL_FEATURE_COLUMNS_ORDERED]
    return df

# --- Helper for Data Sourcing ---
def get_required_source_columns():
    """Return all lowercase column names needed from the models for DataFrame construction."""
    # This is the union of all columns used in the notebook before dropping
    return [
        'injuryprognosis', 'injurydescription', 'dominantinjury', 'whiplash', 'minorpsychologicalinjury',
        'exceptionalcircumstances', 'generalfixed', 'generaluplift', 'generalrest', 'specialhealthexpenses',
        'specialtherapy', 'specialrehabilitation', 'specialmedications', 'specialadditionalinjury',
        'specialearningsloss', 'specialusageloss', 'specialreduction', 'specialoverage', 'specialassetdamage',
        'specialfixes', 'specialloanervehicle', 'specialtripcosts', 'specialjourneyexpenses',
        'accidenttype', 'accidentdescription', 'vehicletype', 'weatherconditions', 'vehicleage',
        'driverage', 'numberofpassengers', 'policereportfiled', 'witnesspresent', 'gender',
        'accidentdate', 'claimdate'
    ]

# --- Django Model to DataFrame Converter ---
def create_dataframe_from_claim(claim_instance, driver_instance, accident_instance, vehicle_instance, injury_instance):
    """
    Convert Django model instances to a single-row DataFrame with columns matching the notebook's raw data.
    All keys must be lowercase and match the notebook/clean_df.csv columns.
    """
    data = {}
    # Injury
    data['injuryprognosis'] = [injury_instance.injury_prognosis if injury_instance else None]
    data['injurydescription'] = [injury_instance.injury_description if injury_instance else None]
    data['dominantinjury'] = [injury_instance.dominant_injury if injury_instance else None]
    data['whiplash'] = [int(getattr(injury_instance, 'whiplash', False)) if injury_instance else 0]
    data['minorpsychologicalinjury'] = [int(getattr(injury_instance, 'minor_psychological_injury', False)) if injury_instance else 0]
    data['exceptionalcircumstances'] = [int(getattr(injury_instance, 'exceptional_circumstances', False)) if injury_instance else 0]
    # Claim
    data['generalfixed'] = [claim_instance.general_fixed]
    data['generaluplift'] = [claim_instance.general_uplift]
    data['generalrest'] = [claim_instance.general_rest]
    data['specialhealthexpenses'] = [claim_instance.special_health_expenses]
    data['specialtherapy'] = [claim_instance.special_therapy]
    data['specialrehabilitation'] = [claim_instance.special_rehabilitation]
    data['specialmedications'] = [claim_instance.special_medications]
    data['specialadditionalinjury'] = [claim_instance.special_additional_injury]
    data['specialearningsloss'] = [claim_instance.special_earnings_loss]
    data['specialusageloss'] = [claim_instance.special_usage_loss]
    data['specialreduction'] = [claim_instance.special_reduction]
    data['specialoverage'] = [claim_instance.special_overage]
    data['specialassetdamage'] = [claim_instance.special_asset_damage]
    data['specialfixes'] = [claim_instance.special_fixes]
    data['specialloanervehicle'] = [claim_instance.special_loaner_vehicle]
    data['specialtripcosts'] = [claim_instance.special_trip_costs]
    data['specialjourneyexpenses'] = [claim_instance.special_journey_expenses]
    # Accident
    data['accidenttype'] = [accident_instance.accident_type if accident_instance else None]
    data['accidentdescription'] = [accident_instance.accident_description if accident_instance else None]
    data['vehicletype'] = [vehicle_instance.vehicle_type if vehicle_instance else None]
    data['weatherconditions'] = [accident_instance.weather_conditions if accident_instance else None]
    data['vehicleage'] = [vehicle_instance.vehicle_age if vehicle_instance else None]
    data['driverage'] = [driver_instance.driver_age if driver_instance else None]
    data['numberofpassengers'] = [vehicle_instance.number_of_passengers if vehicle_instance else None]
    data['policereportfiled'] = [int(getattr(accident_instance, 'police_report_filed', False)) if accident_instance else 0]
    data['witnesspresent'] = [int(getattr(accident_instance, 'witness_present', False)) if accident_instance else 0]
    data['gender'] = [driver_instance.gender if driver_instance else None]
    data['accidentdate'] = [accident_instance.accident_date if accident_instance else None]
    data['claimdate'] = [claim_instance.claim_date]
    return pd.DataFrame(data)

# --- Main Public Function ---
def preprocess_single_claim_for_prediction(claim_instance, driver_instance, accident_instance, vehicle_instance, injury_instance):
    """
    Orchestrates the process: builds DataFrame, applies preprocessing, returns 18 features as an ordered list.
    """
    logger.info(f"Preprocessing claim {claim_instance.id} for prediction.")
    raw_df = create_dataframe_from_claim(
        claim_instance, driver_instance, accident_instance, vehicle_instance, injury_instance
    )
    processed_df = _preprocess_dataframe_for_prediction(raw_df)
    features = processed_df.iloc[0].tolist()
    logger.debug(f"Processed features: {features}")
    return features