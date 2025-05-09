# ml_api/retrain_preprocessing.py
"""
preprocessing for retraining: produces 18 features in the correct order for model training.
No scaling, encoding, or one-hot. Only numeric features, column dropping, tariff banding, and NaN handling.
"""
import pandas as pd
import numpy as np
import warnings

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
TARGET_COLUMN = 'settlementvalue'

def apply_tariff_bands_cw(df_input: pd.DataFrame) -> pd.DataFrame:
    df = df_input.copy()
    col = 'injuryprognosis'
    if col not in df.columns:
        warnings.warn(f"Column '{col}' not found for tariff banding. Skipping.")
        return df
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(25)
    conditions = [
        (df[col] <= 3), (df[col] >= 4) & (df[col] <= 6), (df[col] >= 7) & (df[col] <= 9),
        (df[col] >= 10) & (df[col] <= 12), (df[col] >= 13) & (df[col] <= 15),
        (df[col] >= 16) & (df[col] <= 18), (df[col] >= 19) & (df[col] <= 24), (df[col] >= 25)
    ]
    choices = list(range(8))
    df[col] = np.select(conditions, choices, default=7).astype(int)
    return df

def drop_unwanted_columns_cw(df: pd.DataFrame, cols_to_drop: list) -> pd.DataFrame:
    return df.drop(columns=[col for col in cols_to_drop if col in df.columns], errors='ignore')

def _preprocess_raw_dataframe_for_retraining(df_raw: pd.DataFrame) -> tuple:
    """
    Core preprocessing logic, takes a raw DataFrame and returns (X, y).
    Assumes df_raw contains columns like 'settlementvalue', 'injuryprognosis',
    'generalfixed', and all other columns needed by the preprocessing steps.
    The column names in df_raw should be lowercase.
    """
    print(f"MLaaS Preprocessing: Received raw DataFrame with columns: {df_raw.columns.tolist()}")
    df = df_raw.copy()
    # df.columns = df.columns.str.lower() # Already done by API data assembly if keys are lowercase

    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Target column '{TARGET_COLUMN}' not found in input DataFrame to MLaaS preprocessing.")
    
    # Convert target to numeric and drop rows where target becomes NaN
    df[TARGET_COLUMN] = pd.to_numeric(df[TARGET_COLUMN], errors='coerce')
    df = df.dropna(subset=[TARGET_COLUMN])
    if df.empty:
        warnings.warn("DataFrame became empty after dropping NaNs in target column during MLaaS preprocessing.")
        return pd.DataFrame(), pd.Series(dtype='float64')

    # Apply NOTEBOOK_REMOVE_VALUES_FROM logic (filter rows based on specific columns being zero)
    for col_remove in NOTEBOOK_REMOVE_VALUES_FROM:
        if col_remove in df.columns:
            try:
                numeric_col = pd.to_numeric(df[col_remove], errors='coerce').fillna(0)
                df = df[numeric_col == 0]
            except Exception as e:
                warnings.warn(f"Could not process column {col_remove} for outlier removal during MLaaS preprocessing: {e}")
        if df.empty:
            warnings.warn(f"DataFrame became empty after filtering on column '{col_remove}' during MLaaS preprocessing.")
            return pd.DataFrame(), pd.Series(dtype='float64')

    df = drop_unwanted_columns_cw(df, NOTEBOOK_DROP_COLUMNS)
    df = apply_tariff_bands_cw(df) 
    df = drop_unwanted_columns_cw(df, NOTEBOOK_EXPLICIT_CAT_DROP)

    # Ensure all FINAL_FEATURE_COLUMNS_ORDERED are present, numeric, and NaNs handled (filled with 0)
    processed_features_dict = {}
    for col_final in FINAL_FEATURE_COLUMNS_ORDERED:
        if col_final in df.columns:
            feature_series = pd.to_numeric(df[col_final], errors='coerce').fillna(0)
        else:
            warnings.warn(f"Expected feature '{col_final}' not found in DataFrame during MLaaS preprocessing. Adding as zeros.")
            feature_series = pd.Series([0.0] * len(df), index=df.index, name=col_final, dtype='float64')
        processed_features_dict[col_final] = feature_series
    
    X = pd.DataFrame(processed_features_dict, index=df.index)
    X = X[FINAL_FEATURE_COLUMNS_ORDERED] # Enforce order

    y = df[TARGET_COLUMN].copy() # Already ensured numeric and NaNs dropped
    
    # Final alignment of X and y indices, just in case any operation misaligned them
    common_index = X.index.intersection(y.index)
    X = X.loc[common_index]
    y = y.loc[common_index]
    
    if X.empty or y.empty:
        warnings.warn("X or y DataFrame became empty at the end of MLaaS preprocessing.")
        return pd.DataFrame(), pd.Series(dtype='float64')
        
    print(f"MLaaS Preprocessing: Produced X shape: {X.shape}, y shape: {y.shape}")
    return X, y

