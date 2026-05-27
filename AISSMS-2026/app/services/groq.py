from app.core.config import settings

def classify_sales(transcript: str):
    return {"response_text": "", "lead_classification": "warm", "intent_score": 50, "needs_escalation": False}

def score_agent(transcript: str):
    return {
        "greeting_score": 8,
        "empathy_score": 6,
        "objection_score": 5,
        "closing_score": 7,
        "script_score": 9,
        "feedback": ""
    }
