from fastapi import APIRouter, HTTPException, Depends
from app.models.log import Log
from app.services.log_service import LogService

router = APIRouter()
log_service = LogService()

@router.post("/log")
async def create_log(log: Log):
    log_service.save_log(log)
    return {"message": "Log created successfully"}


@router.get("/logs")
async def get_logs():
    logs = log_service.get_logs()
    return logs