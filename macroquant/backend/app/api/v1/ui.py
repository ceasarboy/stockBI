from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
import os
from app.core.database import get_db
from app.services.stock_data_service import StockDataService
from app.api.v1.auth import get_current_user
from app.models.user import User

router = APIRouter()
stock_data_service = StockDataService()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/data", response_class=HTMLResponse)
async def data_page(request: Request):
    return templates.TemplateResponse("data.html", {"request": request})


@router.get("/news", response_class=HTMLResponse)
async def news_page(request: Request):
    return templates.TemplateResponse("news.html", {"request": request})


@router.get("/factors", response_class=HTMLResponse)
async def factors_page(request: Request):
    return templates.TemplateResponse("factors.html", {"request": request})


@router.get("/alerts", response_class=HTMLResponse)
async def alerts_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/stocks", response_class=HTMLResponse)
async def stocks_page(request: Request, db: AsyncSession = Depends(get_db)):
    stocks = await stock_data_service.get_stocks(db, skip=0, limit=10000, auto_sync=True)
    return templates.TemplateResponse("stocks.html", {"request": request, "stocks": stocks})


@router.get("/stock/{symbol}", response_class=HTMLResponse)
async def stock_detail_page(request: Request, symbol: str, db: AsyncSession = Depends(get_db)):
    stock = await stock_data_service.get_stock(db, symbol, auto_sync=True)
    if not stock:
        return templates.TemplateResponse("error.html", {"request": request, "message": "Stock not found"})
    daily_data = await stock_data_service.get_stock_daily(db, symbol, days=30, auto_sync=True)
    return templates.TemplateResponse("stock_detail.html", {"request": request, "stock": stock, "daily_data": daily_data})


@router.get("/indicators", response_class=HTMLResponse)
async def indicators_page(request: Request):
    return templates.TemplateResponse("indicators.html", {"request": request})
