from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from core.config import settings
from core.init_db import init_db
from core.plugin_loader import load_plugins, GLOBAL_TEMPLATES
from core.location_router import router as location_router
from core.object_router import router as object_router
import os

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

@app.on_event("startup")
def startup_event():
    print(f"🚀 {settings.PROJECT_NAME} v{settings.VERSION} starting up...")
    init_db()
    load_plugins()
    print(f"system language: {settings.Language}")

@app.get("/api/system/config")
async def get_system_config():
    return {
        "project_name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "language": settings.Language  # 會回傳 "Chinese Traditional" 等
    }

# 🌟 已移除 v1：路徑精準變更為 /api/templates
@app.get("/api/templates")
def get_available_templates():
    return {
        "count": len(GLOBAL_TEMPLATES),
        "templates": GLOBAL_TEMPLATES
    }

# 掛載其他 API 路由
app.include_router(location_router)
app.include_router(object_router)

# 🌟 靜態檔案託管安全檢查與掛載
dashboard_ui_path = os.path.join(os.path.dirname(__file__), "dashboard_ui")

if os.path.exists(dashboard_ui_path):
    app.mount("/", StaticFiles(directory=dashboard_ui_path, html=True), name="dashboard_ui")
else:
    print(f"⚠️ 警告：找不到前端 UI 目錄，路徑應為: {dashboard_ui_path}")