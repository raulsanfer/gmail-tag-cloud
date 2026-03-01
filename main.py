# main.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from gmail_service import get_sender_counts, delete_by_sender

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    data = get_sender_counts()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "data": data}
    )

@app.post("/delete/{sender}")
def delete_sender(sender: str):
    delete_by_sender(sender)
    return RedirectResponse("/", status_code=303)
