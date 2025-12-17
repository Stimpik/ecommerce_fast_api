from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.products import Product as ProductModel
from app.models.categories import Category as CategoryModel
from app.schemas import Product as ProductSchema, ProductCreate
from app.db_depends import get_db
from app.db_depends import get_async_db

# Создаём маршрутизатор для товаров
router = APIRouter(
    prefix="/products",
    tags=["products"],
)


@router.get("/", response_model=list[ProductSchema])
async def get_all_products(db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список всех активных товаров.
    """
    products = await db.scalars(select(ProductModel).where(ProductModel.is_active == True))
    return products.all()


@router.post("/", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: AsyncSession = Depends(get_async_db)):
    """
    Создаёт новый товар.
    """
    category_result = await db.scalars(
        select(CategoryModel).where(CategoryModel.id == product.category_id,
                                    CategoryModel.is_active == True))
    category = category_result.one_or_none()
    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Category not found or inactive')
    db_product = ProductModel(**product.model_dump())
    db.add(db_product)
    await db.commit()
    await db.refresh(db_product)
    return db_product


@router.get("/category/{category_id}", response_model=list[ProductSchema], status_code=status.HTTP_200_OK)
async def get_products_by_category(category_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает список товаров в указанной категории по её ID.

    """
    category_result = await db.scalars(
        select(CategoryModel).where(CategoryModel.id == category_id, CategoryModel.is_active == True))
    category = category_result.one_or_none()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Category not found or inactive')
    stmt = await db.scalars(
        select(ProductModel).where(ProductModel.category_id == category_id, ProductModel.is_active == True))
    return stmt.all()


@router.get("/{product_id}", response_model=ProductSchema, status_code=status.HTTP_200_OK)
async def get_product(product_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Возвращает детальную информацию о товаре по его ID.
    """

    product_result = await db.scalars(select(ProductModel).where(ProductModel.is_active == True,
                                                                 ProductModel.id == product_id))
    product = product_result.one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Product not found or inactive')
    category_result = await db.scalars(
        select(CategoryModel).where(CategoryModel.id == product.category_id, CategoryModel.is_active == True))
    category = category_result.one_or_none()
    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Category not found or inactive')
    return product


@router.put("/{product_id}", response_model=ProductSchema)
async def update_product(product_id: int, product: ProductCreate, db: AsyncSession = Depends(get_async_db)):
    """
    Обновляет товар по его ID.
    """
    product_result = await db.scalars(select(ProductModel).where(ProductModel.is_active == True,
                                                                 ProductModel.id == product_id))
    product_c = product_result.one_or_none()
    if not product_c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Product not found')
    category_coro = await db.scalars(select(CategoryModel).where(CategoryModel.id == product.category_id))
    category = category_coro.one_or_none()
    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Category not found or inactive')

    await db.execute(update(ProductModel).where(ProductModel.id == product_id).values(**product.model_dump()))
    await db.commit()
    await db.refresh(product_c)
    return product_c


@router.delete("/{product_id}")
async def delete_product(product_id: int, db: AsyncSession = Depends(get_async_db)):
    """
    Удаляет товар по его ID.

    """

    product_result = await db.scalars(
        select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True))
    product = product_result.one_or_none()
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Product not found or inactive')
    product.is_active = False
    await db.commit()

    return {"status": "success", "message": "Product marked as inactive"}
