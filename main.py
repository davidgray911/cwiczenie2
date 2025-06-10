from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Float, Sequence, select
from pydantic import BaseModel
from typing import Optional, List

# Konfiguracja bazy danych
DATABASE_URL = "postgresql+asyncpg://user:password@db/coffee_shop"
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# Modele SQLAlchemy
class Coffee(Base):
    __tablename__ = "coffees"
    id = Column(Integer, Sequence("coffee_id_seq"), primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False)
    description = Column(String)
    price = Column(Float, nullable=False)

# Schematy Pydantic
class CoffeeCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float

class CoffeeRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    price: float

    class Config:
        orm_mode = True

# Tworzenie aplikacji FastAPI
app = FastAPI()

# Tworzenie tabel w bazie danych
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.on_event("startup")
async def startup():
    await init_db()

# Dependency do sesji bazy danych
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Endpoint: GET /coffees/
@app.get("/coffees/", response_model=List[CoffeeRead])
async def get_coffees(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Coffee))
    coffees = result.scalars().all()
    return coffees

# Endpoint: POST /coffees/
@app.post("/coffees/", response_model=CoffeeRead, status_code=201)
async def add_coffee(coffee_data: CoffeeCreate, db: AsyncSession = Depends(get_db)):
    new_coffee = Coffee(**coffee_data.dict())
    db.add(new_coffee)
    await db.commit()
    await db.refresh(new_coffee)
    return new_coffee

# Endpoint: GET /coffees/{coffee_id}
@app.get("/coffees/{coffee_id}", response_model=CoffeeRead)
async def get_coffee_by_id(coffee_id: int, db: AsyncSession = Depends(get_db)):
    coffee = await db.get(Coffee, coffee_id)
    if not coffee:
        raise HTTPException(status_code=404, detail="Coffee not found")
    return coffee

# Endpoint: PUT /coffees/{coffee_id}
@app.put("/coffees/{coffee_id}", response_model=CoffeeRead)
async def update_coffee(coffee_id: int, updated_data: CoffeeCreate, db: AsyncSession = Depends(get_db)):
    coffee = await db.get(Coffee, coffee_id)
    if not coffee:
        raise HTTPException(status_code=404, detail="Coffee not found")

    coffee.name = updated_data.name
    coffee.description = updated_data.description
    coffee.price = updated_data.price

    await db.commit()
    await db.refresh(coffee)
    return coffee

# Endpoint: DELETE /coffees/{coffee_id}
@app.delete("/coffees/{coffee_id}", status_code=204)
async def delete_coffee(coffee_id: int, db: AsyncSession = Depends(get_db)):
    coffee = await db.get(Coffee, coffee_id)
    if not coffee:
        raise HTTPException(status_code=404, detail="Coffee not found")

    await db.delete(coffee)
    await db.commit()
    return
