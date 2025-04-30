# ml_api/preprocessing.py

import pandas as pd
from sklearn.preprocessing import RobustScaler
import warnings
import numpy as np


# Assumes this module can import models from the 'claims' app probably needs to be rewritten to actually be able to access the claims db 
try:
    from claims.models import Claim # Import necessary models
    CAN_ACCESS_CLAIMS_DB = True
except ImportError:
    Claim = None
    CAN_ACCESS_CLAIMS_DB = False
    warnings.warn("Cannot import 'claims' models. Preprocessing from DB will fail.")




# Ensure these column names EXACTLY match the keys created when converting QuerySet to dict
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
NUMERIC_COLUMNS_FOR_SCALING = [ # Renamed to clarify purpose
    'SpecialHealthExpenses', 'SpecialOverage', 'GeneralRest',
    'SpecialAdditionalInjury', 'SpecialEarningsLoss', 'SpecialUsageLoss',
    'SpecialAssetDamage', 'SpecialFixes', 'GeneralFixed', 'GeneralUplift',
    'SpecialLoanerVehicle', 'SpecialTripCosts', 'SpecialJourneyExpenses',
    'SpecialTherapy'
]
TARGET_COLUMN = 'SettlementValue'



# Helper Functions
def extract_int_from_string(df, col):
    """Extracts first integer from a string column, converts to Int64."""
    if col in df.columns:
        # Use .loc to avoid SettingWithCopyWarning if df is a slice
        df.loc[:, col] = pd.to_numeric(
            df[col].astype(str).str.extract(r'(\d+)', expand=False), errors='coerce'
        ).astype('Int64')
    else:
        warnings.warn(f"Column '{col}' not found for integer extraction.")
    return df

def binary_encode(df, columns, positive_value='Yes'):
    """Converts specified columns to 0/1 based on positive_value."""
    for column in columns:
        if column in df.columns:
            # Fill NaN before applying logic
            df.loc[:, column] = df[column].fillna('No')
            df.loc[:, column] = df[column].apply(
                lambda x: 1 if str(x) == positive_value else 0
            ).astype('Int8')
        else:
            warnings.warn(f"Column '{column}' not found for binary encoding.")
    return df

def one_hot_encode(df, columns):
    """Performs one-hot encoding (as int type) and drops original columns."""
    df_processed = df.copy() # Work on a copy to avoid modifying original during loop
    for column in columns:
        if column in df_processed.columns:
            # Fill NaN and ensure string type for get_dummies
            df_processed.loc[:, column] = df_processed[column].fillna('Unknown').astype(str)

            # Specify dtype=int for 0/1 output
            dummies = pd.get_dummies(
                df_processed[column], prefix=column, dummy_na=False, dtype=int
            )
            # Use original df index for concatenation if indexes differ
            dummies.index = df_processed.index
            df_processed = pd.concat([df_processed, dummies], axis=1)
            df_processed = df_processed.drop(column, axis=1)
        else:
            warnings.warn(f"Column '{column}' not found for one-hot encoding.")
    return df_processed

def float_columns_to_int(df):
    """Rounds float columns and converts to nullable Int64."""
    df_processed = df.copy()
    float_cols = df_processed.select_dtypes(include='float64').columns
    for column in float_cols:
        # Avoid converting columns that might be intentionally float (like scaled ones if kept)
        # This might need adjustment based on whether scaling is the last step
        df_processed.loc[:, column] = df_processed[column].round().astype('Int64')
    return df_processed


def zero_fill_num_columns(df):
    """Fills NaN values in specified numeric columns with 0."""
    # Only fill NaNs in columns intended for scaling or other numeric processing
    # Avoid filling NaNs in columns like 'Driver Age' if they have specific handling
    cols_to_fill = df.select_dtypes(include=np.number).columns.intersection(
        NUMERIC_COLUMNS_FOR_SCALING + [TARGET_COLUMN] # Include target for safety
    )
    if not cols_to_fill.empty:
         df.loc[:, cols_to_fill] = df[cols_to_fill].fillna(0)
         print(f"Filled NaNs with 0 in {len(cols_to_fill)} numeric columns.")
    return df




def preprocess_data_from_queryset(claims_queryset):
    """
    Takes a Django QuerySet of Claim objects, converts to DataFrame,
    and applies preprocessing steps.

    Args:
        claims_queryset: A Django QuerySet for claims.models.Claim,
                         ideally with select_related/prefetch_related applied.

    Returns:
        tuple: (pd.DataFrame: Processed features X, pd.Series: Processed target y)
               Returns empty DataFrame/Series if no valid data.
    Raises:
        ValueError: If essential steps fail (e.g., target missing).
    """
    if not CAN_ACCESS_CLAIMS_DB:
        raise EnvironmentError("Cannot access 'claims' database models. Preprocessing failed.")

    start_time = pd.Timestamp.now()
    print("--- Starting Preprocessing from QuerySet ---")

    # Convert QuerySet to List of Dictionaries
    data_list = []
    required_relations = ['accident', 'accident__driver', 'accident__vehicle', 'accident__injury'] # Check these exist
    for claim in claims_queryset:
        # Basic check for related objects existence before accessing attributes
        has_accident = hasattr(claim, 'accident') and claim.accident is not None
        has_driver = has_accident and hasattr(claim.accident, 'driver') and claim.accident.driver is not None
        has_vehicle = has_accident and hasattr(claim.accident, 'vehicle') and claim.accident.vehicle is not None
        has_injury = has_accident and hasattr(claim.accident, 'injury') and claim.accident.injury is not None

        record = {
            # Claim fields
            TARGET_COLUMN: claim.settlement_value,
            'Claim Date': claim.claim_date,
            'SpecialHealthExpenses': claim.special_health_expenses,
            'SpecialReduction': claim.special_reduction,
            'SpecialOverage': claim.special_overage,
            'GeneralRest': claim.general_rest,
            'SpecialAdditionalInjury': claim.special_additional_injury,
            'SpecialEarningsLoss': claim.special_earnings_loss,
            'SpecialUsageLoss': claim.special_usage_loss,
            'SpecialMedications': claim.special_medications,
            'SpecialAssetDamage': claim.special_asset_damage,
            'SpecialRehabilitation': claim.special_rehabilitation,
            'SpecialFixes': claim.special_fixes,
            'GeneralFixed': claim.general_fixed,
            'GeneralUplift': claim.general_uplift,
            'SpecialLoanerVehicle': claim.special_loaner_vehicle,
            'SpecialTripCosts': claim.special_trip_costs,
            'SpecialJourneyExpenses': claim.special_journey_expenses,
            'SpecialTherapy': claim.special_therapy,
            # Accident fields (check existence)
            'Accident Date': claim.accident.accident_date if has_accident else None,
            'AccidentType': claim.accident.accident_type if has_accident else None,
            'Accident Description': claim.accident.accident_description if has_accident else None,
            'Police Report Filed': 'Yes' if has_accident and claim.accident.police_report_filed else 'No',
            'Witness Present': 'Yes' if has_accident and claim.accident.witness_present else 'No',
            'Weather Conditions': claim.accident.weather_conditions if has_accident else None,
            # Driver fields (check existence)
            'Driver Age': claim.accident.driver.driver_age if has_driver else None,
            'Gender': claim.accident.driver.gender if has_driver else None,
             # Vehicle fields (check existence)
            'Vehicle Age': claim.accident.vehicle.vehicle_age if has_vehicle else None, 
            'Vehicle Type': claim.accident.vehicle.vehicle_type if has_vehicle else None,
            'Number of Passengers': claim.accident.vehicle.number_of_passengers if has_vehicle else None,
            # Injury fields (check existence)
            'Injury_Prognosis': claim.accident.injury.injury_prognosis if has_injury else None, # Renamed column? Check consistency
            'Injury Description': claim.accident.injury.injury_description if has_injury else None,
            'Dominant injury': claim.accident.injury.dominant_injury if has_injury else None, # Renamed column?
            'Whiplash': 'Yes' if has_injury and claim.accident.injury.whiplash else 'No',
            'Minor_Psychological_Injury': 'Yes' if has_injury and claim.accident.injury.minor_psychological_injury else 'No',
            'Exceptional_Circumstances': 'Yes' if has_injury and claim.accident.injury.exceptional_circumstances else 'No',
        }
        data_list.append(record)

    if not data_list:
        warnings.warn("QuerySet resulted in an empty list. No data to preprocess.")
        return pd.DataFrame(), pd.Series(dtype='float64') # Return empty with target dtype

    df = pd.DataFrame(data_list)
    initial_record_count = len(df)
    print(f"Converted QuerySet to DataFrame: {initial_record_count} records.")

    

    # Ensure target exists and drop rows with missing target
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Target column '{TARGET_COLUMN}' not found in constructed DataFrame.")
    df = df.dropna(subset=[TARGET_COLUMN])
    if df.empty:
         warnings.warn("No records left after dropping rows with missing target.")
         return pd.DataFrame(), pd.Series(dtype='float64')
    print(f"Records after target NaN drop: {len(df)}")

    # Drop unwanted columns (robustly check if they exist in df)
    cols_to_drop_present = [col for col in DROP_COLUMNS if col in df.columns]
    if cols_to_drop_present:
        df = df.drop(columns=cols_to_drop_present)
        print(f"Dropped {len(cols_to_drop_present)} columns listed in DROP_COLUMNS.")

    # Handle specific columns
    # Ensure column names match exactly what was created in the dict
    df = extract_int_from_string(df, 'Injury_Prognosis')
    if 'Number of Passengers' in df.columns:
        df.loc[:, 'Number of Passengers'] = pd.to_numeric(
            df['Number of Passengers'], errors='coerce'
        ).fillna(1).astype('Int64') # Default to 1 passenger if missing

    # Drop rows with NaNs in potentially critical feature columns (adjust list if needed)
    critical_check_cols = [
        col for col in ['Injury_Prognosis', 'Exceptional_Circumstances', 'Whiplash']
        if col in df.columns
    ]
    if critical_check_cols:
        initial_len_crit = len(df)
        df = df.dropna(subset=critical_check_cols)
        print(f"Records after critical NaN drop ({critical_check_cols}): {len(df)} (removed {initial_len_crit - len(df)})")
        if df.empty:
            warnings.warn("No records left after dropping critical feature NaNs.")
            return pd.DataFrame(), pd.Series(dtype='float64')

    # Impute remaining numeric NaNs (defined numeric columns) with 0
    df = zero_fill_num_columns(df) # Fills NaNs in NUMERIC_COLUMNS_FOR_SCALING + TARGET_COLUMN

    # Encoding (Binary and One-Hot)
    df = binary_encode(df, BINARY_COLUMNS, 'Yes')
    df = one_hot_encode(df, CATEGORY_COLUMNS) # Creates 0/1 int columns

    # Scaling (RobustScaler on specified numeric columns)
    numeric_cols_present = df.columns.intersection(NUMERIC_COLUMNS_FOR_SCALING)
    numeric_data = df[numeric_cols_present].select_dtypes(include=np.number)
    if not numeric_data.empty:
        scaler = RobustScaler()
        # Use .loc to assign back correctly
        df.loc[:, numeric_data.columns] = scaler.fit_transform(numeric_data)
        print(f"Scaled {len(numeric_data.columns)} numeric columns using RobustScaler.")
    else:
        warnings.warn("No valid numeric columns found to scale among NUMERIC_COLUMNS_FOR_SCALING list.")


    # Final Type Conversion (Optional: Convert floats back to Int)
    # Comment out if you want to keep scaled features as floats
    # df = float_columns_to_int(df)


    
    if TARGET_COLUMN not in df.columns:
        raise ValueError("Target column lost during processing.")

    y = df[TARGET_COLUMN]
    X = df.drop(columns=[TARGET_COLUMN])

    # Ensure features are numeric before returning
    non_numeric_features = X.select_dtypes(exclude=np.number).columns
    if not non_numeric_features.empty:
        warnings.warn(f"Non-numeric columns found in features (X) after processing: {non_numeric_features.tolist()}. Check steps. Dropping them.")
        X = X.select_dtypes(include=np.number)

    # Check for NaNs introduced during processing
    if X.isnull().values.any():
        warnings.warn("NaNs found in final features (X). Consider imputation or review preprocessing steps.")
        # Example: Impute with median (use with caution)
        # X = X.fillna(X.median())
    if y.isnull().values.any():
        warnings.warn("NaNs found in final target (y). Consider imputation or review.")
        # y = y.fillna(y.median())


    end_rows = len(df)
    processing_time = (pd.Timestamp.now() - start_time).total_seconds()
    print(f"--- Preprocessing complete. Final records: {end_rows} ---")
    print(f"Rows removed: {initial_record_count - end_rows}")
    print(f"Final features count: {X.shape[1]}")
    print(f"Preprocessing time: {processing_time:.2f} seconds")

    return X, y