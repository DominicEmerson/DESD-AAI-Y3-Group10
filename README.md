# Machine Learning-Based Insurance Claim Prediction Application

This repository contains a web application that predicts insurance settlement amounts based on user input. The predictive model is integrated into a Django framework.

## Dataset

- **Synthetic_Data_For_Students.csv**: Synthetic data generated and provided for training purposes. It includes various features relevant to insurance claims.
- **clean_df.csv**: A cleaned version of the dataset that is used to train the AI models. Missing values are handled and categorical variables are appropriately encoded.

## Model Training

The model is trained on the cleaned version of the given insurance dataset and saved using pickle. For details on the model training process, please refer to the original project code.

## User Roles and Dashboards

### 1. Admin
- Has full access to the system's functionalities. Can create, update, and delete user accounts, and check the health status of various system components.

### 2. Engineer
- Can manage machine learning models, upload new models, trigger retraining of existing models based on new data, and access logs of prediction requests made to the ML algorithms.

### 3. Finance
- Can view and manage the financial aspects of claims, filtering claims based on various criteria like dates, values, and whether there was a case of whiplash. Thwy can then generate financial reports and/or invoices for selected claims.

### 4. End User
- End users can submit new claims and view the status of their existing claims.

## Usage

### Clone the Repository

To get started, clone the repository using the following command:

```bash
git clone https://github.com/YourUsername/DESD-AAI-Y3-Group10.git
cd DESD-AAI-Y3-Group10
```

### Install Dependencies

Install dependencies by running:

```bash
pip install -r requirements.txt
```

### Run the Application

To start the application, execute the following command:

```bash
docker-compose up --build -d

stop without losing data
docker-compose down

Check if a user exists.

docker exec -it desd-aai-y3-group10-django_app-1 python manage.py shell

from claims.models import CustomUser
print(CustomUser.objects.all())  # Should list all users
exit()
```

============================

## Registering a New ML Model (MLaaS)

To add a new ML model to the system, you need to update the explicit list in:

    MLaaS/ml_api/management/commands/register_models.py

1. **Edit the `models_to_register` list** in that file. Add a new dictionary for your model, e.g.:

    {
        "name": "XGBoost Claim Predictor",
        "version": "20250507",
        "relative_path": "ml_models/xgboost_20250507.pkl",
        "description": "Predicts insurance claims using an XGBoost model.",
        "model_type": "XGBOOST",
        "is_active": True,
    }

   - Make sure the `relative_path` matches the filename in `ml_models/`.
   - Bump the version if you update a model. Only the latest version is marked active.

2. **Run the registration command:**

    ```sh
    docker-compose exec mlaas python manage.py register_models
    ```

   - This will update the database, set the latest version active, and mark old ones as legacy.
   - You'll see output for each model (created, updated, or already exists).

3. **Check registered models:**
   - Use the Django admin, or:
     ```sh
     curl http://localhost:8009/api/algorithms/
     ```

============================

## Preprocessing & Retraining (MLaaS CLI)

To preprocess all claims and get your training data for a new model:

```sh
docker-compose exec mlaas python manage.py shell
```
Then in the shell:
```python
from ml_api import retrain_preprocessing
from claims.models import Claim
qs = Claim.objects.all()
X, y = retrain_preprocessing.retrain_preprocessing_from_queryset(qs)
# Now use X, y to train your model (e.g. XGBoost, sklearn, etc.)
```

- The preprocessing matches the notebook logic: 18 features, correct order, no scaling/encoding.
- If you change the features, update both the retrain_preprocessing and the model registration.

You can also do all of this in the GUI!
============================
