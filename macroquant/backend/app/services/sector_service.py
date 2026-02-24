"""板块数据服务"""
import logging
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, asc
from sqlalchemy.orm import joinedload

from app.models.sector import Sector, SectorDaily

logger = logging.getLogger(__name__)


class SectorService:
    """板块数据服务"""

    async def get_sectors(
        self,
        db: AsyncSession,
        sector_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Sector]:
        """获取板块列表"""
        query = select(Sector)
        if sector_type:
            query = query.where(Sector.sector_type == sector_type)
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    async def get_sector_daily_data(
        self,
        db: AsyncSession,
        trade_date: Optional[datetime.date] = None,
        sector_type: Optional[str] = None,
        sort_by: str = "net_inflow",
        sort_order: str = "desc",
        limit: int = 20
    ) -> List[Dict]:
        """获取板块日数据
        
        Args:
            sort_by: 排序字段 - net_inflow(净流入), change_pct(涨跌幅), main_inflow(主力流入)
            sort_order: 排序方向 - asc(升序), desc(降序)
        """
        if not trade_date:
            # 获取最新交易日期
            result = await db.execute(
                select(SectorDaily.trade_date)
                .order_by(desc(SectorDaily.trade_date))
                .limit(1)
            )
            trade_date = result.scalar()

        if not trade_date:
            return []

        # 构建查询
        query = (
            select(Sector, SectorDaily)
            .join(SectorDaily, Sector.id == SectorDaily.sector_id)
            .where(SectorDaily.trade_date == trade_date)
        )

        if sector_type:
            query = query.where(Sector.sector_type == sector_type)

        # 排序
        sort_column = getattr(SectorDaily, sort_by, SectorDaily.net_inflow)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        query = query.limit(limit)
        result = await db.execute(query)
        rows = result.all()

        # 组装数据
        data = []
        for sector, daily in rows:
            data.append({
                "sector_id": sector.id,
                "sector_code": sector.code,
                "sector_name": sector.name,
                "sector_type": sector.sector_type,
                "trade_date": daily.trade_date.isoformat() if daily.trade_date else None,
                "change_pct": float(daily.change_pct) if daily.change_pct else 0,
                "change_amount": float(daily.change_amount) if daily.change_amount else 0,
                "net_inflow": float(daily.net_inflow) if daily.net_inflow else 0,
                "main_inflow": float(daily.main_inflow) if daily.main_inflow else 0,
                "retail_inflow": float(daily.retail_inflow) if daily.retail_inflow else 0,
                "total_amount": float(daily.total_amount) if daily.total_amount else 0,
                "total_volume": float(daily.total_volume) if daily.total_volume else 0,
                "leading_stock": daily.leading_stock,
                "leading_stock_name": daily.leading_stock_name,
                "leading_change_pct": float(daily.leading_change_pct) if daily.leading_change_pct else 0,
                "up_count": daily.up_count or 0,
                "down_count": daily.down_count or 0,
                "flat_count": daily.flat_count or 0,
            })

        return data

    async def sync_sectors_from_akshare(self, db: AsyncSession) -> int:
        """从AKShare同步板块列表"""
        try:
            import akshare as ak

            count = 0

            # 同步行业板块
            try:
                df = ak.stock_board_industry_name_em()
                for _, row in df.iterrows():
                    code = row.get('板块代码', '')
                    name = row.get('板块名称', '')
                    if code and name:
                        await self._get_or_create_sector(db, code, name, 'industry')
                        count += 1
            except Exception as e:
                logger.error(f"Error syncing industry sectors: {e}")

            # 同步概念板块
            try:
                df = ak.stock_board_concept_name_em()
                for _, row in df.iterrows():
                    code = row.get('板块代码', '')
                    name = row.get('板块名称', '')
                    if code and name:
                        await self._get_or_create_sector(db, code, name, 'concept')
                        count += 1
            except Exception as e:
                logger.error(f"Error syncing concept sectors: {e}")

            await db.commit()
            logger.info(f"Synced {count} sectors")
            return count

        except Exception as e:
            logger.error(f"Error syncing sectors: {e}")
            await db.rollback()
            return 0

    async def _get_or_create_sector(
        self,
        db: AsyncSession,
        code: str,
        name: str,
        sector_type: str
    ) -> Sector:
        """获取或创建板块"""
        result = await db.execute(
            select(Sector).where(Sector.code == code)
        )
        sector = result.scalar_one_or_none()

        if not sector:
            sector = Sector(
                code=code,
                name=name,
                sector_type=sector_type
            )
            db.add(sector)

        return sector

    async def sync_sector_daily_data(self, db: AsyncSession, trade_date: Optional[datetime.date] = None) -> int:
        """同步板块日数据"""
        try:
            import akshare as ak

            if not trade_date:
                trade_date = datetime.now().date()

            count = 0

            # 获取所有板块
            result = await db.execute(select(Sector))
            sectors = result.scalars().all()

            for sector in sectors:
                try:
                    if sector.sector_type == 'industry':
                        # 获取行业板块数据
                        df = ak.stock_board_industry_hist_em(
                            symbol=sector.name,
                            period="日k",
                            adjust="",
                            start_date=trade_date.strftime('%Y%m%d'),
                            end_date=trade_date.strftime('%Y%m%d')
                        )
                    elif sector.sector_type == 'concept':
                        # 获取概念板块数据
                        df = ak.stock_board_concept_hist_em(
                            symbol=sector.name,
                            period="日k",
                            adjust="",
                            start_date=trade_date.strftime('%Y%m%d'),
                            end_date=trade_date.strftime('%Y%m%d')
                        )
                    else:
                        continue

                    if df.empty:
                        continue

                    row = df.iloc[0]

                    # 创建或更新日数据
                    result = await db.execute(
                        select(SectorDaily).where(
                            SectorDaily.sector_id == sector.id,
                            SectorDaily.trade_date == trade_date
                        )
                    )
                    daily = result.scalar_one_or_none()

                    if not daily:
                        daily = SectorDaily(
                            sector_id=sector.id,
                            trade_date=trade_date
                        )
                        db.add(daily)

                    # 更新数据
                    daily.change_pct = float(row.get('涨跌幅', 0))
                    daily.total_amount = float(row.get('成交额', 0))
                    daily.total_volume = float(row.get('成交量', 0))

                    count += 1

                except Exception as e:
                    logger.error(f"Error syncing sector {sector.name}: {e}")
                    continue

            await db.commit()
            logger.info(f"Synced {count} sector daily records")
            return count

        except Exception as e:
            logger.error(f"Error syncing sector daily data: {e}")
            await db.rollback()
            return 0


# 创建服务实例
sector_service = SectorService()
