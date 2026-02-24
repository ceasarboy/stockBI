"""板块数据API"""
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.sector_service import sector_service

router = APIRouter(tags=["sectors"])


@router.get("")
async def get_sectors(
    sector_type: Optional[str] = Query(None, description="板块类型: industry-行业, concept-概念"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db)
):
    """获取板块列表"""
    sectors = await sector_service.get_sectors(db, sector_type=sector_type, skip=skip, limit=limit)
    return {
        "items": [
            {
                "id": sector.id,
                "code": sector.code,
                "name": sector.name,
                "sector_type": sector.sector_type,
                "created_at": sector.created_at.isoformat() if sector.created_at else None
            }
            for sector in sectors
        ],
        "total": len(sectors)
    }


@router.get("/daily")
async def get_sector_daily(
    sector_type: Optional[str] = Query(None, description="板块类型: industry-行业, concept-概念"),
    sort_by: str = Query("net_inflow", description="排序字段: net_inflow-净流入, change_pct-涨跌幅, main_inflow-主力流入"),
    sort_order: str = Query("desc", description="排序方向: asc-升序, desc-降序"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """获取板块日数据（支持排序）"""
    # 验证排序字段
    valid_sort_fields = ["net_inflow", "change_pct", "main_inflow", "total_amount"]
    if sort_by not in valid_sort_fields:
        raise HTTPException(status_code=400, detail=f"Invalid sort_by. Must be one of: {', '.join(valid_sort_fields)}")

    # 验证排序方向
    if sort_order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid sort_order. Must be 'asc' or 'desc'")

    data = await sector_service.get_sector_daily_data(
        db,
        sector_type=sector_type,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=limit
    )

    return {
        "items": data,
        "total": len(data),
        "sort_by": sort_by,
        "sort_order": sort_order
    }


@router.post("/sync")
async def sync_sectors(db: AsyncSession = Depends(get_db)):
    """同步板块列表"""
    count = await sector_service.sync_sectors_from_akshare(db)
    return {
        "status": "success",
        "message": f"Synced {count} sectors",
        "count": count,
        "timestamp": datetime.now()
    }


@router.post("/sync-daily")
async def sync_sector_daily(db: AsyncSession = Depends(get_db)):
    """同步板块日数据"""
    count = await sector_service.sync_sector_daily_data(db)
    return {
        "status": "success",
        "message": f"Synced {count} sector daily records",
        "count": count,
        "timestamp": datetime.now()
    }
