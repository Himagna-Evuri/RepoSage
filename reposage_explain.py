
from pathlib import Path
import joblib
import pandas as pd

# Get the project folder
BASE_DIR = Path(__file__).resolve().parent

# Load the trained model and feature names
model = joblib.load(BASE_DIR / "reposage_model.joblib")
features = joblib.load(BASE_DIR / "reposage_features.joblib")

# Extract feature importance values
importance_values = model.feature_importances_

# Create a DataFrame
importance_df = pd.DataFrame({
    "Feature": features,
    "Importance": importance_values
})

# Sort features by importance
importance_df = importance_df.sort_values(
    by="Importance",
    ascending=False
)

# Display results
print("\n===== RepoSage Feature Importance =====")
print(importance_df.to_string(index=False))
