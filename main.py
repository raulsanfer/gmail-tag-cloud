from datetime import datetime
from threading import Lock
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from gmail_service import delete_by_sender, get_sender_counts, normalize_sender

app = FastAPI()
app.mount("/static", StaticFiles(directory="templates/static"), name="static")
templates = Jinja2Templates(directory="templates")

jobs_lock = Lock()
delete_jobs: dict[str, dict] = {}


class QueueDeleteRequest(BaseModel):
    senders: list[str] = Field(default_factory=list)
    months: int = Field(default=1, ge=1, le=6)


def _create_job(senders: list[str], months: int) -> str:
    job_id = str(uuid4())
    now = datetime.utcnow().isoformat()
    with jobs_lock:
        delete_jobs[job_id] = {
            "job_id": job_id,
            "status": "queued",
            "months": months,
            "total_senders": len(senders),
            "processed_senders": 0,
            "processed_messages": 0,
            "deleted_messages": 0,
            "trashed_messages": 0,
            "results": [],
            "created_at": now,
            "started_at": None,
            "finished_at": None,
        }
    return job_id


def _update_job(job_id: str, **fields):
    with jobs_lock:
        job = delete_jobs.get(job_id)
        if not job:
            return
        job.update(fields)


def _append_result(job_id: str, result: dict):
    with jobs_lock:
        job = delete_jobs.get(job_id)
        if not job:
            return

        job["results"].append(result)
        job["processed_senders"] += 1

        if result.get("status") == "success":
            job["processed_messages"] += result.get("processed", 0)
            job["deleted_messages"] += result.get("deleted", 0)
            job["trashed_messages"] += result.get("trashed", 0)


def run_delete_job(job_id: str, senders: list[str], months: int):
    _update_job(job_id, status="running", started_at=datetime.utcnow().isoformat())

    for sender in senders:
        try:
            deletion = delete_by_sender(sender, months=months)
            _append_result(
                job_id,
                {
                    "sender": sender,
                    "status": "success",
                    "processed": deletion["processed"],
                    "deleted": deletion["deleted"],
                    "trashed": deletion["trashed"],
                },
            )
        except Exception as exc:
            _append_result(
                job_id,
                {
                    "sender": sender,
                    "status": "error",
                    "error": str(exc),
                },
            )

    _update_job(job_id, status="done", finished_at=datetime.utcnow().isoformat())


@app.get("/", response_class=HTMLResponse)
def index(request: Request, months: int = Query(1, ge=1, le=6)):
    data = get_sender_counts(months=months)
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "data": data,
            "months": months,
            "period_options": [1, 2, 3, 4, 5, 6],
        },
    )


@app.post("/queue-delete")
def queue_delete(payload: QueueDeleteRequest, background_tasks: BackgroundTasks):
    unique_senders = []
    seen = set()
    for raw_sender in payload.senders:
        sender = normalize_sender(raw_sender)
        if sender and sender not in seen:
            unique_senders.append(sender)
            seen.add(sender)

    if not unique_senders:
        return JSONResponse(
            status_code=400,
            content={"error": "No se han seleccionado remitentes válidos."},
        )

    job_id = _create_job(unique_senders, payload.months)
    background_tasks.add_task(run_delete_job, job_id, unique_senders, payload.months)

    return {
        "job_id": job_id,
        "status": "queued",
        "total_senders": len(unique_senders),
    }


@app.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    with jobs_lock:
        job = delete_jobs.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job no encontrado")
        return job


@app.post("/delete/{sender}")
def delete_sender(sender: str, months: int = Query(1, ge=1, le=6)):
    normalized = normalize_sender(sender)
    if not normalized:
        return RedirectResponse(f"/?months={months}", status_code=303)

    job_id = _create_job([normalized], months)
    run_delete_job(job_id, [normalized], months)
    return RedirectResponse(f"/?months={months}", status_code=303)


@app.get("/delete/{sender}")
def delete_sender_get(sender: str, months: int = Query(1, ge=1, le=6)):
    return delete_sender(sender, months=months)
