from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import databases
from typing import List
from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import Table, MetaData, Column, Integer, String, DateTime, VARCHAR, Float, ForeignKey, create_engine
from random import randint
import os
import time

DB_USER = "postgres"
DB_NAME = "trading_network"
DB_PASSWORD = "postgrespw"
DB_HOST = "127.0.0.1"

# создание Docker контейнера с postgres 
os.system(f"docker run --name My_Postgres -p 5432:5432 -e POSTGRES_USER={DB_USER} -e POSTGRES_PASSWORD={DB_PASSWORD} -e POSTGRES_DB={DB_NAME} -d postgres:latest")
time.sleep(5)

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:5432/{DB_NAME}"

database = databases.Database(DATABASE_URL)
metadata = MetaData()

stores = Table(
    "stores",
    metadata,
    Column("id", Integer, primary_key=True, unique=True, autoincrement=True, comment="Идентификатор магазина"),
    Column("address", VARCHAR, unique=True, comment='Адрес магазина')
)

items = Table(
    "items",
    metadata,
    Column("id", Integer, primary_key=True, unique=True, autoincrement=True, comment="Идентификатор товара"),
    Column("name", String(50), unique=True, comment='Наименование товара'),
    Column("price", Float, comment='Цена товара')
)

sales = Table(
    "sales",
    metadata,
    Column("id", Integer, primary_key=True, unique=True, autoincrement=True, comment="Идентификатор продажи"),
    Column("sale_time", DateTime, comment='Время продажи продажи'),
    Column("item_id", Integer, ForeignKey('items.id'), comment="Идентификатор товара"),
    Column("store_id", Integer, ForeignKey('stores.id'), comment="Идентификатор магазина")
)

# engine - пул соединений к БД
engine = create_engine(DATABASE_URL)

# создание таблиц
metadata.create_all(engine)

class SalesIn(BaseModel):
    sale_time = datetime.now()
    item_id: int
    store_id: int

class Stores(BaseModel):
    id: int
    address: str

class Items(BaseModel):
    id: int
    name: str
    price: float

class StoresTop(BaseModel):
    id: int
    address: str
    sum_of_sales: float

class ItemsTop(BaseModel):
    id: int
    name: str
    count_of_sales: int               

app = FastAPI()

@app.on_event("startup")
async def startup():
    await database.connect()

    # создание магазинов
    query = stores.select()
    if (await database.fetch_all(query)) == []:
        queries = []
        queries.append(stores.insert().values(address="Косой переулок 33"))
        queries.append(stores.insert().values(address="Паучий тупик 7"))
        queries.append(stores.insert().values(address="Лютный переулок 666"))
        queries.append(stores.insert().values(address="Тотнем-Корт-Роуд 18"))
        queries.append(stores.insert().values(address="Улица Магнолий 69"))
        for query in queries:
            await database.fetch_all(query)

    # создание товаров
    query = items.select()
    if (await database.fetch_all(query)) == []:
        queries = []
        queries.append(items.insert().values(name='Часы настенные из серебра', price=1000))
        queries.append(items.insert().values(name='Шкатулка со дна океана', price=3000))
        queries.append(items.insert().values(name='Проклятая заколка', price=5000))
        queries.append(items.insert().values(name='Закупоренная бутылка', price=500))
        queries.append(items.insert().values(name='Дырявая шляпа', price=100))
        for query in queries:
            await database.fetch_all(query)

    # создание 100 рандомных продаж
    query = sales.select()
    if (await database.fetch_all(query)) == []:
        n = 1
        while n<101:
            query = sales.insert().values(sale_time=(datetime.now() + timedelta(weeks=(randint(-48,-1)))), item_id=(randint(1,5)), store_id=(randint(1,5)))
            await database.fetch_all(query)
            n += 1

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.get("/stores/", response_model=List[Stores])
async def read_stores():
    query = stores.select()
    return await database.fetch_all(query)

# обрабатывает GET-запрос на получение данных по топ 10 самых доходных магазинов за месяц (id + адрес + суммарная выручка)
@app.get("/stores/top/", response_model=List[StoresTop])
async def show_top_stores():
    date:str = (datetime.today() + relativedelta(months=-1)).strftime("%Y%m%d")
    query = f"""
        SELECT stores.id, stores.address, SUM(items.price) AS sum_of_sales
        FROM sales 
        JOIN stores ON sales.store_id = stores.id 
        JOIN items ON sales.item_id = items.id
        WHERE sales.sale_time >= '{date}'
        GROUP BY stores.address, stores.id
        ORDER BY sum_of_sales DESC
        LIMIT 10
        """
    return await database.fetch_all(query)

@app.get("/items/", response_model=List[Items])
async def read_items():
    query = items.select()
    return await database.fetch_all(query)

# обрабатывает GET-запрос на получение данных по топ 10 самых продаваемых товаров (id + наименование + количество проданных товаров)
@app.get("/items/top/", response_model=List[ItemsTop])
async def show_top_items():
    query = """
        SELECT items.id, items.name, COUNT(items.name) AS count_of_sales
        FROM sales 
        JOIN stores ON sales.store_id = stores.id 
        JOIN items ON sales.item_id = items.id
        GROUP BY items.name, items.id
        ORDER BY count_of_sales DESC
        LIMIT 10
        """
    return await database.fetch_all(query)     

@app.post("/sales/")
async def create_sale(sale: SalesIn):
    query = sales.insert().values(sale_time=sale.sale_time, item_id=sale.item_id, store_id=sale.store_id)
    last_record_id = await database.execute(query)
    return {**sale.dict(), "id": last_record_id}      