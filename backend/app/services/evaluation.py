from sklearn.metrics import accuracy_score,f1_score
from app.services.fairness import *

def evaluate_system_performance(df):
    if df.empty:
        return {
            "performance": {"accuracy": 0.0, "f1": 0.0},
            "fairness": {"dp": 0.0, "di": 0.0, "eo": 0.0}
        }

    df["y_true"]=df.status.eq("accepted").astype(int)
    df["y_pred"]=df.score.ge(85).astype(int)

    perf={
        "accuracy":accuracy_score(df.y_true,df.y_pred),
        "f1":f1_score(df.y_true,df.y_pred)
    }

    fairness={
        "dp":demographic_parity(df,"gender","y_pred"),
        "di":disparate_impact(df,"gender","y_pred","M","F"),
        "eo":equal_opportunity(df,"gender","y_true","y_pred")
    }

    result = {"performance":perf,"fairness":fairness}
    # Add gender_fairness for frontend compatibility
    result["gender_fairness"] = fairness["di"] # Using Disparate Impact as the primary fairness score
    return result