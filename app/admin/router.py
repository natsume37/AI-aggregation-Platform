from fastapi import APIRouter
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter()

# 假设 templates 目录在 app/templates
BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = BASE_DIR / "templates" / "admin.html"

@router.get("/", response_class=FileResponse)
async def admin_page():
    return FileResponse(TEMPLATE_PATH)
