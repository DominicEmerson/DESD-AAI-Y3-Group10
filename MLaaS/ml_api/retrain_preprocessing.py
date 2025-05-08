"""
preprocessing for retraining: produces 18 features in the correct order for model training.
No scaling, encoding, or one-hot. Only numeric features, column dropping, tariff banding, and NaN handling.
"""
import pandas as pd
import numpy as np
import warnings
import joblib

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

def apply_tariff_bands_cw(df: pd.DataFrame) -> pd.DataFrame:
    """
    Bin 'injuryprognosis' into tariff bands as per notebook logic.
    """
    df = df.copy()
    col = 'injuryprognosis'
    if col not in df.columns:
        warnings.warn(f"Column '{col}' not found for tariff banding. Skipping.")
        return df
    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(25)
    conditions = [
        (df[col] <= 3),
        (df[col] >= 4) & (df[col] <= 6),
        (df[col] >= 7) & (df[col] <= 9),
        (df[col] >= 10) & (df[col] <= 12),
        (df[col] >= 13) & (df[col] <= 15),
        (df[col] >= 16) & (df[col] <= 18),
        (df[col] >= 19) & (df[col] <= 24),
        (df[col] >= 25)
    ]
    choices = list(range(8))
    df[col] = np.select(conditions, choices, default=7).astype(int)
    return df

def drop_unwanted_columns_cw(df: pd.DataFrame, cols_to_drop: list) -> pd.DataFrame:
    """
    Drop columns from DataFrame if present.
    """
    return df.drop(columns=[col for col in cols_to_drop if col in df.columns], errors='ignore')

def retrain_preprocessing_from_queryset(claims_queryset) -> tuple:
    """
    Preprocess a QuerySet of Claim objects for retraining.
    Returns (X, y) where X is a DataFrame of 18 features and y is the target.
    """
    try:
        from claims.models import Claim  # noqa: F401
    except ImportError:
        raise EnvironmentError("Cannot access 'claims' database models. Preprocessing failed.")
    data_list = []
    for claim in claims_queryset:
        accident = getattr(claim, 'accident', None)
        driver = getattr(accident, 'driver', None) if accident else None
        vehicle = getattr(accident, 'vehicle', None) if accident else None
        injury = getattr(accident, 'injury', None) if accident else None
        data = {
            'settlementvalue': claim.settlement_value,
            'injuryprognosis': getattr(injury, 'injury_prognosis', None) if injury else None,
            'generalfixed': claim.general_fixed,
            'generaluplift': claim.general_uplift,
            'generalrest': claim.general_rest,
            'specialhealthexpenses': claim.special_health_expenses,
            'specialtherapy': claim.special_therapy,
            'specialrehabilitation': claim.special_rehabilitation,
            'specialmedications': claim.special_medications,
            'specialadditionalinjury': claim.special_additional_injury,
            'specialearningsloss': claim.special_earnings_loss,
            'specialusageloss': claim.special_usage_loss,
            'specialreduction': claim.special_reduction,
            'specialoverage': claim.special_overage,
            'specialassetdamage': claim.special_asset_damage,
            'specialfixes': claim.special_fixes,
            'specialloanervehicle': claim.special_loaner_vehicle,
            'specialtripcosts': claim.special_trip_costs,
            'specialjourneyexpenses': claim.special_journey_expenses,
            # The rest are dropped by preprocessing
        }
        # Add any extra columns needed for dropping
        data['injurydescription'] = getattr(injury, 'injury_description', None) if injury else None
        data['dominantinjury'] = getattr(injury, 'dominant_injury', None) if injury else None
        data['whiplash'] = int(getattr(injury, 'whiplash', False)) if injury else 0
        data['minorpsychologicalinjury'] = int(getattr(injury, 'minor_psychological_injury', False)) if injury else 0
        data['exceptionalcircumstances'] = int(getattr(injury, 'exceptional_circumstances', False)) if injury else 0
        data['accidenttype'] = getattr(accident, 'accident_type', None) if accident else None
        data['accidentdescription'] = getattr(accident, 'accident_description', None) if accident else None
        data['vehicletype'] = getattr(vehicle, 'vehicle_type', None) if vehicle else None
        data['weatherconditions'] = getattr(accident, 'weather_conditions', None) if accident else None
        data['vehicleage'] = getattr(vehicle, 'vehicle_age', None) if vehicle else None
        data['driverage'] = getattr(driver, 'driver_age', None) if driver else None
        data['numberofpassengers'] = getattr(vehicle, 'number_of_passengers', None) if vehicle else None
        data['policereportfiled'] = int(getattr(accident, 'police_report_filed', False)) if accident else 0
        data['witnesspresent'] = int(getattr(accident, 'witness_present', False)) if accident else 0
        data['gender'] = getattr(driver, 'gender', None) if driver else None
        data['accidentdate'] = getattr(accident, 'accident_date', None) if accident else None
        data['claimdate'] = claim.claim_date
        data_list.append(data)
    if not data_list:
        return pd.DataFrame(), pd.Series(dtype='float64')
    df = pd.DataFrame(data_list)
    df.columns = df.columns.str.lower()
    df = df.dropna(subset=[TARGET_COLUMN])
    for col in NOTEBOOK_REMOVE_VALUES_FROM:
        if col in df.columns:
            df = df[df[col] == 0]
    df = drop_unwanted_columns_cw(df, NOTEBOOK_DROP_COLUMNS)
    df = apply_tariff_bands_cw(df)
    df = drop_unwanted_columns_cw(df, NOTEBOOK_EXPLICIT_CAT_DROP)
    for col in FINAL_FEATURE_COLUMNS_ORDERED:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            df[col] = 0
    X = df[FINAL_FEATURE_COLUMNS_ORDERED]
    y = df[TARGET_COLUMN]
    return X, y