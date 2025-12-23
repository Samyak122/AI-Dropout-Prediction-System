from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib
import numpy as np
import pandas as pd
import os
from datetime import datetime

# -------------------------------------------------
# App setup
# -------------------------------------------------
app = FastAPI(title="AI Dropout Prediction API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(BASE_DIR, "ml", "dropout_model.pkl")
DATA_DIR = os.path.join(BASE_DIR, "data")
INTERVENTION_FILE = os.path.join(DATA_DIR, "interventions.csv")

os.makedirs(DATA_DIR, exist_ok=True)

# -------------------------------------------------
# Load model
# -------------------------------------------------
try:
    model = joblib.load(MODEL_PATH)
except Exception as e:
    raise RuntimeError(f"Model loading failed: {e}")

# -------------------------------------------------
# Schemas
# -------------------------------------------------
class StudentInput(BaseModel):
    attendance: float
    internal_marks: float
    quiz_score: float
    login_frequency: float
    financial_issue: int
    backlog_count: int


class InterventionLog(BaseModel):
    attendance: float
    internal_marks: float
    quiz_score: float
    login_frequency: float
    financial_issue: int
    backlog_count: int
    risk_level: str
    intervention_taken: str


class OutcomeUpdate(BaseModel):
    timestamp: str
    outcome: str  # Improved / No Change / Dropped Out


# -------------------------------------------------
# Root
# -------------------------------------------------
@app.get("/")
def root():
    return {"message": "AI Dropout Prediction API is running"}


# -------------------------------------------------
# Prediction endpoint
# -------------------------------------------------
@app.post("/predict")
def predict_dropout(data: StudentInput):
    try:
        features = np.array([[
            data.attendance,
            data.internal_marks,
            data.quiz_score,
            data.login_frequency,
            data.financial_issue,
            data.backlog_count
        ]])

        probability = model.predict_proba(features)[0][1]
        percentage = round(probability * 100, 2)

        if percentage < 30:
            risk_level = "Low"
        elif percentage < 60:
            risk_level = "Medium"
        else:
            risk_level = "High"

        # Simple explainability (feature influence proxy)
        feature_names = [
            "Attendance",
            "Internal Marks",
            "Quiz Score",
            "Login Frequency",
            "Financial Issue",
            "Backlog Count"
        ]
        importance = abs(features[0] - np.mean(features))
        top_features = [
            feature_names[i]
            for i in np.argsort(importance)[-3:]
        ]

        return {
            "dropout_risk_percentage": percentage,
            "risk_level": risk_level,
            "top_risk_factors": top_features
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------------------------
# Log intervention
# -------------------------------------------------
@app.post("/log-intervention")
def log_intervention(data: InterventionLog):
    timestamp = datetime.utcnow().isoformat()

    record = {
        "timestamp": timestamp,
        "attendance": data.attendance,
        "internal_marks": data.internal_marks,
        "quiz_score": data.quiz_score,
        "login_frequency": data.login_frequency,
        "financial_issue": data.financial_issue,
        "backlog_count": data.backlog_count,
        "risk_level": data.risk_level,
        "intervention_taken": data.intervention_taken,
        "outcome": ""
    }

    df = pd.DataFrame([record])

    if os.path.exists(INTERVENTION_FILE):
        df.to_csv(INTERVENTION_FILE, mode="a", header=False, index=False)
    else:
        df.to_csv(INTERVENTION_FILE, index=False)

    return {"message": "Intervention logged successfully"}


# -------------------------------------------------
# Update outcome (prospective validation)
# -------------------------------------------------
@app.post("/update-outcome")
def update_outcome(data: OutcomeUpdate):
    if not os.path.exists(INTERVENTION_FILE):
        raise HTTPException(status_code=404, detail="No intervention data found")

    df = pd.read_csv(INTERVENTION_FILE)

    if data.timestamp not in df["timestamp"].values:
        raise HTTPException(status_code=404, detail="Record not found")

    df.loc[df["timestamp"] == data.timestamp, "outcome"] = data.outcome
    df.to_csv(INTERVENTION_FILE, index=False)

    return {"message": "Outcome updated successfully"}


# -------------------------------------------------
# Validation metrics (prospective validation)
# -------------------------------------------------
@app.get("/validation-metrics")
def validation_metrics():
    if not os.path.exists(INTERVENTION_FILE):
        return {"message": "No validation data available"}

    df = pd.read_csv(INTERVENTION_FILE)
    completed = df[df["outcome"] != ""]

    if completed.empty:
        return {"message": "No completed outcomes yet"}

    high_risk = completed[completed["risk_level"] == "High"]
    non_high_risk = completed[completed["risk_level"] != "High"]

    high_risk_dropout = (
        high_risk["outcome"].str.lower() == "dropped out"
    ).mean()

    non_high_risk_dropout = (
        non_high_risk["outcome"].str.lower() == "dropped out"
    ).mean()

    return {
        "high_risk_dropout_rate": round(high_risk_dropout * 100, 2),
        "non_high_risk_dropout_rate": round(non_high_risk_dropout * 100, 2),
        "total_validated_cases": len(completed)
    }


# -------------------------------------------------
# DASHBOARD ENDPOINT (ADMIN ANALYTICS)
# -------------------------------------------------
@app.get("/dashboard")
def dashboard_data():
    if not os.path.exists(INTERVENTION_FILE):
        return {"message": "No data available"}

    df = pd.read_csv(INTERVENTION_FILE)

    return {
        "total_logs": len(df),
        "risk_distribution": df["risk_level"].value_counts().to_dict(),
        "intervention_distribution": df["intervention_taken"].value_counts().to_dict(),
        "outcome_distribution": df[df["outcome"] != ""]["outcome"].value_counts().to_dict()
    }
