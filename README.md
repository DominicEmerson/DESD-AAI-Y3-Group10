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
```

### Access the Application

Open your web browser and visit the following URLs to access the application interfaces:

- **Django Admin Interface**: `http://localhost:8000/admin`
- **MLaaS API**: `http://localhost:8009/api/`
- **Frontend Application**: `http://localhost:8080`