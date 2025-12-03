from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select, update

from app.models.products import Product as ProductModel
from app.models.categories import Category as CategoryModel
from app.schemas import Product as ProductSchema, ProductCreate
from app.db_depends import get_db

# Создаём маршрутизатор для товаров
router = APIRouter(
    prefix="/products",
    tags=["products"],
)


@router.get("/", response_model=list[ProductSchema], status_code=status.HTTP_200_OK)
async def get_all_products(db: Session = Depends(get_db)):
    """
    Возвращает список всех товаров.
    """
    products = db.scalars(
        select(ProductModel).join(CategoryModel).where(ProductModel.is_active == True,
                                                       CategoryModel.is_active == True,
                                                       ProductModel.stock > 0)).all()
    return products


@router.post("/", response_model=ProductSchema, status_code=status.HTTP_201_CREATED)
async def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """
    Создаёт новый товар.
    """
    category = db.scalars(
        select(CategoryModel).where(CategoryModel.id == product.category_id,
                                    CategoryModel.is_active == True)).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Category not found or inactive')
    db_product = ProductModel(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.get("/category/{category_id}", response_model=list[ProductSchema], status_code=status.HTTP_200_OK)
async def get_products_by_category(category_id: int, db: Session = Depends(get_db)):
    """
    Возвращает список товаров в указанной категории по её ID.

    """
    category = db.scalar(select(CategoryModel).where(CategoryModel.id == category_id, CategoryModel.is_active == True))
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Category not found or inactive')
    stmt = select(ProductModel).where(ProductModel.category_id == category_id, ProductModel.is_active == True)
    return db.scalars(stmt).all()


@router.get("/{product_id}", response_model=ProductSchema, status_code=status.HTTP_200_OK)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """
    Возвращает детальную информацию о товаре по его ID.
    """

    product = db.scalar(select(ProductModel).where(ProductModel.is_active == True,
                                                   ProductModel.id == product_id))
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Product not found or inactive')
    category = db.scalar(
        select(CategoryModel).where(CategoryModel.id == product.category_id, CategoryModel.is_active == True))
    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Category not found or inactive')
    return product


@router.put("/{product_id}", response_model=ProductSchema)
async def update_product(product_id: int, product: ProductCreate, db: Session = Depends(get_db)):
    """
    Обновляет товар по его ID.
    """
    product_c = db.scalar(select(ProductModel).where(ProductModel.is_active == True,
                                                     ProductModel.id == product_id))
    if not product_c:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Product not found')
    category = db.scalar(select(CategoryModel).where(CategoryModel.id == product.category_id))
    if not category:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Category not found or inactive')

    db.execute(update(ProductModel).where(ProductModel.id == product_id).values(**product.model_dump()))
    db.commit()
    db.refresh(product_c)
    return product_c


@router.delete("/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    """
    Удаляет товар по его ID.

    """

    product = db.scalar(select(ProductModel).where(ProductModel.id == product_id, ProductModel.is_active == True))
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Product not found or inactive')
    product.is_active = False
    db.commit()

    return {"status": "success", "message": "Product marked as inactive"}
