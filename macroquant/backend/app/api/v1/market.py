from fastapi import APIRouter
from typing import List
import datetime
from pydantic import BaseModel

router = APIRouter()


class MarketSnapshotItem(BaseModel):
    symbol: str
    name: str
    price: float
    change: str


@router.get("/global-snapshot")
async def get_global_snapshot():
    snapshot = [
        {"symbol": "GC=F", "name": "COMEX黄金", "price": 2050.2, "change": "+0.5%"},
        {"symbol": "CL=F", "name": "WTI原油", "price": 78.3, "change": "-1.2%"},
        {"symbol": "^TNX", "name": "美债10Y收益率", "price": 4.25, "change": "+0.02"},
        {"symbol": "EURUSD=X", "name": "欧元/美元", "price": 1.085, "change": "-0.1%"},
        {"symbol": "^HSI", "name": "恒生指数", "price": 18250.5, "change": "+0.8%"}
    ]
    return {"timestamp": datetime.datetime.now(), "data": snapshot}
