from fastapi import FastAPI
from contextlib import asynccontextmanager
import uvicorn
from app.utils.llm import get_llm_response
from app.core.db import engine, Base
from app.routers.leads import router as leads_router
from app.routers.calls import router as calls_router
from app.routers.analysis import router as analysis_router
from app.routers.dashboard import router as dashboard_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.models import models as _models
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(lifespan=lifespan)
app.include_router(leads_router)
app.include_router(calls_router)
app.include_router(analysis_router)
app.include_router(dashboard_router)

@app.get("/health")
def read_health():
    return {"Health": "OK"}

@app.get("/app-info")
def read_app_info():
    return {"App": "AISSMS-2026"}

@app.get("/llm")
def read_llm(question: str):
    return {"Response": get_llm_response(question)}

 

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
