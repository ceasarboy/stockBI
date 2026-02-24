from fastapi import APIRouter

router = APIRouter()


@router.get("/rules")
async def get_alert_rules():
    return {"rules": []}


@router.post("/rules")
async def create_alert_rule():
    return {"status": "success"}


@router.get("/logs")
async def get_alert_logs():
    return {"logs": []}
