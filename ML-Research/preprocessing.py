import pandas as pd
from sklearn.preprocessing import MinMaxScaler

DROP_COLUMNS = ['SpecialReduction','SpecialRehabilitation','SpecialMedications','Driver Age',
                'Gender','Accident Date','Claim Date']
BINARY_COLUMNS = ['Exceptional_Circumstances','Minor_Psychological_Injury','Whiplash',
                  'Police Report Filed','Witness Present']
CATEGORY_COLUMNS = ['Dominant injury','Vehicle Type','Weather Conditions','Injury Description',
                    'Accident Description']
NUMERIC_COLUMNS = ['SpecialHealthExpenses','SpecialOverage','GeneralRest',
                    'SpecialAdditionalInjury','SpecialEarningsLoss','SpecialUsageLoss',
                    'SpecialAssetDamage','SpecialFixes','GeneralFixed','GeneralUplift',
                    'SpecialLoanerVehicle','SpecialTripCosts','SpecialJourneyExpenses','SpecialTherapy']
SPECIAL_COLUMN = ['Injury_Prognosis','Number of Passengers']
TARGET_COLUMN = 'SettlementValue'


def extract_int_from_string(df, col):
    df[col] = (
        df[col]
        .str.extract('(\d+)', expand=False)
        .astype('Int64')
    )
    return df


def binary_encode(df, columns, positive_value):
    for column in columns:
        df[column] = df[column].apply(lambda x: 1 if x == positive_value else 0)
        df[column] = df[column].astype('Int8')
    return df


def one_hot_encode(df, columns):
    for column in columns:
        df = pd.concat([df, pd.get_dummies(df[column], prefix=column)], axis=1)
        df = df.drop(column, axis=1)
    return df


def float_columns_to_int(df):
    for column in df.select_dtypes(include='float64'):
        df[column] = df[column].round().astype('Int64')
    return df


def zero_fill_num_columns(df):
    for column in df.select_dtypes(include='number'):
        df[column] = df[column].fillna(0)
    return df

def fill_category_columns(df):
    for column in df.select_dtypes(include='object'):
        df[column] = df[column].fillna('Unknown')
    return df

def preprocess_data(ml_dataset):
    df = ml_dataset.copy()
    df = df.dropna(subset=['SettlementValue'])
    df = df.drop(DROP_COLUMNS, axis=1)
    df = extract_int_from_string(df,'Injury_Prognosis')
    df = df.drop(DROP_COLUMNS, axis=1)
    df = df.drop(CATEGORY_COLUMNS, axis=1)
    df = df.dropna(subset=['SettlementValue','Injury_Prognosis','Exceptional_Circumstances','Whiplash'])
    df['Number of Passengers'] = df['Number of Passengers'].fillna(1)
    df = extract_int_from_string(df,'Injury_Prognosis')
    df = zero_fill_num_columns(df)
    df = fill_category_columns(df)
    df = binary_encode(df,BINARY_COLUMNS,'Yes')
    df = one_hot_encode(df,CATEGORY_COLUMNS)
    df = float_columns_to_int(df)
    min_max_scaler = MinMaxScaler()
    df[NUMERIC_COLUMNS] = min_max_scaler.fit_transform(df[NUMERIC_COLUMNS])
    print("Number of records remaining: " + str(len(df.index)))
    return df