import joblib
import pandas as pd

model = joblib.load("reposage_model.joblib")
features = joblib.load("reposage_features.joblib")

sample_commit = {
    "nfiles": int(input("Number of files changed: ")),
    "la": int(input("Lines added: ")),
    "ld": int(input("Lines deleted: ")),
    "hunks": int(input("Number of hunks: ")),
    "ndirs": int(input("Number of directories changed: ")),
    "nexts": int(input("Number of extensions: ")),
    "test_ratio": float(input("Test ratio (e.g. 0.2): ")),
    "msg_len": int(input("Commit message length: ")),
    "msg_ref": int(input("Commit message reference count: ")),
}

input_data = pd.DataFrame([sample_commit], columns=features)

# Estimated probability that the commit is defect-inducing
risk_score = model.predict_proba(input_data)[0][1]

# Use the threshold selected during validation
threshold = 0.7
prediction = int(risk_score >= threshold)

print(f"Estimated risk score: {risk_score:.3f}")
print(f"Predicted label at threshold {threshold}: {prediction}")