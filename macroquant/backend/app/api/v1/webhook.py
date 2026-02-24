from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional
import datetime
import logging
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


class AlertPayload(BaseModel):
    ticker: str
    price: float
    strategy_name: str
    comment: Optional[str] = None
    timestamp: datetime.datetime = datetime.datetime.now()


class PushNotification(BaseModel):
    title: str
    body: str
    level: str
    data: dict


async def verify_token(x_token: str = Header(...)):
    if x_token != settings.WEBHOOK_TOKEN:
        raise HTTPException(status_code=403, detail="Invalid Token")
    return x_token


@router.post("/tradingview", dependencies=[Depends(verify_token)])
async def receive_tradingview_alert(payload: AlertPayload):
    logger.info(f"收到实时报警: {payload.ticker} 触发 {payload.strategy_name}，价格: {payload.price}")
    
    impact_msg = f"检测到 {payload.ticker} 波动。{payload.comment if payload.comment else ''}"
    
    push_data = {
        "title": f"⚠️ 全球指标预警: {payload.ticker}",
        "body": impact_msg,
        "level": "warning",
        "data": {
            "ticker": payload.ticker,
            "price": payload.price,
            "event": payload.strategy_name
        }
    }
    
    await simulate_mobile_push(push_data)
    
    return {"status": "success", "message": "Alert processed and pushed"}


async def simulate_mobile_push(push_content: dict):
    print(f"\n[DOCKER CLOUD PUSH] >>> 向手机端发送推送通知:")
    print(f"TITLE: {push_content['title']}")
    print(f"BODY: {push_content['body']}")
    print(f"METADATA: {push_content['data']}\n")
