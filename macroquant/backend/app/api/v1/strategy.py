from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_strategies():
    return {"strategies": []}


@router.post("/")
async def create_strategy():
    return {"status": "success"}


@router.get("/{strategy_id}/backtests")
async def get_strategy_backtests(strategy_id: int):
    return {"strategy_id": strategy_id, "backtests": []}
