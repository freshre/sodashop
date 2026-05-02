"""
Приложение для заказа газированных напитков
Требования: Python 3.8+, sqlite3 (встроен), Pillow (опционально)
"""

import tkinter as tk
from tkinter import ttk, messagebox, font
import psycopg2
from psycopg2 import sql
import hashlib
import os
from datetime import datetime

# ─────────────────────────────────────────────
#  НАСТРОЙКИ БАЗЫ ДАННЫХ
# ─────────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "soda_shop",
    "user":     "postgres",
    "password": "125634",   # <-- замените на свой пароль
}

# ─────────────────────────────────────────────
#  ПАЛИТРА ЦВЕТОВ
# ─────────────────────────────────────────────
COLORS = {
    "bg":           "#0D0D1A",
    "card":         "#16162A",
    "card2":        "#1E1E35",
    "accent":       "#6C63FF",
    "accent2":      "#FF6584",
    "accent3":      "#43D9AD",
    "text":         "#E8E8F0",
    "text_dim":     "#8888AA",
    "border":       "#2A2A4A",
    "entry_bg":     "#12122A",
    "btn_hover":    "#8075FF",
    "success":      "#43D9AD",
    "danger":       "#FF6584",
    "warning":      "#FFD166",
}

FONT_FAMILY = "Segoe UI" if os.name == "nt" else "SF Pro Display"

# ─────────────────────────────────────────────
#  СИСТЕМА АДАПТИВНОГО ДИЗАЙНА
# ─────────────────────────────────────────────
class ResponsiveSizer:
    """Вычисляет размеры на основе размера окна"""
    def __init__(self, window):
        self.window = window
        self.base_width = 480
        self.base_height = 600
        self.scale = 1.0
        self.update_scale()
        self.window.bind("<Configure>", self._on_configure)
    
    def _on_configure(self, event):
        self.update_scale()
    
    def update_scale(self):
        """Обновить масштаб на основе текущего размера окна"""
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        if width > 1 and height > 1:  # Избегаем деления на ноль
            self.scale = max(width / self.base_width, height / self.base_height) * 0.8
            self.scale = max(0.6, min(self.scale, 2.0))  # Ограничиваем масштаб
    
    def font_size(self, base_size):
        """Вычислить размер шрифта с масштабом"""
        return max(8, int(base_size * self.scale))
    
    def padding(self, base_padding):
        """Вычислить отступ с масштабом"""
        return max(2, int(base_padding * self.scale))
    
    def width(self, base_width):
        """Вычислить ширину с масштабом"""
        return max(20, int(base_width * self.scale))

# ─────────────────────────────────────────────
class Database:
    def __init__(self):
        self.conn = None
        self.connect()
        self.init_schema()

    def connect(self):
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.conn.autocommit = False
        except psycopg2.OperationalError as e:
            messagebox.showerror(
                "Ошибка подключения",
                f"Не удалось подключиться к PostgreSQL.\n\n{e}\n\n"
                "Проверьте параметры в переменной DB_CONFIG в начале файла app.py"
            )
            raise SystemExit(1)

    def cursor(self):
        if self.conn.closed:
            self.connect()
        return self.conn.cursor()

    def init_schema(self):
        cur = self.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id          SERIAL PRIMARY KEY,
                username    VARCHAR(64) UNIQUE NOT NULL,
                email       VARCHAR(128) UNIQUE NOT NULL,
                password    VARCHAR(128) NOT NULL,
                created_at  TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS brands (
                id   SERIAL PRIMARY KEY,
                name VARCHAR(64) UNIQUE NOT NULL,
                logo VARCHAR(8) NOT NULL DEFAULT '🏷️'
            );

            CREATE TABLE IF NOT EXISTS drinks (
                id          SERIAL PRIMARY KEY,
                brand_id    INTEGER REFERENCES brands(id) ON DELETE CASCADE,
                name        VARCHAR(128) NOT NULL,
                flavor      VARCHAR(128),
                volume_ml   INTEGER NOT NULL DEFAULT 500,
                price       NUMERIC(8,2) NOT NULL,
                emoji       VARCHAR(8) NOT NULL DEFAULT '🥤',
                color       VARCHAR(16) NOT NULL DEFAULT '#6C63FF'
            );

            CREATE TABLE IF NOT EXISTS orders (
                id          SERIAL PRIMARY KEY,
                user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE,
                drink_id    INTEGER REFERENCES drinks(id) ON DELETE CASCADE,
                quantity    INTEGER NOT NULL DEFAULT 1,
                total_price NUMERIC(10,2) NOT NULL,
                ordered_at  TIMESTAMP DEFAULT NOW(),
                status      VARCHAR(32) DEFAULT 'completed'
            );
        """)
        self.conn.commit()
        self._seed_data(cur)
        cur.close()

    def _seed_data(self, cur):
        cur.execute("SELECT COUNT(*) FROM brands")
        if cur.fetchone()[0] > 0:
            return

        brands = [
            ("Coca-Cola", "🔴"),
            ("Pepsi",     "🔵"),
            ("Sprite",    "🟢"),
            ("Fanta",     "🟠"),
            ("Mountain Dew", "💚"),
            ("Dr Pepper", "🟤"),
            ("7UP",       "⚪"),
            ("Red Bull",  "🐂"),
        ]
        brand_ids = {}
        for name, logo in brands:
            cur.execute(
                "INSERT INTO brands (name, logo) VALUES (%s, %s) RETURNING id",
                (name, logo)
            )
            brand_ids[name] = cur.fetchone()[0]

        drinks = [
            # brand, name, flavor, vol, price, emoji, color
            ("Coca-Cola", "Coca-Cola Classic",    "Классическая кола",  330, 89.00,  "🥤", "#C8001E"),
            ("Coca-Cola", "Coca-Cola Zero",       "Без сахара",         330, 89.00,  "⬛", "#1A1A1A"),
            ("Coca-Cola", "Coca-Cola Cherry",     "Вишня",              500, 109.00, "🍒", "#9B0017"),
            ("Pepsi",     "Pepsi Original",       "Оригинальная",       500, 85.00,  "🥤", "#004B93"),
            ("Pepsi",     "Pepsi Max",            "Без сахара",         330, 79.00,  "⬛", "#000E3F"),
            ("Pepsi",     "Pepsi Mango",          "Манго",              500, 99.00,  "🥭", "#FFB700"),
            ("Sprite",    "Sprite Лимон-лайм",    "Лимон и лайм",       500, 85.00,  "🍋", "#00A550"),
            ("Sprite",    "Sprite Арбуз",         "Арбуз",              500, 95.00,  "🍉", "#FF4D6D"),
            ("Fanta",     "Fanta Апельсин",       "Апельсин",           500, 85.00,  "🍊", "#FF6B00"),
            ("Fanta",     "Fanta Клубника",       "Клубника",           500, 95.00,  "🍓", "#FF1744"),
            ("Fanta",     "Fanta Виноград",       "Виноград",           500, 95.00,  "🍇", "#7B1FA2"),
            ("Mountain Dew", "Mtn Dew Original",  "Цитрус",             500, 99.00,  "🍈", "#88CC00"),
            ("Mountain Dew", "Mtn Dew Blue",      "Голубика",           500, 109.00, "🫐", "#0066FF"),
            ("Dr Pepper", "Dr Pepper Original",   "Вишня-специи",       500, 109.00, "🥤", "#5B1A00"),
            ("7UP",       "7UP Оригинальный",     "Лимон-лайм",         500, 79.00,  "🍋", "#00B140"),
            ("Red Bull",  "Red Bull Energy",      "Классический",       250, 129.00, "⚡", "#CC1E25"),
            ("Red Bull",  "Red Bull Sugar Free",  "Без сахара",         250, 129.00, "🩵", "#0082CA"),
        ]

        for b, name, flavor, vol, price, emoji, color in drinks:
            cur.execute(
                """INSERT INTO drinks (brand_id,name,flavor,volume_ml,price,emoji,color)
                   VALUES (%s,%s,%s,%s,%s,%s,%s)""",
                (brand_ids[b], name, flavor, vol, price, emoji, color)
            )
        self.conn.commit()

    # ──── Пользователи ────
    def register_user(self, username, email, password):
        hashed = hashlib.sha256(password.encode()).hexdigest()
        cur = self.cursor()
        try:
            cur.execute(
                "INSERT INTO users (username, email, password) VALUES (%s,%s,%s) RETURNING id",
                (username, email, hashed)
            )
            uid = cur.fetchone()[0]
            self.conn.commit()
            return uid
        except psycopg2.IntegrityError as e:
            self.conn.rollback()
            if "username" in str(e):
                raise ValueError("Пользователь с таким именем уже существует")
            elif "email" in str(e):
                raise ValueError("Пользователь с таким email уже зарегистрирован")
            raise ValueError("Ошибка регистрации")
        finally:
            cur.close()

    def login_user(self, username, password):
        hashed = hashlib.sha256(password.encode()).hexdigest()
        cur = self.cursor()
        cur.execute(
            "SELECT id, username, email, created_at FROM users WHERE username=%s AND password=%s",
            (username, hashed)
        )
        row = cur.fetchone()
        cur.close()
        return row  # (id, username, email, created_at) or None

    # ──── Напитки ────
    def get_brands(self):
        cur = self.cursor()
        cur.execute("SELECT id, name, logo FROM brands ORDER BY name")
        rows = cur.fetchall()
        cur.close()
        return rows

    def get_drinks(self, brand_id=None, search=""):
        cur = self.cursor()
        query = """
            SELECT d.id, b.name, b.logo, d.name, d.flavor, d.volume_ml,
                   d.price, d.emoji, d.color
            FROM drinks d JOIN brands b ON d.brand_id = b.id
            WHERE 1=1
        """
        params = []
        if brand_id:
            query += " AND d.brand_id = %s"
            params.append(brand_id)
        if search:
            query += " AND (LOWER(d.name) LIKE %s OR LOWER(b.name) LIKE %s OR LOWER(d.flavor) LIKE %s)"
            s = f"%{search.lower()}%"
            params += [s, s, s]
        query += " ORDER BY b.name, d.name"
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        return rows

    def get_drink_by_id(self, drink_id):
        cur = self.cursor()
        cur.execute("""
            SELECT d.id, b.name, b.logo, d.name, d.flavor, d.volume_ml,
                   d.price, d.emoji, d.color
            FROM drinks d JOIN brands b ON d.brand_id = b.id
            WHERE d.id = %s
        """, (drink_id,))
        row = cur.fetchone()
        cur.close()
        return row

    # ──── Заказы ────
    def place_order(self, user_id, drink_id, quantity):
        cur = self.cursor()
        cur.execute("SELECT price FROM drinks WHERE id=%s", (drink_id,))
        price = cur.fetchone()[0]
        total = float(price) * quantity
        cur.execute(
            """INSERT INTO orders (user_id, drink_id, quantity, total_price)
               VALUES (%s,%s,%s,%s) RETURNING id""",
            (user_id, drink_id, quantity, total)
        )
        oid = cur.fetchone()[0]
        self.conn.commit()
        cur.close()
        return oid, total

    def get_order_history(self, user_id):
        cur = self.cursor()
        cur.execute("""
            SELECT o.id, b.name AS brand, b.logo, d.name AS drink,
                   d.emoji, d.volume_ml, o.quantity,
                   o.total_price, o.ordered_at, o.status
            FROM orders o
            JOIN drinks d ON o.drink_id = d.id
            JOIN brands b ON d.brand_id  = b.id
            WHERE o.user_id = %s
            ORDER BY o.ordered_at DESC
        """, (user_id,))
        rows = cur.fetchall()
        cur.close()
        return rows

    def get_user_stats(self, user_id):
        cur = self.cursor()
        cur.execute("""
            SELECT COUNT(*), COALESCE(SUM(total_price),0),
                   COALESCE(SUM(quantity),0)
            FROM orders WHERE user_id=%s
        """, (user_id,))
        row = cur.fetchone()
        cur.close()
        return row  # (orders_count, total_spent, total_drinks)


# ─────────────────────────────────────────────
#  ВСПОМОГАТЕЛЬНЫЕ ВИДЖЕТЫ
# ─────────────────────────────────────────────
def style_btn(btn, bg=None, fg=None, hover_bg=None, hover_fg=None):
    bg = bg or COLORS["accent"]
    fg = fg or COLORS["text"]
    hover_bg = hover_bg or COLORS["btn_hover"]
    hover_fg = hover_fg or COLORS["text"]
    btn.configure(bg=bg, fg=fg, activebackground=hover_bg, activeforeground=hover_fg,
                  relief="flat", cursor="hand2", bd=0)
    btn.bind("<Enter>", lambda e: btn.configure(bg=hover_bg))
    btn.bind("<Leave>", lambda e: btn.configure(bg=bg))


def entry_widget(parent, placeholder="", show="", width=30, font_size=11):
    frame = tk.Frame(parent, bg=COLORS["border"], pady=1, padx=1)
    e = tk.Entry(frame, bg=COLORS["entry_bg"], fg=COLORS["text"],
                 insertbackground=COLORS["text"], relief="flat",
                 font=(FONT_FAMILY, font_size), width=width, show=show)
    e.pack(fill="x", padx=1, pady=1, ipady=6)

    if placeholder:
        e.insert(0, placeholder)
        e.configure(fg=COLORS["text_dim"])

        def on_focus_in(event):
            if e.get() == placeholder:
                e.delete(0, "end")
                e.configure(fg=COLORS["text"])

        def on_focus_out(event):
            if not e.get():
                e.insert(0, placeholder)
                e.configure(fg=COLORS["text_dim"])

        e.bind("<FocusIn>",  on_focus_in)
        e.bind("<FocusOut>", on_focus_out)
        e._placeholder = placeholder
    else:
        e._placeholder = None
    return frame, e


def get_val(entry):
    """Возвращает значение поля, игнорируя placeholder."""
    v = entry.get().strip()
    if hasattr(entry, "_placeholder") and v == entry._placeholder:
        return ""
    return v


def make_scrollable(parent):
    canvas = tk.Canvas(parent, bg=COLORS["bg"], highlightthickness=0)
    vsb = tk.Scrollbar(parent, orient="vertical", command=canvas.yview,
                       bg=COLORS["card"], troughcolor=COLORS["bg"])
    canvas.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    inner = tk.Frame(canvas, bg=COLORS["bg"])
    win_id = canvas.create_window((0, 0), window=inner, anchor="nw")

    def on_configure(e):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig(win_id, width=canvas.winfo_width())

    inner.bind("<Configure>", on_configure)
    canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))
    canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
    return inner


# ─────────────────────────────────────────────
#  ОКНО АВТОРИЗАЦИИ / РЕГИСТРАЦИИ
# ─────────────────────────────────────────────
class AuthWindow(tk.Tk):
    def __init__(self, db: Database):
        super().__init__()
        self.db = db
        self.title("SodaShop — Вход")
        self.geometry("480x600")
        self.minsize(400, 500)
        self.resizable(True, True)
        self.configure(bg=COLORS["bg"])
        self.sizer = ResponsiveSizer(self)
        self._center()
        self._mode = "login"   # "login" | "register"
        self._build()
        self.bind("<F11>", self._toggle_fullscreen)

    def _toggle_fullscreen(self, event=None):
        self.attributes("-fullscreen", not self.attributes("-fullscreen"))

    def _center(self):
        self.update_idletasks()
        w, h = 480, 600
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _on_resize(self, event=None):
        """Обновить масштаб при изменении размера окна"""
        self.sizer.update_scale()

    def _build(self):
        self.main_frame = tk.Frame(self, bg=COLORS["bg"])
        self.main_frame.pack(fill="both", expand=True, padx=self.sizer.padding(40), pady=self.sizer.padding(20))
        self._render_login()

    def _clear(self):
        for w in self.main_frame.winfo_children():
            w.destroy()

    def _render_login(self):
        self._clear()
        f = self.main_frame

        # Логотип
        tk.Label(f, text="🥤", font=(FONT_FAMILY, self.sizer.font_size(56)), bg=COLORS["bg"],
                 fg=COLORS["accent"]).pack(pady=(self.sizer.padding(20), 0))
        tk.Label(f, text="SodaShop", font=(FONT_FAMILY, self.sizer.font_size(26), "bold"),
                 bg=COLORS["bg"], fg=COLORS["text"]).pack()
        tk.Label(f, text="Ваш любимый магазин газировки",
                 font=(FONT_FAMILY, self.sizer.font_size(10)), bg=COLORS["bg"],
                 fg=COLORS["text_dim"]).pack(pady=(0, self.sizer.padding(20)))

        # Кнопки выбора режима
        mode_frame = tk.Frame(f, bg=COLORS["bg"])
        mode_frame.pack(pady=(0, self.sizer.padding(20)))
        login_btn = tk.Button(mode_frame, text="Войти", font=(FONT_FAMILY, self.sizer.font_size(12), "bold"),
                              command=self._render_login, pady=self.sizer.padding(8), padx=self.sizer.padding(20))
        style_btn(login_btn, bg=COLORS["accent"], fg=COLORS["text"])
        login_btn.pack(side="left", padx=self.sizer.padding(5))
        reg_btn = tk.Button(mode_frame, text="Регистрация", font=(FONT_FAMILY, self.sizer.font_size(12), "bold"),
                            command=self._render_register, pady=self.sizer.padding(8), padx=self.sizer.padding(20))
        style_btn(reg_btn, bg=COLORS["accent2"], fg=COLORS["text"])
        reg_btn.pack(side="left", padx=self.sizer.padding(5))

        # Карточка
        card = tk.Frame(f, bg=COLORS["card"], pady=self.sizer.padding(30), padx=self.sizer.padding(30),
                        highlightbackground=COLORS["border"],
                        highlightthickness=1)
        card.pack(fill="x")

        tk.Label(card, text="Вход в аккаунт", font=(FONT_FAMILY, self.sizer.font_size(16), "bold"),
                 bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w", pady=(0, self.sizer.padding(20)))

        tk.Label(card, text="Имя пользователя", font=(FONT_FAMILY, self.sizer.font_size(10)),
                 bg=COLORS["card"], fg=COLORS["text_dim"]).pack(anchor="w")
        uf, self.login_user_e = entry_widget(card, "username", font_size=self.sizer.font_size(11))
        uf.pack(fill="x", pady=(self.sizer.padding(2), self.sizer.padding(12)))

        tk.Label(card, text="Пароль", font=(FONT_FAMILY, self.sizer.font_size(10)),
                 bg=COLORS["card"], fg=COLORS["text_dim"]).pack(anchor="w")
        pf, self.login_pass_e = entry_widget(card, "••••••••", show="•", font_size=self.sizer.font_size(11))
        pf.pack(fill="x", pady=(self.sizer.padding(2), self.sizer.padding(24)))

        btn = tk.Button(card, text="Войти", font=(FONT_FAMILY, self.sizer.font_size(12), "bold"),
                        command=self._do_login, pady=self.sizer.padding(10))
        style_btn(btn)
        btn.pack(fill="x")

        # Enter
        self.bind("<Return>", lambda e: self._do_login())

    def _render_register(self):
        self._clear()
        self.geometry("480x750")
        self._center()
        f = self.main_frame

        tk.Label(f, text="🥤", font=(FONT_FAMILY, self.sizer.font_size(40)), bg=COLORS["bg"],
                 fg=COLORS["accent"]).pack(pady=(self.sizer.padding(10), 0))
        tk.Label(f, text="Регистрация", font=(FONT_FAMILY, self.sizer.font_size(22), "bold"),
                 bg=COLORS["bg"], fg=COLORS["text"]).pack()
        tk.Label(f, text="Создайте свой аккаунт",
                 font=(FONT_FAMILY, self.sizer.font_size(10)), bg=COLORS["bg"],
                 fg=COLORS["text_dim"]).pack(pady=(0, self.sizer.padding(20)))

        # Кнопки выбора режима
        mode_frame = tk.Frame(f, bg=COLORS["bg"])
        mode_frame.pack(pady=(0, self.sizer.padding(20)))
        login_btn = tk.Button(mode_frame, text="Войти", font=(FONT_FAMILY, self.sizer.font_size(12), "bold"),
                              command=self._render_login, pady=self.sizer.padding(8), padx=self.sizer.padding(20))
        style_btn(login_btn, bg=COLORS["accent"], fg=COLORS["text"])
        login_btn.pack(side="left", padx=self.sizer.padding(5))
        reg_btn = tk.Button(mode_frame, text="Регистрация", font=(FONT_FAMILY, self.sizer.font_size(12), "bold"),
                            command=self._render_register, pady=self.sizer.padding(8), padx=self.sizer.padding(20))
        style_btn(reg_btn, bg=COLORS["accent2"], fg=COLORS["text"])
        reg_btn.pack(side="left", padx=self.sizer.padding(5))

        card = tk.Frame(f, bg=COLORS["card"], pady=self.sizer.padding(30), padx=self.sizer.padding(30),
                        highlightbackground=COLORS["border"],
                        highlightthickness=1)
        card.pack(fill="x")

        fields = [
            ("Имя пользователя", "username", ""),
            ("Email",            "email",    ""),
            ("Пароль",           "password", "•"),
            ("Повторите пароль", "confirm",  "•"),
        ]
        self._reg_entries = {}
        for label, key, show in fields:
            tk.Label(card, text=label, font=(FONT_FAMILY, self.sizer.font_size(10)),
                     bg=COLORS["card"], fg=COLORS["text_dim"]).pack(anchor="w")
            kw = {"show": show} if show else {}
            placeholder = label.lower() if not show else "••••••••"
            frm, ent = entry_widget(card, placeholder, font_size=self.sizer.font_size(11), **kw)
            frm.pack(fill="x", pady=(self.sizer.padding(2), self.sizer.padding(12)))
            self._reg_entries[key] = ent

        btn = tk.Button(card, text="Создать аккаунт",
                        font=(FONT_FAMILY, self.sizer.font_size(12), "bold"),
                        command=self._do_register, pady=self.sizer.padding(10))
        style_btn(btn, bg=COLORS["accent3"], fg=COLORS["bg"],
                  hover_bg="#5af0c0", hover_fg=COLORS["bg"])
        btn.pack(fill="x")

        self.bind("<Return>", lambda e: self._do_register())

    def _do_login(self):
        username = get_val(self.login_user_e)
        password = get_val(self.login_pass_e)
        if not username or not password:
            messagebox.showwarning("Внимание", "Заполните все поля")
            return
        row = self.db.login_user(username, password)
        if row is None:
            messagebox.showerror("Ошибка", "Неверное имя пользователя или пароль")
            return
        user = {"id": row[0], "username": row[1], "email": row[2], "created_at": row[3]}
        self.destroy()
        app = MainApp(self.db, user)
        app.mainloop()

    def _do_register(self):
        e = self._reg_entries
        username = get_val(e["username"])
        email    = get_val(e["email"])
        password = get_val(e["password"])
        confirm  = get_val(e["confirm"])

        if not all([username, email, password, confirm]):
            messagebox.showwarning("Внимание", "Заполните все поля")
            return
        if len(username) < 3:
            messagebox.showwarning("Внимание", "Имя пользователя минимум 3 символа")
            return
        if "@" not in email or "." not in email:
            messagebox.showwarning("Внимание", "Введите корректный email")
            return
        if len(password) < 6:
            messagebox.showwarning("Внимание", "Пароль минимум 6 символов")
            return
        if password != confirm:
            messagebox.showerror("Ошибка", "Пароли не совпадают")
            return
        try:
            uid = self.db.register_user(username, email, password)
            messagebox.showinfo("Успех", f"Аккаунт создан! Теперь войдите в систему.")
            self._render_login()
        except ValueError as err:
            messagebox.showerror("Ошибка", str(err))


# ─────────────────────────────────────────────
#  ГЛАВНОЕ ПРИЛОЖЕНИЕ (с боковым меню)
# ─────────────────────────────────────────────
class MainApp(tk.Tk):
    def __init__(self, db: Database, user: dict):
        super().__init__()
        self.db   = db
        self.user = user
        self.title(f"SodaShop — {user['username']}")
        self.geometry("1200x750")
        self.minsize(900, 600)
        self.configure(bg=COLORS["bg"])
        self.sizer = ResponsiveSizer(self)
        self.sizer.base_width = 1200
        self.sizer.base_height = 750
        self._center()
        self._cart = []          # список (drink_data, qty)
        self._active_page = None
        self._build()
        self._show_catalog()
        self.bind("<Configure>", self._on_resize)

    def _center(self):
        self.update_idletasks()
        w, h = 1200, 750
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _on_resize(self, event=None):
        """Обновить масштаб при изменении размера окна"""
        self.sizer.update_scale()

    # ── Layout ──
    def _build(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self.content = tk.Frame(self, bg=COLORS["bg"])
        self.content.grid(row=0, column=1, sticky="nsew")

    def _build_sidebar(self):
        sb = tk.Frame(self, bg=COLORS["card"], width=220)
        sb.grid(row=0, column=0, sticky="nsew")
        sb.grid_propagate(False)

        # Logo
        logo_frame = tk.Frame(sb, bg=COLORS["card"], pady=20)
        logo_frame.pack(fill="x")
        tk.Label(logo_frame, text="🥤", font=(FONT_FAMILY, 32),
                 bg=COLORS["card"], fg=COLORS["accent"]).pack()
        tk.Label(logo_frame, text="SodaShop", font=(FONT_FAMILY, 16, "bold"),
                 bg=COLORS["card"], fg=COLORS["text"]).pack()

        sep = tk.Frame(sb, bg=COLORS["border"], height=1)
        sep.pack(fill="x", padx=15)

        # Меню
        nav = tk.Frame(sb, bg=COLORS["card"], pady=10)
        nav.pack(fill="x")

        self._nav_btns = {}
        menu_items = [
            ("🛒  Каталог напитков", "catalog",  self._show_catalog),
            ("🛍️  Корзина",          "cart",     self._show_cart),
            ("👤  Профиль",          "profile",  self._show_profile),
        ]
        for label, key, cmd in menu_items:
            btn = tk.Button(nav, text=label, font=(FONT_FAMILY, 11),
                            bg=COLORS["card"], fg=COLORS["text"],
                            activebackground=COLORS["card2"],
                            activeforeground=COLORS["accent"],
                            relief="flat", anchor="w", padx=20, pady=10,
                            cursor="hand2", command=cmd)
            btn.pack(fill="x")
            self._nav_btns[key] = btn

        # Cart badge
        self.cart_badge_var = tk.StringVar(value="🛍️  Корзина")
        self._nav_btns["cart"].configure(textvariable=self.cart_badge_var)

        # Нижняя часть sidebar
        bottom = tk.Frame(sb, bg=COLORS["card"])
        bottom.pack(side="bottom", fill="x", pady=20, padx=15)

        sep2 = tk.Frame(sb, bg=COLORS["border"], height=1)
        sep2.pack(side="bottom", fill="x", padx=15, pady=5)

        tk.Label(bottom, text=f"👤 {self.user['username']}",
                 font=(FONT_FAMILY, 10, "bold"),
                 bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")

        logout_btn = tk.Button(bottom, text="Выйти из аккаунта",
                               font=(FONT_FAMILY, 9),
                               bg=COLORS["card"], fg=COLORS["danger"],
                               activebackground=COLORS["card"],
                               activeforeground=COLORS["accent2"],
                               relief="flat", cursor="hand2", anchor="w",
                               command=self._logout)
        logout_btn.pack(anchor="w", pady=(4, 0))

    def _set_active_nav(self, key):
        for k, btn in self._nav_btns.items():
            if k == key:
                btn.configure(bg=COLORS["card2"], fg=COLORS["accent"])
            else:
                btn.configure(bg=COLORS["card"], fg=COLORS["text"])
        self._active_page = key

    def _clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def _update_cart_badge(self):
        total = sum(q for _, q in self._cart)
        if total:
            self.cart_badge_var.set(f"🛍️  Корзина ({total})")
        else:
            self.cart_badge_var.set("🛍️  Корзина")

    def _logout(self):
        if messagebox.askyesno("Выход", "Выйти из аккаунта?"):
            self.destroy()
            auth = AuthWindow(self.db)
            auth.mainloop()

    # ─────────────────────────────────────────────
    #  КАТАЛОГ
    # ─────────────────────────────────────────────
    def _show_catalog(self):
        self._set_active_nav("catalog")
        self._clear_content()
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)

        # Header
        hdr = tk.Frame(self.content, bg=COLORS["bg"], pady=15, padx=20)
        hdr.grid(row=0, column=0, sticky="ew")

        tk.Label(hdr, text="Каталог напитков 🥤",
                 font=(FONT_FAMILY, 20, "bold"),
                 bg=COLORS["bg"], fg=COLORS["text"]).pack(side="left")

        # Поиск
        search_frame = tk.Frame(hdr, bg=COLORS["border"], padx=1, pady=1)
        search_frame.pack(side="right")
        self.search_var = tk.StringVar()
        search_e = tk.Entry(search_frame, textvariable=self.search_var,
                            font=(FONT_FAMILY, 11), bg=COLORS["entry_bg"],
                            fg=COLORS["text"], insertbackground=COLORS["text"],
                            relief="flat", width=24)
        search_e.insert(0, "🔍 Поиск...")
        search_e.configure(fg=COLORS["text_dim"])

        def sf_focus_in(e):
            if search_e.get() == "🔍 Поиск...":
                search_e.delete(0, "end")
                search_e.configure(fg=COLORS["text"])
        def sf_focus_out(e):
            if not search_e.get():
                search_e.insert(0, "🔍 Поиск...")
                search_e.configure(fg=COLORS["text_dim"])
        search_e.bind("<FocusIn>",  sf_focus_in)
        search_e.bind("<FocusOut>", sf_focus_out)
        search_e.pack(padx=4, pady=4, ipady=5)
        self.search_var.trace_add("write", lambda *a: self._reload_drinks())

        # Body
        body = tk.Frame(self.content, bg=COLORS["bg"])
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(1, weight=1)
        body.grid_rowconfigure(0, weight=1)

        # Бренды sidebar
        brands_panel = tk.Frame(body, bg=COLORS["card"], width=170)
        brands_panel.grid(row=0, column=0, sticky="nsew")
        brands_panel.grid_propagate(False)

        tk.Label(brands_panel, text="Бренды", font=(FONT_FAMILY, 12, "bold"),
                 bg=COLORS["card"], fg=COLORS["text_dim"],
                 pady=12).pack(fill="x", padx=12)

        self._selected_brand = tk.IntVar(value=0)

        all_btn = tk.Button(brands_panel, text="🌐  Все бренды",
                            font=(FONT_FAMILY, 10),
                            bg=COLORS["accent"], fg=COLORS["text"],
                            activebackground=COLORS["btn_hover"],
                            activeforeground=COLORS["text"],
                            relief="flat", anchor="w", padx=12, pady=7,
                            cursor="hand2",
                            command=lambda: self._filter_brand(0, all_btn))
        all_btn.pack(fill="x")
        self._brand_btns = {0: all_btn}

        for bid, bname, blogo in self.db.get_brands():
            btn = tk.Button(brands_panel, text=f"{blogo}  {bname}",
                            font=(FONT_FAMILY, 10),
                            bg=COLORS["card"], fg=COLORS["text"],
                            activebackground=COLORS["card2"],
                            activeforeground=COLORS["accent"],
                            relief="flat", anchor="w", padx=12, pady=7,
                            cursor="hand2",
                            command=lambda b=bid, bt=None: None)
            btn.configure(command=lambda b=bid, bt=btn: self._filter_brand(b, bt))
            btn.pack(fill="x")
            self._brand_btns[bid] = btn

        # Список напитков
        drinks_frame = tk.Frame(body, bg=COLORS["bg"])
        drinks_frame.grid(row=0, column=1, sticky="nsew")
        drinks_frame.grid_columnconfigure(0, weight=1)
        drinks_frame.grid_rowconfigure(0, weight=1)

        self._drinks_scroll_container = drinks_frame
        self.drinks_inner = make_scrollable(drinks_frame)

        self._current_brand_id = None
        self._reload_drinks()

    def _filter_brand(self, brand_id, clicked_btn):
        self._current_brand_id = brand_id if brand_id else None
        for bid, btn in self._brand_btns.items():
            if btn == clicked_btn:
                btn.configure(bg=COLORS["accent"], fg=COLORS["text"])
            else:
                btn.configure(bg=COLORS["card"], fg=COLORS["text"])
        self._reload_drinks()

    def _reload_drinks(self):
        for w in self.drinks_inner.winfo_children():
            w.destroy()

        search = self.search_var.get().strip()
        if search == "🔍 Поиск...":
            search = ""

        drinks = self.db.get_drinks(self._current_brand_id, search)

        if not drinks:
            tk.Label(self.drinks_inner, text="😕 Напитки не найдены",
                     font=(FONT_FAMILY, 14), bg=COLORS["bg"],
                     fg=COLORS["text_dim"]).pack(pady=60)
            return

        # Сетка карточек
        grid = tk.Frame(self.drinks_inner, bg=COLORS["bg"])
        grid.pack(fill="both", padx=15, pady=15)

        cols = 3
        for idx, drink in enumerate(drinks):
            row_i = idx // cols
            col_i = idx % cols
            grid.grid_columnconfigure(col_i, weight=1)
            self._drink_card(grid, drink, row_i, col_i)

    def _drink_card(self, parent, drink, row_i, col_i):
        # drink: (id, brand, logo, name, flavor, vol, price, emoji, color)
        did, brand, blogo, name, flavor, vol, price, emoji, color = drink

        card = tk.Frame(parent, bg=COLORS["card"],
                        highlightbackground=COLORS["border"],
                        highlightthickness=1)
        card.grid(row=row_i, column=col_i, padx=8, pady=8, sticky="nsew")

        # Цветная полоса
        bar = tk.Frame(card, bg=color, height=5)
        bar.pack(fill="x")

        inner = tk.Frame(card, bg=COLORS["card"], padx=12, pady=10)
        inner.pack(fill="both", expand=True)

        # Эмодзи и название
        top = tk.Frame(inner, bg=COLORS["card"])
        top.pack(fill="x")
        tk.Label(top, text=emoji, font=(FONT_FAMILY, 32),
                 bg=COLORS["card"]).pack(side="left")
        info = tk.Frame(top, bg=COLORS["card"])
        info.pack(side="left", padx=10, fill="x", expand=True)
        tk.Label(info, text=name, font=(FONT_FAMILY, 11, "bold"),
                 bg=COLORS["card"], fg=COLORS["text"],
                 wraplength=140, justify="left").pack(anchor="w")
        tk.Label(info, text=f"{blogo} {brand}",
                 font=(FONT_FAMILY, 9),
                 bg=COLORS["card"], fg=COLORS["text_dim"]).pack(anchor="w")

        # Вкус и объём
        tk.Label(inner, text=f"🍶 {flavor}  •  {vol} мл",
                 font=(FONT_FAMILY, 9),
                 bg=COLORS["card"], fg=COLORS["text_dim"]).pack(anchor="w", pady=(6, 0))

        # Цена и кнопка
        bottom = tk.Frame(inner, bg=COLORS["card"])
        bottom.pack(fill="x", pady=(10, 0))
        tk.Label(bottom, text=f"{float(price):.0f} ₽",
                 font=(FONT_FAMILY, 14, "bold"),
                 bg=COLORS["card"], fg=COLORS["accent"]).pack(side="left")

        add_btn = tk.Button(bottom, text="+ В корзину",
                            font=(FONT_FAMILY, 9, "bold"),
                            pady=4, padx=8,
                            command=lambda d=drink: self._open_order_dialog(d))
        style_btn(add_btn)
        add_btn.pack(side="right")

    # ─────────────────────────────────────────────
    #  ДИАЛОГ ЗАКАЗА
    # ─────────────────────────────────────────────
    def _open_order_dialog(self, drink):
        did, brand, blogo, name, flavor, vol, price, emoji, color = drink

        dlg = tk.Toplevel(self)
        dlg.title(f"Заказ: {name}")
        dlg.geometry("420x500")
        dlg.resizable(False, False)
        dlg.configure(bg=COLORS["bg"])
        dlg.grab_set()
        dlg.transient(self)

        # Center
        dlg.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()  - 420) // 2
        y = self.winfo_y() + (self.winfo_height() - 500) // 2
        dlg.geometry(f"420x500+{x}+{y}")

        # Header
        hf = tk.Frame(dlg, bg=color, pady=20)
        hf.pack(fill="x")
        tk.Label(hf, text=emoji, font=(FONT_FAMILY, 52),
                 bg=color).pack()

        body = tk.Frame(dlg, bg=COLORS["bg"], padx=30, pady=20)
        body.pack(fill="both", expand=True)

        tk.Label(body, text=name, font=(FONT_FAMILY, 16, "bold"),
                 bg=COLORS["bg"], fg=COLORS["text"],
                 wraplength=340).pack()
        tk.Label(body, text=f"{blogo} {brand}  •  {flavor}  •  {vol} мл",
                 font=(FONT_FAMILY, 10),
                 bg=COLORS["bg"], fg=COLORS["text_dim"]).pack(pady=(4, 20))

        tk.Label(body, text=f"{float(price):.0f} ₽ / шт",
                 font=(FONT_FAMILY, 22, "bold"),
                 bg=COLORS["bg"], fg=COLORS["accent"]).pack()

        # Количество
        qty_frame = tk.Frame(body, bg=COLORS["bg"])
        qty_frame.pack(pady=20)
        tk.Label(qty_frame, text="Количество:",
                 font=(FONT_FAMILY, 11),
                 bg=COLORS["bg"], fg=COLORS["text_dim"]).pack(side="left")
        qty_var = tk.IntVar(value=1)

        def dec():
            if qty_var.get() > 1:
                qty_var.set(qty_var.get() - 1)
                _update_total()
        def inc():
            if qty_var.get() < 99:
                qty_var.set(qty_var.get() + 1)
                _update_total()

        tk.Button(qty_frame, text="−", font=(FONT_FAMILY, 14, "bold"),
                  bg=COLORS["card2"], fg=COLORS["text"],
                  activebackground=COLORS["border"],
                  relief="flat", cursor="hand2", padx=10,
                  command=dec).pack(side="left", padx=(10, 0))
        qty_lbl = tk.Label(qty_frame, textvariable=qty_var,
                           font=(FONT_FAMILY, 14, "bold"),
                           bg=COLORS["bg"], fg=COLORS["text"], width=3)
        qty_lbl.pack(side="left")
        tk.Button(qty_frame, text="+", font=(FONT_FAMILY, 14, "bold"),
                  bg=COLORS["card2"], fg=COLORS["text"],
                  activebackground=COLORS["border"],
                  relief="flat", cursor="hand2", padx=10,
                  command=inc).pack(side="left")

        total_lbl = tk.Label(body, text=f"Итого: {float(price):.0f} ₽",
                             font=(FONT_FAMILY, 13),
                             bg=COLORS["bg"], fg=COLORS["text"])
        total_lbl.pack()

        def _update_total():
            total_lbl.configure(text=f"Итого: {float(price) * qty_var.get():.0f} ₽")

        # Кнопки
        btns = tk.Frame(body, bg=COLORS["bg"])
        btns.pack(fill="x", pady=(20, 0))

        def add_to_cart():
            self._add_to_cart(drink, qty_var.get())
            dlg.destroy()
            messagebox.showinfo("Корзина", f"✅ {name} x{qty_var.get()} добавлен в корзину!")

        def buy_now():
            self._place_order_direct(drink, qty_var.get())
            dlg.destroy()

        cart_btn = tk.Button(btns, text="🛍️  В корзину",
                             font=(FONT_FAMILY, 11, "bold"),
                             pady=8, command=add_to_cart)
        style_btn(cart_btn, bg=COLORS["card2"], fg=COLORS["text"],
                  hover_bg=COLORS["border"])
        cart_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

        buy_btn = tk.Button(btns, text="⚡  Купить сейчас",
                            font=(FONT_FAMILY, 11, "bold"),
                            pady=8, command=buy_now)
        style_btn(buy_btn)
        buy_btn.pack(side="left", fill="x", expand=True, padx=(6, 0))

    def _add_to_cart(self, drink, qty):
        for i, (d, q) in enumerate(self._cart):
            if d[0] == drink[0]:
                self._cart[i] = (d, q + qty)
                self._update_cart_badge()
                return
        self._cart.append((drink, qty))
        self._update_cart_badge()

    def _place_order_direct(self, drink, qty):
        try:
            oid, total = self.db.place_order(self.user["id"], drink[0], qty)
            messagebox.showinfo(
                "Заказ оформлен! 🎉",
                f"✅ Заказ #{oid} успешно оформлен!\n\n"
                f"  {drink[7]} {drink[3]}\n"
                f"  Количество: {qty} шт.\n"
                f"  Сумма: {total:.0f} ₽\n\n"
                "Спасибо за покупку!"
            )
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось оформить заказ:\n{e}")

    # ─────────────────────────────────────────────
    #  КОРЗИНА
    # ─────────────────────────────────────────────
    def _show_cart(self):
        self._set_active_nav("cart")
        self._clear_content()
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)

        # Header
        hdr = tk.Frame(self.content, bg=COLORS["bg"], pady=15, padx=20)
        hdr.grid(row=0, column=0, sticky="ew")
        tk.Label(hdr, text="Корзина 🛍️",
                 font=(FONT_FAMILY, 20, "bold"),
                 bg=COLORS["bg"], fg=COLORS["text"]).pack(side="left")

        if not self._cart:
            empty = tk.Frame(self.content, bg=COLORS["bg"])
            empty.grid(row=1, column=0, sticky="nsew")
            tk.Label(empty, text="🛒", font=(FONT_FAMILY, 64),
                     bg=COLORS["bg"]).pack(pady=(80, 10))
            tk.Label(empty, text="Корзина пуста",
                     font=(FONT_FAMILY, 18, "bold"),
                     bg=COLORS["bg"], fg=COLORS["text"]).pack()
            tk.Label(empty, text="Добавьте напитки из каталога",
                     font=(FONT_FAMILY, 11),
                     bg=COLORS["bg"], fg=COLORS["text_dim"]).pack(pady=8)
            btn = tk.Button(empty, text="Перейти в каталог",
                            font=(FONT_FAMILY, 11, "bold"),
                            pady=10, padx=20,
                            command=self._show_catalog)
            style_btn(btn)
            btn.pack(pady=20)
            return

        body = tk.Frame(self.content, bg=COLORS["bg"])
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_columnconfigure(0, weight=1)
        body.grid_rowconfigure(0, weight=1)

        scroll_c = tk.Frame(body, bg=COLORS["bg"])
        scroll_c.grid(row=0, column=0, sticky="nsew", padx=20, pady=10)
        scroll_c.grid_columnconfigure(0, weight=1)
        scroll_c.grid_rowconfigure(0, weight=1)
        inner = make_scrollable(scroll_c)

        total_price = 0
        for idx, (drink, qty) in enumerate(self._cart):
            did, brand, blogo, name, flavor, vol, price, emoji, color = drink
            item_total = float(price) * qty
            total_price += item_total

            row_f = tk.Frame(inner, bg=COLORS["card"],
                             highlightbackground=COLORS["border"],
                             highlightthickness=1)
            row_f.pack(fill="x", pady=5, padx=5)

            bar = tk.Frame(row_f, bg=color, width=5)
            bar.pack(side="left", fill="y")

            cont = tk.Frame(row_f, bg=COLORS["card"], padx=15, pady=12)
            cont.pack(fill="x", expand=True, side="left")

            left = tk.Frame(cont, bg=COLORS["card"])
            left.pack(side="left", fill="x", expand=True)

            tk.Label(left, text=f"{emoji} {name}",
                     font=(FONT_FAMILY, 13, "bold"),
                     bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")
            tk.Label(left, text=f"{blogo} {brand}  •  {flavor}  •  {vol} мл",
                     font=(FONT_FAMILY, 9),
                     bg=COLORS["card"], fg=COLORS["text_dim"]).pack(anchor="w")

            right = tk.Frame(cont, bg=COLORS["card"])
            right.pack(side="right")

            # Количество
            qty_var = tk.IntVar(value=qty)
            price_lbl = tk.Label(right, text=f"{item_total:.0f} ₽",
                                 font=(FONT_FAMILY, 13, "bold"),
                                 bg=COLORS["card"], fg=COLORS["accent"])
            price_lbl.pack(anchor="e")

            qty_ctrl = tk.Frame(right, bg=COLORS["card"])
            qty_ctrl.pack(anchor="e", pady=(5, 0))

            def dec(i=idx, qv=qty_var, pl=price_lbl, pr=price):
                if qv.get() > 1:
                    qv.set(qv.get() - 1)
                    self._cart[i] = (self._cart[i][0], qv.get())
                    pl.configure(text=f"{float(pr) * qv.get():.0f} ₽")
                    self._update_cart_badge()
                    self._update_cart_total()

            def inc(i=idx, qv=qty_var, pl=price_lbl, pr=price):
                if qv.get() < 99:
                    qv.set(qv.get() + 1)
                    self._cart[i] = (self._cart[i][0], qv.get())
                    pl.configure(text=f"{float(pr) * qv.get():.0f} ₽")
                    self._update_cart_badge()
                    self._update_cart_total()

            tk.Button(qty_ctrl, text="−", font=(FONT_FAMILY, 11, "bold"),
                      bg=COLORS["card2"], fg=COLORS["text"],
                      activebackground=COLORS["border"],
                      relief="flat", cursor="hand2", padx=8,
                      command=dec).pack(side="left")
            tk.Label(qty_ctrl, textvariable=qty_var,
                     font=(FONT_FAMILY, 11, "bold"),
                     bg=COLORS["card"], fg=COLORS["text"],
                     width=3).pack(side="left")
            tk.Button(qty_ctrl, text="+", font=(FONT_FAMILY, 11, "bold"),
                      bg=COLORS["card2"], fg=COLORS["text"],
                      activebackground=COLORS["border"],
                      relief="flat", cursor="hand2", padx=8,
                      command=inc).pack(side="left")

            # Удалить
            del_btn = tk.Button(qty_ctrl,
                                text="🗑",
                                font=(FONT_FAMILY, 11),
                                bg=COLORS["card"], fg=COLORS["danger"],
                                activebackground=COLORS["card"],
                                activeforeground=COLORS["danger"],
                                relief="flat", cursor="hand2", padx=4,
                                command=lambda i=idx: self._remove_from_cart(i))
            del_btn.pack(side="left", padx=(8, 0))

        # Footer с итогом
        footer = tk.Frame(self.content, bg=COLORS["card"],
                          highlightbackground=COLORS["border"],
                          highlightthickness=1, pady=16, padx=20)
        footer.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))

        self.cart_total_lbl = tk.Label(footer,
                                        text=f"Итого: {total_price:.0f} ₽",
                                        font=(FONT_FAMILY, 16, "bold"),
                                        bg=COLORS["card"], fg=COLORS["text"])
        self.cart_total_lbl.pack(side="left")
        self._cart_total = total_price

        clear_btn = tk.Button(footer, text="Очистить",
                              font=(FONT_FAMILY, 10),
                              pady=8, padx=14,
                              command=self._clear_cart)
        style_btn(clear_btn, bg=COLORS["card2"], fg=COLORS["danger"],
                  hover_bg=COLORS["border"])
        clear_btn.pack(side="right", padx=(8, 0))

        order_btn = tk.Button(footer, text="✅  Оформить заказ",
                              font=(FONT_FAMILY, 12, "bold"),
                              pady=8, padx=20,
                              command=self._checkout)
        style_btn(order_btn)
        order_btn.pack(side="right")

    def _update_cart_total(self):
        if hasattr(self, "cart_total_lbl") and self.cart_total_lbl.winfo_exists():
            total = sum(float(d[6]) * q for d, q in self._cart)
            self.cart_total_lbl.configure(text=f"Итого: {total:.0f} ₽")

    def _remove_from_cart(self, idx):
        self._cart.pop(idx)
        self._update_cart_badge()
        self._show_cart()

    def _clear_cart(self):
        if messagebox.askyesno("Очистить корзину", "Удалить все товары из корзины?"):
            self._cart.clear()
            self._update_cart_badge()
            self._show_cart()

    def _checkout(self):
        if not self._cart:
            return
        total = sum(float(d[6]) * q for d, q in self._cart)
        items_str = "\n".join(f"  {d[7]} {d[3]} x{q}" for d, q in self._cart)
        if not messagebox.askyesno(
            "Подтверждение заказа",
            f"Оформить заказ?\n\n{items_str}\n\nИтого: {total:.0f} ₽"
        ):
            return
        errors = []
        success = []
        for drink, qty in self._cart:
            try:
                oid, t = self.db.place_order(self.user["id"], drink[0], qty)
                success.append(f"  {drink[7]} {drink[3]} x{qty} — {t:.0f} ₽")
            except Exception as e:
                errors.append(str(e))
        self._cart.clear()
        self._update_cart_badge()
        if success:
            messagebox.showinfo(
                "Заказ оформлен! 🎉",
                "✅ Ваш заказ успешно оформлен!\n\n" + "\n".join(success) +
                f"\n\nОбщая сумма: {total:.0f} ₽\n\nСпасибо за покупку! 🥤"
            )
        if errors:
            messagebox.showerror("Ошибки", "\n".join(errors))
        self._show_cart()

    # ─────────────────────────────────────────────
    #  ПРОФИЛЬ
    # ─────────────────────────────────────────────
    def _show_profile(self):
        self._set_active_nav("profile")
        self._clear_content()
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(1, weight=1)

        # Header
        hdr = tk.Frame(self.content, bg=COLORS["bg"], pady=15, padx=20)
        hdr.grid(row=0, column=0, sticky="ew")
        tk.Label(hdr, text="Профиль 👤",
                 font=(FONT_FAMILY, 20, "bold"),
                 bg=COLORS["bg"], fg=COLORS["text"]).pack(side="left")

        # Body scrollable
        body_wrap = tk.Frame(self.content, bg=COLORS["bg"])
        body_wrap.grid(row=1, column=0, sticky="nsew")
        body_wrap.grid_columnconfigure(0, weight=1)
        body_wrap.grid_rowconfigure(0, weight=1)
        inner = make_scrollable(body_wrap)
        inner_pad = tk.Frame(inner, bg=COLORS["bg"])
        inner_pad.pack(fill="both", expand=True, padx=20, pady=10)

        # ── Карточка пользователя ──
        user_card = tk.Frame(inner_pad, bg=COLORS["card"],
                             highlightbackground=COLORS["border"],
                             highlightthickness=1, padx=25, pady=20)
        user_card.pack(fill="x", pady=(0, 16))

        avatar_frame = tk.Frame(user_card, bg=COLORS["accent"],
                                width=70, height=70)
        avatar_frame.pack(side="left")
        avatar_frame.pack_propagate(False)
        tk.Label(avatar_frame,
                 text=self.user["username"][0].upper(),
                 font=(FONT_FAMILY, 28, "bold"),
                 bg=COLORS["accent"], fg=COLORS["text"]).place(relx=.5, rely=.5, anchor="center")

        info = tk.Frame(user_card, bg=COLORS["card"], padx=20)
        info.pack(side="left", fill="x", expand=True)
        tk.Label(info, text=self.user["username"],
                 font=(FONT_FAMILY, 18, "bold"),
                 bg=COLORS["card"], fg=COLORS["text"]).pack(anchor="w")
        tk.Label(info, text=self.user["email"],
                 font=(FONT_FAMILY, 10),
                 bg=COLORS["card"], fg=COLORS["text_dim"]).pack(anchor="w")
        reg_date = self.user["created_at"]
        if hasattr(reg_date, "strftime"):
            reg_str = reg_date.strftime("%d.%m.%Y")
        else:
            reg_str = str(reg_date)[:10]
        tk.Label(info, text=f"📅 Зарегистрирован: {reg_str}",
                 font=(FONT_FAMILY, 9),
                 bg=COLORS["card"], fg=COLORS["text_dim"]).pack(anchor="w", pady=(4, 0))

        # ── Статистика ──
        stats = self.db.get_user_stats(self.user["id"])
        orders_cnt, total_spent, total_drinks = stats

        stats_frame = tk.Frame(inner_pad, bg=COLORS["bg"])
        stats_frame.pack(fill="x", pady=(0, 16))

        stat_items = [
            ("📋", "Заказов",        str(orders_cnt),             COLORS["accent"]),
            ("💰", "Потрачено",      f"{float(total_spent):.0f} ₽", COLORS["warning"]),
            ("🥤", "Напитков куплено", str(total_drinks),          COLORS["accent3"]),
        ]
        for i, (icon, label, val, clr) in enumerate(stat_items):
            stats_frame.grid_columnconfigure(i, weight=1)
            sc = tk.Frame(stats_frame, bg=COLORS["card"],
                          highlightbackground=clr, highlightthickness=2,
                          padx=16, pady=16)
            sc.grid(row=0, column=i, padx=6, sticky="nsew")
            tk.Label(sc, text=icon, font=(FONT_FAMILY, 24),
                     bg=COLORS["card"]).pack()
            tk.Label(sc, text=val, font=(FONT_FAMILY, 18, "bold"),
                     bg=COLORS["card"], fg=clr).pack()
            tk.Label(sc, text=label, font=(FONT_FAMILY, 9),
                     bg=COLORS["card"], fg=COLORS["text_dim"]).pack()

        # ── История заказов ──
        tk.Label(inner_pad, text="История заказов",
                 font=(FONT_FAMILY, 15, "bold"),
                 bg=COLORS["bg"], fg=COLORS["text"]).pack(anchor="w", pady=(10, 8))

        history = self.db.get_order_history(self.user["id"])

        if not history:
            tk.Label(inner_pad, text="😕 У вас ещё нет заказов",
                     font=(FONT_FAMILY, 12),
                     bg=COLORS["bg"], fg=COLORS["text_dim"]).pack(pady=20)
        else:
            # Таблица
            tbl_frame = tk.Frame(inner_pad, bg=COLORS["card"],
                                 highlightbackground=COLORS["border"],
                                 highlightthickness=1)
            tbl_frame.pack(fill="x", pady=(0, 20))

            # Header строка
            cols_cfg = [
                ("#",         4,  COLORS["text_dim"]),
                ("Бренд",     12, COLORS["text_dim"]),
                ("Напиток",   22, COLORS["text_dim"]),
                ("Кол-во",    7,  COLORS["text_dim"]),
                ("Сумма",     10, COLORS["text_dim"]),
                ("Дата",      14, COLORS["text_dim"]),
                ("Статус",    10, COLORS["text_dim"]),
            ]
            hdr_row = tk.Frame(tbl_frame, bg=COLORS["card2"])
            hdr_row.pack(fill="x")
            for col_text, width, color in cols_cfg:
                tk.Label(hdr_row, text=col_text, width=width,
                         font=(FONT_FAMILY, 9, "bold"),
                         bg=COLORS["card2"], fg=color,
                         anchor="w", padx=8, pady=8).pack(side="left")

            # Строки
            for i, row in enumerate(history):
                oid, brand, blogo, drink_name, demoji, vol, qty, total, ts, status = row

                bg_row = COLORS["card"] if i % 2 == 0 else COLORS["card2"]
                r = tk.Frame(tbl_frame, bg=bg_row)
                r.pack(fill="x")

                # Подсветка при наведении
                def on_enter(e, fr=r, bg=bg_row):
                    fr.configure(bg=COLORS["border"])
                    for child in fr.winfo_children():
                        try: child.configure(bg=COLORS["border"])
                        except: pass
                def on_leave(e, fr=r, bg=bg_row):
                    fr.configure(bg=bg)
                    for child in fr.winfo_children():
                        try: child.configure(bg=bg)
                        except: pass
                r.bind("<Enter>", on_enter)
                r.bind("<Leave>", on_leave)

                if hasattr(ts, "strftime"):
                    ts_str = ts.strftime("%d.%m.%Y %H:%M")
                else:
                    ts_str = str(ts)[:16]

                status_color = COLORS["success"] if status == "completed" else COLORS["warning"]
                status_text  = "✅ Выполнен" if status == "completed" else status

                cells = [
                    (f"#{oid}",                          4,  COLORS["text_dim"],  bg_row),
                    (f"{blogo} {brand}",                 12, COLORS["text"],       bg_row),
                    (f"{demoji} {drink_name}",           22, COLORS["text"],       bg_row),
                    (f"{qty} шт.",                       7,  COLORS["accent"],     bg_row),
                    (f"{float(total):.0f} ₽",           10, COLORS["warning"],    bg_row),
                    (ts_str,                             14, COLORS["text_dim"],  bg_row),
                    (status_text,                        10, status_color,        bg_row),
                ]
                for txt, width, fg_color, bg_color in cells:
                    lbl = tk.Label(r, text=txt, width=width,
                                   font=(FONT_FAMILY, 9),
                                   bg=bg_color, fg=fg_color,
                                   anchor="w", padx=8, pady=7)
                    lbl.pack(side="left")
                    r.bind("<Enter>", on_enter)
                    r.bind("<Leave>", on_leave)
                    lbl.bind("<Enter>", on_enter)
                    lbl.bind("<Leave>", on_leave)


# ─────────────────────────────────────────────
#  ТОЧКА ВХОДА
# ─────────────────────────────────────────────
if __name__ == "__main__":
    db = Database()
    root = AuthWindow(db)
    root.mainloop()
