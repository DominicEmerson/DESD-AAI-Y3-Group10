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

import joblib # For loading scaler
import numpy as np
import pandas as pd
from django.conf import settings
from sklearn.preprocessing import RobustScaler # For scaling

# Import models directly from the claims app within the Backend project
from claims.models import Claim

logger = logging.getLogger(__name__)

# --- Constants (Match original script/notebook) ---
DROP_COLUMNS = [
    'SpecialReduction', 'SpecialRehabilitation', 'SpecialMedications',
    'Driver Age', 'Gender', 'Accident Date', 'Claim Date',
    'Accident Description', 'Injury Description'
]
BINARY_COLUMNS = [
    'Exceptional_Circumstances', 'Minor_Psychological_Injury', 'Whiplash',
    'Police Report Filed', 'Witness Present'
]
CATEGORY_COLUMNS = [
    'Dominant injury', 'Vehicle Type', 'Weather Conditions', 'AccidentType'
]
# ** IMPORTANT: Verify this list exactly matches columns scaled in training **
NUMERIC_COLUMNS_FOR_SCALING = [
    'SpecialHealthExpenses', 'SpecialOverage', 'GeneralRest',
    'SpecialAdditionalInjury', 'SpecialEarningsLoss', 'SpecialUsageLoss',
    'SpecialAssetDamage', 'SpecialFixes', 'GeneralFixed', 'GeneralUplift',
    'SpecialLoanerVehicle', 'SpecialTripCosts', 'SpecialJourneyExpenses',
    'SpecialTherapy',
    'Injury_Prognosis', # Assuming this was converted and scaled
]
# TARGET_COLUMN = 'SettlementValue' # Not needed for prediction input

# --- Feature Order Loading ---
# ** IMPORTANT: Create 'final_feature_order.json' **
# Place it in this 'utils' directory. List of column names from X_train.
FINAL_FEATURE_ORDER = None
EXPECTED_FEATURE_COUNT = 54 # Default/fallback - **VERIFY THIS NUMBER**
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


# --- Helper Functions ---

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


# --- Main Preprocessing Function for Single Claim (Scaler Included) ---

def preprocess_single_claim(claim: Claim) -> list:
    """
    Takes fetched Claim object, preprocesses (including scaling),
    ensures correct feature order/count, returns feature vector.

    Requires 'robust_scaler_fitted.joblib' and 'final_feature_order.json'
    in the 'utils' directory for successful execution.

    Args:
        claim: A claims.models.Claim object, fetched with related objects.

    Returns:
        list: A list containing one inner list of processed numeric features.
              Example: [[feat1, feat2, ..., feat54]]
    """
    if not isinstance(claim, Claim):
        raise TypeError("Input must be a claims.models.Claim object.")

    logger.info("Starting preprocessing for Claim ID: %s", claim.pk)
    start_time = pd.Timestamp.now()

    # 1. Construct Dictionary from Claim Object
    try:
        acc = claim.accident
        driver = getattr(acc, 'driver', None)
        vehicle = getattr(acc, 'vehicle', None)
        injury = getattr(acc, 'injury', None)
    except AttributeError as e:
        raise AttributeError("Claim requires related 'accident' object.") from e

    record = { # Fields needed based on original script's logic
        'Claim Date': claim.claim_date,
        'SpecialHealthExpenses': claim.special_health_expenses,
        'SpecialReduction': claim.special_reduction, 'SpecialOverage': claim.special_overage,
        'GeneralRest': claim.general_rest, 'SpecialAdditionalInjury': claim.special_additional_injury,
        'SpecialEarningsLoss': claim.special_earnings_loss, 'SpecialUsageLoss': claim.special_usage_loss,
        'SpecialMedications': claim.special_medications, 'SpecialAssetDamage': claim.special_asset_damage,
        'SpecialRehabilitation': claim.special_rehabilitation, 'SpecialFixes': claim.special_fixes,
        'GeneralFixed': claim.general_fixed, 'GeneralUplift': claim.general_uplift,
        'SpecialLoanerVehicle': claim.special_loaner_vehicle, 'SpecialTripCosts': claim.special_trip_costs,
        'SpecialJourneyExpenses': claim.special_journey_expenses, 'SpecialTherapy': claim.special_therapy,
        'Accident Date': acc.accident_date if acc else None, 'AccidentType': acc.accident_type if acc else None,
        'Accident Description': acc.accident_description if acc else None,
        'Police Report Filed': 'Yes' if acc and acc.police_report_filed else 'No',
        'Witness Present': 'Yes' if acc and acc.witness_present else 'No',
        'Weather Conditions': acc.weather_conditions if acc else None,
        'Driver Age': driver.driver_age if driver else None, 'Gender': driver.gender if driver else None,
        'Vehicle Age': vehicle.vehicle_age if vehicle else None, 'Vehicle Type': vehicle.vehicle_type if vehicle else None,
        'Number of Passengers': vehicle.number_of_passengers if vehicle else None,
        'Injury_Prognosis': injury.injury_prognosis if injury else None,
        'Injury Description': injury.injury_description if injury else None,
        'Dominant injury': injury.dominant_injury if injury else None,
        'Whiplash': 'Yes' if injury and injury.whiplash else 'No',
        'Minor_Psychological_Injury': 'Yes' if injury and injury.minor_psychological_injury else 'No',
        'Exceptional_Circumstances': 'Yes' if injury and injury.exceptional_circumstances else 'No',
    }

    # 2. Create Single-Row DataFrame
    df = pd.DataFrame([record])

    # 3. Apply Preprocessing Steps (Mirroring original script order)
    # Drop columns
    cols_to_drop_present = [col for col in DROP_COLUMNS if col in df.columns]
    if cols_to_drop_present:
        df = df.drop(columns=cols_to_drop_present)

    # Handle specific columns
    df = extract_int_from_string(df, 'Injury_Prognosis')
    if 'Number of Passengers' in df.columns:
        df.loc[:, 'Number of Passengers'] = pd.to_numeric(
            df['Number of Passengers'], errors='coerce'
        ).fillna(1).astype('Int64')
    if 'Vehicle Age' in df.columns:
        df.loc[:, 'Vehicle Age'] = pd.to_numeric(df['Vehicle Age'], errors='coerce')

    # Impute numeric NaNs with 0
    df = zero_fill_num_columns(df)

    # Encoding
    df = binary_encode(df, BINARY_COLUMNS, 'Yes')
    df = one_hot_encode(df, CATEGORY_COLUMNS)

    # --- Scaling Step (Included - Requires scaler file!) ---
    logger.debug("Attempting scaling step...")
    numeric_cols_to_scale = df.columns.intersection(NUMERIC_COLUMNS_FOR_SCALING)
    actual_numeric_cols = df[numeric_cols_to_scale].select_dtypes(include=np.number).columns

    if not actual_numeric_cols.empty:
        try:
            scaler_filename = 'robust_scaler_fitted.joblib'
            utils_dir = os.path.dirname(os.path.abspath(__file__))
            scaler_path = os.path.join(utils_dir, scaler_filename)
            logger.debug("Loading scaler from: %s", scaler_path)

            # This line will raise FileNotFoundError until the file exists
            scaler = joblib.load(scaler_path)
            logger.info("Loaded fitted scaler: %s", scaler_filename)

            # Apply .transform() only
            df.loc[:, actual_numeric_cols] = scaler.transform(df[actual_numeric_cols])
            logger.debug("Applied scaling transformation to %d columns.", len(actual_numeric_cols))

        except FileNotFoundError:
            logger.error("!!! CRITICAL: SCALER FILE MISSING at %s !!!", scaler_path)
            # Re-raise for the view to handle and return an appropriate error
            raise FileNotFoundError(f"Required scaler file not found: {scaler_path}")
        except Exception as e:
            logger.exception("Error during scaling step: %s", e)
            raise ValueError("Failed during the scaling step.") from e
    else:
         logger.warning("No numeric columns found for scaling after encoding.")
    # --- End Scaling Step ---

    # --- Final Checks & Feature Ordering ---
    non_numeric_features = df.select_dtypes(exclude=np.number).columns
    if not non_numeric_features.empty:
        logger.error("Non-numeric columns remain after processing: %s.", non_numeric_features.tolist())
        raise ValueError(f"Preprocessing resulted in non-numeric columns: {non_numeric_features.tolist()}")

    if df.isnull().values.any():
        nan_cols = df.columns[df.isnull().any()].tolist()
        logger.warning("NaNs found in final features: %s. Filling with 0.", nan_cols)
        df = df.fillna(0)

    # Apply final feature order (CRITICAL)
    if FINAL_FEATURE_ORDER:
        logger.debug("Applying final feature order (%d features).", len(FINAL_FEATURE_ORDER))
        missing_cols = set(FINAL_FEATURE_ORDER) - set(df.columns)
        for col in missing_cols:
            df[col] = 0
            logger.warning("Added missing final feature column '%s' with 0.", col)

        extra_cols = set(df.columns) - set(FINAL_FEATURE_ORDER)
        if extra_cols:
             logger.warning("Dropping extra columns not in final feature list: %s", extra_cols)
             df = df.drop(columns=list(extra_cols))

        try:
            df = df[FINAL_FEATURE_ORDER] # Select and reorder
        except KeyError as e:
             logger.error("Failed to select final features. Error: %s", e)
             raise ValueError(f"Could not apply final feature order. Error: {e}")
    else:
         logger.error("Final feature order list ('final_feature_order.json') not loaded. CANNOT PROCEED.")
         raise FileNotFoundError("final_feature_order.json is required for prediction but was not found in utils.")

    # Final count check
    if df.shape[1] != EXPECTED_FEATURE_COUNT:
        logger.error("Final feature count mismatch! Expected %d, got %d.", EXPECTED_FEATURE_COUNT, df.shape[1])
        raise ValueError(f"Preprocessing resulted in {df.shape[1]} features, but expected {EXPECTED_FEATURE_COUNT}.")

    processing_time = (pd.Timestamp.now() - start_time).total_seconds()
    logger.info("Preprocessing for Claim ID %s completed successfully in %.4fs.", claim.pk, processing_time)

    return df.values.tolist() # Return [[feat1, feat2, ...]]