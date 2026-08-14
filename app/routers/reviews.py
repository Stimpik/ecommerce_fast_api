from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db_depends import get_async_db
from app.models.reviews import Review as ReviewModel
from app.models.users import User as UserModel
from app.models.products import Product
from app.schemas import Review, ReviewCreate
from app.auth import get_current_buyer
from app.services.reviews import update_product_rating

router = APIRouter(prefix="/reviews",
                   tags=["reviews"], )


@router.get("/", response_model=list[Review])
async def review_list(db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список всех активных отзывов.

    Эндпоинт доступен без аутентификации и отдаёт только отзывы,
    у которых is_active = True.
    """
    result = await  db.scalars(select(ReviewModel).where(ReviewModel.is_active == True))
    return result.all()


@router.post("/", response_model=Review, status_code=status.HTTP_201_CREATED)
async def review_create(data: ReviewCreate,
                        db: AsyncSession = Depends(get_async_db),
                        current_user: UserModel = Depends(get_current_buyer)):
    """

    Создаёт новый отзыв для указанного товара. После добавления отзыва пересчитывает средний рейтинг товара
    (rating в таблице products) на основе всех активных оценок (grade) для этого товара.
    Доступно только роли "buyer"

    """
    product = await db.get(Product, data.product_id)

    if not product or not product.is_active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail='Product not found or is not active')
    review = ReviewModel(
        **data.model_dump(),
        user_id=current_user.id,
    )
    db.add(review)
    await db.flush()
    await update_product_rating(db, data.product_id)
    await db.commit()
    await db.refresh(review)
    return review
