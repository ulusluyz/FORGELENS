"""FastAPI Local Web GUI Application Server."""

from pathlib import Path
from typing import Any, Dict, Optional
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from forgelens.app.service import ApplicationService

app = FastAPI(
    title="ForgeLens — AI Dataset & Model Auditor",
    description="Remote inspection web dashboard and API.",
    version="0.1.0",
)

service = ApplicationService()

static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=HTMLResponse)
def index():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return index_file.read_text(encoding="utf-8")
    return "<h1>ForgeLens Web Dashboard</h1>"


# --- API Models ---

class DatasetAuditRequest(BaseModel):
    repo_id: str
    profile_name: str = "General Dataset"
    sample_size: int = 1000
    strategy: str = "random"
    revision: str = "main"
    ai_model: Optional[str] = None


class ModelAuditRequest(BaseModel):
    repo_id: str
    profile_name: str = "General Model Audit"
    revision: str = "main"
    ai_model: Optional[str] = None


class ProviderConfigRequest(BaseModel):
    provider_type: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    default_model: Optional[str] = None
    is_enabled: bool = True


# --- REST Endpoints ---

@app.post("/api/audit/dataset")
async def audit_dataset(req: DatasetAuditRequest):
    try:
        res = await service.run_dataset_audit(
            repo_id=req.repo_id,
            profile_name=req.profile_name,
            sample_size=req.sample_size,
            strategy=req.strategy,
            revision=req.revision,
            ai_model=req.ai_model,
        )
        return res.model_dump()
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))


@app.post("/api/audit/model")
async def audit_model(req: ModelAuditRequest):
    try:
        res = await service.run_model_audit(
            repo_id=req.repo_id,
            profile_name=req.profile_name,
            revision=req.revision,
            ai_model=req.ai_model,
        )
        return res.model_dump()
    except Exception as err:
        raise HTTPException(status_code=500, detail=str(err))


@app.get("/api/providers")
def list_providers():
    return service.list_providers()


@app.post("/api/providers")
def save_provider(req: ProviderConfigRequest):
    service.configure_provider(
        provider_type=req.provider_type,
        api_key=req.api_key,
        base_url=req.base_url,
        default_model=req.default_model,
        is_enabled=req.is_enabled,
    )
    return {"status": "success"}


@app.get("/api/history")
def list_history():
    records = service.list_history()
    return [r.model_dump() for r in records]
