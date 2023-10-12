#!/usr/bin/env python3

from pathlib import Path
import markdown

from fastapi import Request, status
from fastapi_offline import FastAPIOffline
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import uvicorn


SCRIPT_DIR = Path(__file__).resolve().parent

app = FastAPIOffline(
    title="Backend",
    description="API to talk to MongoDB",
    root_path="",
    version = "development"
)

config = {
    "fastapi_host": "0.0.0.0",
    "fastapi_port": 8080,
    "proxy_path": "",  # Empty string if not behind a reverse proxy

}

template_dir = SCRIPT_DIR / "templates"
templates = Jinja2Templates(directory=template_dir)


@app.get("", include_in_schema=False, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
@app.get("/", include_in_schema=False, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
async def redirect_typer():
    return RedirectResponse(f"{config['proxy_path']}/readme")


@app.get("/readme", response_class=HTMLResponse,
         status_code=status.HTTP_200_OK,
         summary="Return markdown of readme",
         include_in_schema=False)
async def index(request: Request):
    with open(SCRIPT_DIR / "README.md", "r", encoding="utf-8") as input_file:
        text = input_file.read()

    html = markdown.markdown(text, extensions=['tables'])
    data = {
        "text": html
    }
    return templates.TemplateResponse("/page.html", {"request": request, "data": data})


@app.get("/status", include_in_schema=False)
async def get_status():
    """
    Assert webserver is running

    Return status code
    """
    return 200


def main():
    uvicorn.run(app, host=config["fastapi_host"], port=config["fastapi_port"])


if __name__ == "__main__":
    main()
