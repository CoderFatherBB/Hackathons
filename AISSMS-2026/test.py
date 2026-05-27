import os
import sys
import importlib
import pytest
from fastapi.testclient import TestClient

class DummyLLM:
    def invoke(self, formatted_prompt):
        return type("R", (), {"content": "Paris"})()

def init_app(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path}/test.db")
    import types
    celery_mod = types.ModuleType("celery")
    class Celery:
        def __init__(self, *args, **kwargs): ...
        def task(self, fn):
            def wrapper(*args, **kwargs):
                return fn(*args, **kwargs)
            wrapper.delay = lambda *args, **kwargs: fn(*args, **kwargs)
            return wrapper
    celery_mod.Celery = Celery
    monkeypatch.setitem(sys.modules, "celery", celery_mod)
    # Mock redis
    redis_mod = types.ModuleType("redis")
    class _Client:
        def __init__(self): self._list = []
        def rpush(self, key, value): self._list.append(value)
        def ltrim(self, key, start, end): self._list = self._list[max(len(self._list)+start,0):len(self._list)+end+1]
        def lrange(self, key, start, end): return self._list[start:end if end != -1 else len(self._list)]
    class Redis:
        @staticmethod
        def from_url(url): return _Client()
    redis_mod.Redis = Redis
    monkeypatch.setitem(sys.modules, "redis", redis_mod)
    import app.core.config as cfg
    import app.core.db as db
    importlib.reload(cfg)
    importlib.reload(db)
    import main as mainmod
    mainmod = importlib.reload(mainmod)
    import app.services.memory as memory
    import app.services.groq as groq
    monkeypatch.setattr(memory, "add_exchange", lambda *args, **kwargs: None)
    monkeypatch.setattr(groq, "classify_sales", lambda transcript: {"response_text": "ok", "lead_classification": "warm", "intent_score": 50, "needs_escalation": False})
    # Startup handled via lifespan
    import app.models.models as models  # ensure models registered
    db.Base.metadata.create_all(bind=db.engine)
    try:
        models.Call.__table__.create(bind=db.engine, checkfirst=True)
    except Exception:
        pass
    try:
        models.User.__table__.create(bind=db.engine, checkfirst=True)
    except Exception:
        pass
    try:
        models.AgentScore.__table__.create(bind=db.engine, checkfirst=True)
    except Exception:
        pass
    try:
        models.Lead.__table__.create(bind=db.engine, checkfirst=True)
    except Exception:
        pass
    client = TestClient(mainmod.app)
    return client, db.SessionLocal

def test_llm_response(monkeypatch):
    import app.utils.llm as llm_module
    monkeypatch.setattr(llm_module, "get_llm", lambda: DummyLLM())
    response = llm_module.get_llm_response("What is the capital of France?")
    assert isinstance(response, str)
    assert len(response) > 0

def test_leads_crud(monkeypatch, tmp_path):
    client, _ = init_app(monkeypatch, tmp_path)
    r = client.post("/api/leads/create", json={"name":"Alice","phone":"+10000000000","source":"web"})
    assert r.status_code == 200
    lead = r.json()
    rid = lead["id"]
    r2 = client.get(f"/api/leads/{rid}")
    assert r2.status_code == 200
    r3 = client.put("/api/leads/update-status", json={"lead_id": rid, "status": "called"})
    assert r3.status_code == 200
    assert r3.json()["status"] == "called"
    client.close()
    import app.core.db as db
    db.engine.dispose()

def test_twilio_webhooks_and_recording(monkeypatch, tmp_path):
    client, session_factory = init_app(monkeypatch, tmp_path)
    sid = "CA12345"
    r = client.post("/api/calls/twilio-webhook", data={"CallSid": sid, "From":"+1999", "To":"+1888"})
    assert r.status_code == 200
    r2 = client.post("/api/calls/recording-webhook", data={"CallSid": sid, "RecordingUrl":"http://rec"})
    assert r2.status_code == 200
    with session_factory() as s:
        from app.models.models import Call
        call = s.query(Call).filter(Call.call_sid == sid).first()
        assert call is not None
        assert call.recording_url == "http://rec"
        assert call.escalation_flag is False
    client.close()
    import app.core.db as db
    db.engine.dispose()

def test_analysis_score_and_dashboard(monkeypatch, tmp_path):
    client, session_factory = init_app(monkeypatch, tmp_path)
    # Create a call to score
    with session_factory() as s:
        from app.models.models import Call, User
        c = Call(direction="outbound")
        s.add(c)
        s.commit()
        s.refresh(c)
        u = User(name="Agent", email="agent@example.com", role="agent")
        s.add(u)
        s.commit()
        s.refresh(u)
        c.agent_id = u.id
        s.commit()
        call_id = str(c.id)
    r = client.post("/api/analysis/score-call", json={"call_id": call_id, "transcript":"hello"})
    assert r.status_code == 200
    # Dashboard metrics and leaderboard require role header
    m = client.get("/api/dashboard/metrics", headers={"X-Role":"admin"})
    assert m.status_code == 200
    l = client.get("/api/dashboard/leaderboard", headers={"X-Role":"admin"})
    assert l.status_code == 200
    client.close()
    import app.core.db as db
    db.engine.dispose()
