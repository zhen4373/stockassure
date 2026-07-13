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
    print(f"🚀 {settings.PROJECT_NAME} v{settings.VERSION} 正在啟動...")
    init_db()
    load_plugins()

# 1. 確保這個 API 的路徑「精準符合」前端 Fetch 的網址：/api/v1/templates
@app.get("/api/v1/templates")
def get_available_templates():
    return {
        "count": len(GLOBAL_TEMPLATES),
        "templates": GLOBAL_TEMPLATES
    }

# 2. 掛載其他 API 路由
app.include_router(location_router)
app.include_router(object_router)

# 3. 靜態檔案託管一定要放在「最後面」！
static_path = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_path):
    app.mount("/", StaticFiles(directory=static_path, html=True), name="static")