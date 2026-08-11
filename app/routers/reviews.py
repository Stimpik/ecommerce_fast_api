from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db_depends import get_async_db
from app.models.reviews import Review as ReviewModel
from app.schemas import ReviewSchema

router = APIRouter(prefix="/reviews",
                   tags=["reviews"], )


@router.get("/", response_model=list[ReviewSchema])
async def review_list(db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список всех активных отзывов.

    Эндпоинт доступен без аутентификации и отдаёт только отзывы,
    у которых is_active = True.
    """
    result = await  db.scalars(select(ReviewModel).where(ReviewModel.is_active == True))
    return result.all()
