# SodaShop - Веб-приложение для заказа газировки

Это веб-приложение для заказа газировки с регистрацией пользователей, корзиной и историей заказов.

## Функции
- Регистрация и авторизация пользователей
- Просмотр каталога напитков
- Добавление в корзину и оформление заказов
- Просмотр истории заказов
- Профиль пользователя с статистикой

## Технологии
- **Backend**: FastAPI (Python)
- **Frontend**: React + TypeScript + Tailwind CSS
- **База данных**: PostgreSQL (Supabase)
- **Развертывание**: Railway (backend), Vercel (frontend)

## Локальная разработка

### Предварительные требования
- Python 3.8+
- Node.js 16+
- PostgreSQL (локально или Supabase)

### Установка

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/your-username/sodashop.git
   cd sodashop
   ```

2. Настройте backend:
   ```bash
   cd backend
   python -m venv venv
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

3. Настройте базу данных:
   - Создайте проект на [Supabase](https://supabase.com)
   - Скопируйте connection string
   - Создайте `.env` файл:
     ```
     DATABASE_URL=postgresql://user:password@host:port/dbname
     ```

4. Запустите backend:
   ```bash
   python backend.py
   ```

5. Настройте frontend:
   ```bash
   cd ..
   npm install
   npm run dev
   ```

6. Откройте http://localhost:3000

## Развертывание

### 1. База данных (Supabase)
1. Зарегистрируйтесь на Supabase
2. Создайте новый проект
3. Скопируйте DATABASE_URL из Settings > Database

### 2. Backend (Railway)
1. Зарегистрируйтесь на Railway
2. Создайте новый проект из GitHub
3. Добавьте переменную окружения DATABASE_URL
4. Railway автоматически развернет backend

### 3. Frontend (Vercel)
1. Зарегистрируйтесь на Vercel
2. Импортируйте репозиторий из GitHub
3. Добавьте переменную окружения VITE_API_BASE с URL backend (например, https://your-app.railway.app)
4. Vercel развернет frontend

## API Endpoints

- `POST /register` - Регистрация
- `POST /login` - Вход
- `GET /drinks` - Получить напитки
- `POST /orders` - Создать заказ
- `GET /orders/{user_id}` - Получить заказы пользователя
- `GET /profile/{user_id}` - Получить профиль пользователя

## Структура проекта
```
/
├── backend.py          # FastAPI сервер
├── requirements.txt    # Зависимости Python
├── .env               # Переменные окружения
├── src/
│   ├── App.tsx        # Главный компонент React
│   ├── main.tsx       # Точка входа
│   └── index.css      # Стили
├── package.json       # Зависимости Node.js
└── vite.config.ts     # Конфиг Vite
```

## Безопасность
- Пароли хэшируются с bcrypt
- CORS настроен для разрешенных доменов
- Используйте HTTPS в продакшене

## Лицензия
MIT