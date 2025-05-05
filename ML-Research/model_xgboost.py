
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import xgboost
import shap
from sklearn.model_selection import train_test_split
from sklearn.metrics import root_mean_squared_error, r2_score, mean_absolute_percentage_error

############
# Database naming format
# REMOVE_VALUES_FROM = ['SpecialHealthExpenses','SpecialFixes',
#                       'SpecialRehabilitation','SpecialAdditionalInjury'
# ]
# DROP_COLUMNS = [
#     'SpecialReduction', 'SpecialRehabilitation', 'SpecialMedications',
#     'Driver Age', 'Gender', 'Accident Date', 'Claim Date',
#     'Accident Description', 'Injury Description', 'Vehicle Age',
#     'Police Report Filed', 'Witness Present', 'Dominant injury',
#     'Vehicle Type', 'Weather Conditions','Number of Passengers',
#     'Accident Description', 'Injury Description',
# ]
# CATEGORY_COLUMNS = [
#     'AccidentType','Exceptional_Circumstances', 'Minor_Psychological_Injury', 'Whiplash',
# ]

# def apply_tariff_bands(df):
#     # create bins for injury prognosis based on the whiplash tariff scale
#     for idx, row in df.iterrows():
#         if df.at[idx, 'Injury_Prognosis'] <= 3:
#             df.at[idx, 'Injury_Prognosis'] = 0
#         elif 4 <= df.at[idx, 'Injury_Prognosis'] <= 6:
#             df.at[idx, 'Injury_Prognosis'] = 1
#         elif 7 <= df.at[idx, 'Injury_Prognosis'] <= 9:
#             df.at[idx, 'Injury_Prognosis'] = 2
#         elif 10 <= df.at[idx, 'Injury_Prognosis'] <= 12:
#             df.at[idx, 'Injury_Prognosis'] = 3
#         elif 13<= df.at[idx, 'Injury_Prognosis'] <= 15:
#             df.at[idx, 'Injury_Prognosis'] = 4
#         elif 16 <= df.at[idx, 'Injury_Prognosis'] <= 18:
#             df.at[idx, 'Injury_Prognosis'] = 5
#         elif 19 <= df.at[idx, 'Injury_Prognosis'] <= 24:
#             df.at[idx, 'Injury_Prognosis'] = 6
        
#         # if we return an Injury_Prognosis value of 7 
#         # this must be flagged as prediction warning
#         elif 25 <= df.at[idx, 'Injury_Prognosis']:
#             df.at[idx, 'Injury_Prognosis'] = 7

#     df['Injury_Prognosis'] = df['Injury_Prognosis'].astype('category')
#     return df

########


#########
# csv file naming format
REMOVE_VALUES_FROM = ['specialhealthexpenses','specialfixes','specialrehabilitation','specialadditionalinjury']
DROP_COLUMNS = ['driverage','vehicleage','accidentdate','claimdate','policereportfiled','witnesspresent','dominantinjury','vehicletype','weatherconditions','gender','numberofpassengers', 'accidentdescription', 'injurydescription']
CATEGORY_COLUMNS = ['accidenttype','exceptionalcircumstances', 'minorpsychologicalinjury', 'whiplash',]


def apply_tariff_bands(df):
    # create bins for injury prognosis based on the whiplash tariff scale
    for idx, row in df.iterrows():
        if df.at[idx, 'injuryprognosis'] <= 3:
            df.at[idx, 'injuryprognosis'] = 0
        elif 4 <= df.at[idx, 'injuryprognosis'] <= 6:
            df.at[idx, 'injuryprognosis'] = 1
        elif 7 <= df.at[idx, 'injuryprognosis'] <= 9:
            df.at[idx, 'injuryprognosis'] = 2
        elif 10 <= df.at[idx, 'injuryprognosis'] <= 12:
            df.at[idx, 'injuryprognosis'] = 3
        elif 13<= df.at[idx, 'injuryprognosis'] <= 15:
            df.at[idx, 'injuryprognosis'] = 4
        elif 16 <= df.at[idx, 'injuryprognosis'] <= 18:
            df.at[idx, 'injuryprognosis'] = 5
        elif 19 <= df.at[idx, 'injuryprognosis'] <= 24:
            df.at[idx, 'injuryprognosis'] = 6
        
        # if we return an injuryprognosis value of 7 
        # this must be flagged as prediction warning
        elif 25 <= df.at[idx, 'injuryprognosis']:
            df.at[idx, 'injuryprognosis'] = 7

    df['injuryprognosis'] = df['injuryprognosis'].astype('category')
    return df

#############

def drop_outlier_values(df):
    
    # remove rows with values in these columns - we must flag up prediction warning
    # when there are values in these columns exceeding a certain threshold (based on model MAPE score?)
    for idx, row in df.iterrows():
        for col in REMOVE_VALUES_FROM:
            if df.at[idx, col] != 0:
                df.drop(idx, inplace=True)
                break
    return df


def convert_columns_to_category(df):
    for col in CATEGORY_COLUMNS:
        if col in df.columns:
            df[col] = df[col].astype('category')


def drop_unwanted_columns(df):
    df.drop(columns=DROP_COLUMNS, inplace=True)
    return df


def log_convert_targets(df):
    # run this on the target column before predictions, to reduce skewness
    df[0] = np.log1p(df[0])
    return df

def inverse_log_convert_targets(df):
    # run this on the target column after predictions, to return to original scale
    df[0] = np.expm1(df[0])
    return df


df = pd.read_csv('clean_df.csv') # column names are using
df = drop_unwanted_columns(df)
df = drop_outlier_values(df)
df = apply_tariff_bands(df)
df = convert_columns_to_category(df)

df.head()
# apply log1p to settlementvalue to reduce skewness
df['settlementvalue'] = np.log1p(df['settlementvalue'])
for col in CATEGORY_COLUMNS:
    if col in df.columns:
        df[col] = df[col].astype('category')

X = df.drop("settlementvalue", axis=1) # Independent variables
y = df.settlementvalue # Dependent variable
log_convert_targets(y)

# Split into train and test 
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=1)

# With log1p applied to settlementvalue
# Train a machine learning model
xgb = xgboost.XGBRegressor(n_estimators=100, eval_metric='rmsle', early_stopping_rounds=10, enable_categorical=True, verbosity=2)
# xgb.fit(X_train, y_train)
xgb.fit(X_train, y_train, eval_set=[(X_test, y_test)])

# Retrieve the RMSLE values from the training process
results = xgb.evals_result()
epochs = len(results['validation_0']['rmsle'])
x_axis = range(0, epochs)

# Plot the RMSLE values
plt.figure()
plt.plot(x_axis, results['validation_0']['rmsle'], label='Test')
plt.legend()
plt.xlabel('Number of Boosting Rounds')
plt.ylabel('RMSLE')
plt.title('XGBoost RMSLE Performance')
plt.show()

# Make predictions and evaluate the final RMSLE on the test set
y_pred = xgb.predict(X_test)
# Calculate RMSLE
final_rmsle = np.sqrt(np.mean(np.square(np.log1p(y_pred) - np.log1p(y_test))))
print(f"Final RMSLE on test set: {final_rmsle:.4f}")
y_pred = inverse_log_convert_targets(y_pred)
y_test = inverse_log_convert_targets(y_test)
print(f"r2 score: {r2_score(y_pred, y_test)}")
print(f"MAPE score: {mean_absolute_percentage_error(y_pred, y_test)}")
print(f"RMSE_score: {root_mean_squared_error(y_pred, y_test)}")


plt.figure(figsize=(8, 8))
plt.scatter(y_test, y_pred, alpha=0.5)
plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2, label='Perfect Prediction (y=x)') # Add y=x line
plt.xlabel("Actual Settlement Amount (£)")
plt.ylabel("Predicted Settlement Amount (£)")
plt.title("Predicted vs. Actual Settlement Amounts")
plt.legend()
plt.grid(True)
plt.show()

explainer = shap.Explainer(xgb)
xgb_shap_values = explainer.shap_values(X_test)
shap.summary_plot(xgb_shap_values, X_test)

shap.decision_plot(explainer.expected_value, xgb_shap_values, X_test.columns)