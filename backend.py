from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
from typing import List, Optional
from dotenv import load_dotenv
import bcrypt

load_dotenv()

app = FastAPI(title="SodaShop API")

# CORS для React
origins = [
    "http://localhost:3000",  # Для разработки
    "https://your-frontend.vercel.app",  # Замените на ваш Vercel URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение к БД
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    try:
        yield conn
    finally:
        conn.close()

# Модели
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class Drink(BaseModel):
    id: int
    brand: str
    logo: str
    name: str
    flavor: str
    vol: int
    price: int
    emoji: str
    color: str

class OrderItem(BaseModel):
    drink_id: int
    quantity: int

class OrderCreate(BaseModel):
    items: List[OrderItem]

# Инициализация БД
@app.on_event("startup")
def init_db():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS drinks (
            id SERIAL PRIMARY KEY,
            brand VARCHAR(50) NOT NULL,
            logo VARCHAR(10) NOT NULL,
            name VARCHAR(100) NOT NULL,
            flavor VARCHAR(100) NOT NULL,
            vol INT NOT NULL,
            price INT NOT NULL,
            emoji VARCHAR(10) NOT NULL,
            color VARCHAR(7) NOT NULL
        );
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            user_id INT REFERENCES users(id),
            total INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS order_items (
            id SERIAL PRIMARY KEY,
            order_id INT REFERENCES orders(id),
            drink_id INT REFERENCES drinks(id),
            quantity INT NOT NULL,
            price INT NOT NULL
        );
    """)
    # Вставка напитков, если таблица пустая
    cursor.execute("SELECT COUNT(*) FROM drinks")
    if cursor.fetchone()[0] == 0:
        drinks = [
            ("Coca-Cola", "🔴", "Coca-Cola Classic", "Классическая кола", 330, 89, "🥤", "#C8001E"),
            ("Pepsi", "🔵", "Pepsi Original", "Оригинальная", 500, 85, "🥤", "#004B93"),
            ("Sprite", "🟢", "Sprite Лимон-лайм", "Лимон и лайм", 500, 85, "🍋", "#00A550"),
            ("Fanta", "🟠", "Fanta Апельсин", "Апельсин", 500, 85, "🍊", "#FF6B00"),
            ("Red Bull", "🐂", "Red Bull Energy", "Классический", 250, 129, "⚡", "#CC1E25"),
            ("Mountain Dew", "💚", "Mtn Dew Original", "Цитрус", 500, 99, "🍈", "#88CC00"),
        ]
        cursor.executemany("INSERT INTO drinks (brand, logo, name, flavor, vol, price, emoji, color) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", drinks)
    conn.commit()
    conn.close()

# Роуты
@app.post("/register")
def register(user: UserCreate, db=Depends(get_db)):
    cursor = db.cursor()
    hashed = bcrypt.hashpw(user.password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    try:
        cursor.execute("INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s) RETURNING id",
                       (user.username, user.email, hashed))
        user_id = cursor.fetchone()["id"]
        db.commit()
        return {"user_id": user_id}
    except psycopg2.IntegrityError:
        raise HTTPException(status_code=400, detail="Пользователь уже существует")

@app.post("/login")
def login(user: UserLogin, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT id, username, email, password_hash, created_at FROM users WHERE username = %s",
                   (user.username,))
    result = cursor.fetchone()
    if not result or not bcrypt.checkpw(user.password.encode('utf-8'), result["password_hash"].encode('utf-8')):
        raise HTTPException(status_code=401, detail="Неверные данные")
    return {k: v for k, v in result.items() if k != "password_hash"}

@app.get("/drinks")
def get_drinks(db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT * FROM drinks")
    return [dict(row) for row in cursor.fetchall()]

@app.post("/orders")
def create_order(order: OrderCreate, user_id: int, db=Depends(get_db)):
    cursor = db.cursor()
    total = 0
    for item in order.items:
        cursor.execute("SELECT price FROM drinks WHERE id = %s", (item.drink_id,))
        price = cursor.fetchone()["price"]
        total += price * item.quantity

    cursor.execute("INSERT INTO orders (user_id, total) VALUES (%s, %s) RETURNING id", (user_id, total))
    order_id = cursor.fetchone()["id"]

    for item in order.items:
        cursor.execute("SELECT price FROM drinks WHERE id = %s", (item.drink_id,))
        price = cursor.fetchone()["price"]
        cursor.execute("INSERT INTO order_items (order_id, drink_id, quantity, price) VALUES (%s, %s, %s, %s)",
                       (order_id, item.drink_id, item.quantity, price))

    db.commit()
    return {"order_id": order_id, "total": total}

@app.get("/orders/{user_id}")
def get_orders(user_id: int, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("""
        SELECT o.id, o.total, o.created_at, oi.quantity, d.brand, d.logo, d.name, d.emoji
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        JOIN drinks d ON oi.drink_id = d.id
        WHERE o.user_id = %s
        ORDER BY o.created_at DESC
    """, (user_id,))
    return [dict(row) for row in cursor.fetchall()]

@app.get("/profile/{user_id}")
def get_profile(user_id: int, db=Depends(get_db)):
    cursor = db.cursor()
    cursor.execute("SELECT username, email, created_at FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    cursor.execute("""
        SELECT COUNT(*) as orders_count, SUM(total) as total_spent, SUM(oi.quantity) as drinks_count
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        WHERE o.user_id = %s
    """, (user_id,))
    stats = cursor.fetchone()
    return {**dict(user), **dict(stats)}