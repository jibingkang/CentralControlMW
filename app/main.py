from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.api import callback, mapping, config, log
import os

app = FastAPI(
    title="CentralControlMW",
    description="中间件服务 - 设备回调转换服务",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册API路由（必须在静态文件挂载之前）
app.include_router(callback.router, prefix="/api/v1", tags=["按键回调"])
app.include_router(mapping.router, prefix="/api/v1", tags=["设备映射"])
app.include_router(config.router, prefix="/api/v1", tags=["系统配置"])
app.include_router(log.router, prefix="/api/v1", tags=["操作日志"])

# 挂载静态文件（放在最后）
app.mount("/", StaticFiles(directory=".", html=True), name="static")

@app.get("/api")
async def api_root():
    return {"message": "CentralControlMW Service", "version": "1.0.0"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}
