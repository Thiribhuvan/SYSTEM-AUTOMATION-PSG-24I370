
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)
import joblib

# STEP 1 - Load dataset
df = pd.read_csv("day1_log.csv")

print("DATASET PREVIEW")
print(df.head())

print("\nDataset shape:", df.shape)

# STEP 2 - Check missing values
print("\nMissing values:")
print(df.isnull().sum())

df = df.dropna()

# STEP 3 - Select input features and target
X = df[[
    "temperature",
    "pressure",
    "vibration",
    "current"
]]

y = df["state"]

print("\nState distribution:")
print(y.value_counts())

# STEP 4 - Split training and testing data
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.5,
    random_state=42,
    stratify=y
)

print("\nTraining samples:", len(X_train))
print("Testing samples:", len(X_test))

# STEP 5 - Create Random Forest model
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)   

# STEP 6 - Train model
model.fit(X_train, y_train)

print("\nModel training completed!")

# STEP 7 - Predict test data
y_pred = model.predict(X_test)

# STEP 8 - Calculate accuracy
accuracy = accuracy_score(y_test, y_pred)

print("\nMODEL ACCURACY")
print(f"Accuracy: {accuracy * 100:.2f}%")

# STEP 9 - Classification report
print("\nCLASSIFICATION REPORT")
print(classification_report(
    y_test,
    y_pred,
    zero_division=0
))

# STEP 10 - Confusion matrix
print("\nCONFUSION MATRIX")
print(confusion_matrix(y_test, y_pred))

# STEP 11 - Save trained model
joblib.dump(model, "automation_model.pkl")

print("\nModel saved as automation_model.pkl")

# STEP 12 - Test with new sensor values
new_data = pd.DataFrame([{
    "temperature": 92.5,
    "pressure": 120.4,
    "vibration": 3.2,
    "current": 18.5
}])

prediction = model.predict(new_data)

print("\nNEW SENSOR PREDICTION")
print("Predicted machine state:", prediction[0])
