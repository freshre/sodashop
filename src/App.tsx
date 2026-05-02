import { useState, useEffect } from "react";
import axios from "axios";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000"; // Для продакшена установите переменную окружения

const COLORS = {
  bg: "#0D0D1A",
  card: "#16162A",
  card2: "#1E1E35",
  accent: "#6C63FF",
  accent2: "#FF6584",
  accent3: "#43D9AD",
  border: "#2A2A4A",
  text: "#E8E8F0",
  textDim: "#8888AA",
  warning: "#FFD166",
};

interface Drink {
  id: number;
  brand: string;
  logo: string;
  name: string;
  flavor: string;
  vol: number;
  price: number;
  emoji: string;
  color: string;
}

interface Order {
  id: number;
  brand: string;
  logo: string;
  drink: string;
  emoji: string;
  qty: number;
  total: number;
  date: string;
}

interface User {
  id: number;
  username: string;
  email: string;
  created_at: string;
}

function App() {
  const [mode, setMode] = useState<"auth" | "main">("auth");
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [user, setUser] = useState<User | null>(null);
  const [drinks, setDrinks] = useState<Drink[]>([]);
  const [cart, setCart] = useState<{ [key: number]: number }>({});
  const [orders, setOrders] = useState<Order[]>([]);
  const [profile, setProfile] = useState<any>(null);
  const [activeTab, setActiveTab] = useState<"shop" | "cart" | "history" | "profile">("shop");

  useEffect(() => {
    if (mode === "main") {
      fetchDrinks();
      fetchOrders();
      fetchProfile();
    }
  }, [mode, user]);

  const fetchDrinks = async () => {
    try {
      const res = await axios.get(`${API_BASE}/drinks`);
      setDrinks(res.data);
    } catch (err) {
      console.error("Ошибка загрузки напитков:", err);
    }
  };

  const fetchOrders = async () => {
    if (!user) return;
    try {
      const res = await axios.get(`${API_BASE}/orders/${user.id}`);
      setOrders(res.data.map((o: any) => ({
        id: o.id,
        brand: o.brand,
        logo: o.logo,
        drink: o.name,
        emoji: o.emoji,
        qty: o.quantity,
        total: o.total,
        date: new Date(o.created_at).toLocaleString("ru-RU"),
      })));
    } catch (err) {
      console.error("Ошибка загрузки заказов:", err);
    }
  };

  const fetchProfile = async () => {
    if (!user) return;
    try {
      const res = await axios.get(`${API_BASE}/profile/${user.id}`);
      setProfile(res.data);
    } catch (err) {
      console.error("Ошибка загрузки профиля:", err);
    }
  };

  const handleLogin = async (username: string, password: string) => {
    try {
      const res = await axios.post(`${API_BASE}/login`, { username, password });
      setUser(res.data);
      setMode("main");
    } catch (err: any) {
      alert(err.response?.data?.detail || "Ошибка входа");
    }
  };

  const handleRegister = async (username: string, email: string, password: string) => {
    try {
      await axios.post(`${API_BASE}/register`, { username, email, password });
      alert("Регистрация успешна! Войдите в аккаунт.");
      setAuthMode("login");
    } catch (err: any) {
      alert(err.response?.data?.detail || "Ошибка регистрации");
    }
  };

  const addToCart = (drinkId: number) => {
    setCart((prev) => ({ ...prev, [drinkId]: (prev[drinkId] || 0) + 1 }));
  };

  const removeFromCart = (drinkId: number) => {
    setCart((prev) => {
      const newCart = { ...prev };
      if (newCart[drinkId] > 1) newCart[drinkId]--;
      else delete newCart[drinkId];
      return newCart;
    });
  };

  const checkout = async () => {
    if (!user) return;
    const items = Object.entries(cart).map(([drinkId, qty]) => ({ drink_id: parseInt(drinkId), quantity: qty }));
    try {
      await axios.post(`${API_BASE}/orders`, { items }, { params: { user_id: user.id } });
      setCart({});
      fetchOrders();
      alert("Заказ оформлен!");
    } catch (err) {
      alert("Ошибка оформления заказа");
    }
  };

  const logout = () => {
    setUser(null);
    setMode("auth");
    setCart({});
    setOrders([]);
    setProfile(null);
  };

  if (mode === "auth") {
    return <AuthScreen mode={authMode} setMode={setAuthMode} onLogin={handleLogin} onRegister={handleRegister} />;
  }

  return (
    <div className="min-h-screen flex" style={{ background: COLORS.bg, color: COLORS.text }}>
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} user={user} logout={logout} />
      <MainContent
        activeTab={activeTab}
        drinks={drinks}
        cart={cart}
        orders={orders}
        profile={profile}
        addToCart={addToCart}
        removeFromCart={removeFromCart}
        checkout={checkout}
      />
    </div>
  );
}

function AuthScreen({ mode, setMode, onLogin, onRegister }: any) {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const submit = () => {
    if (mode === "login") {
      onLogin(username, password);
    } else {
      onRegister(username, email, password);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen py-8 px-6" style={{ background: COLORS.bg }}>
      <div className="text-6xl mb-2">🥤</div>
      <div className="text-2xl font-bold mb-1">SodaShop</div>
      <div className="text-sm mb-6" style={{ color: COLORS.textDim }}>Ваш любимый магазин газировки</div>

      <div className="w-full max-w-xs rounded-xl p-6" style={{ background: COLORS.card, border: `1px solid ${COLORS.border}` }}>
        <div className="flex mb-4">
          <button
            className={`flex-1 py-2 rounded-l ${mode === "login" ? "bg-blue-500" : "bg-gray-600"}`}
            onClick={() => setMode("login")}
          >
            Вход
          </button>
          <button
            className={`flex-1 py-2 rounded-r ${mode === "register" ? "bg-blue-500" : "bg-gray-600"}`}
            onClick={() => setMode("register")}
          >
            Регистрация
          </button>
        </div>

        <div className="text-base font-bold mb-4">{mode === "login" ? "Вход в аккаунт" : "Регистрация"}</div>

        <input
          type="text"
          placeholder="Имя пользователя"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          className="w-full mb-3 px-3 py-2 rounded text-sm"
          style={{ background: COLORS.card2, color: COLORS.text, border: `1px solid ${COLORS.border}` }}
        />

        {mode === "register" && (
          <input
            type="email"
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full mb-3 px-3 py-2 rounded text-sm"
            style={{ background: COLORS.card2, color: COLORS.text, border: `1px solid ${COLORS.border}` }}
          />
        )}

        <input
          type="password"
          placeholder="Пароль"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full mb-5 px-3 py-2 rounded text-sm"
          style={{ background: COLORS.card2, color: COLORS.text, border: `1px solid ${COLORS.border}` }}
        />

        <button
          onClick={submit}
          className="w-full py-2 rounded font-bold text-white text-sm transition-all hover:opacity-80"
          style={{ background: COLORS.accent }}
        >
          {mode === "login" ? "Войти" : "Зарегистрироваться"}
        </button>
      </div>
    </div>
  );
}

function Sidebar({ activeTab, setActiveTab, user, logout }: any) {
  return (
    <div className="w-64 p-4" style={{ background: COLORS.card }}>
      <div className="text-xl font-bold mb-6">🥤 SodaShop</div>
      <nav className="space-y-2">
        <button
          onClick={() => setActiveTab("shop")}
          className={`w-full text-left py-2 px-4 rounded ${activeTab === "shop" ? "bg-blue-500" : "hover:bg-gray-700"}`}
        >
          🛒 Магазин
        </button>
        <button
          onClick={() => setActiveTab("cart")}
          className={`w-full text-left py-2 px-4 rounded ${activeTab === "cart" ? "bg-blue-500" : "hover:bg-gray-700"}`}
        >
          🛍️ Корзина ({Object.values(cart).reduce((a, b) => a + b, 0)})
        </button>
        <button
          onClick={() => setActiveTab("history")}
          className={`w-full text-left py-2 px-4 rounded ${activeTab === "history" ? "bg-blue-500" : "hover:bg-gray-700"}`}
        >
          📜 История
        </button>
        <button
          onClick={() => setActiveTab("profile")}
          className={`w-full text-left py-2 px-4 rounded ${activeTab === "profile" ? "bg-blue-500" : "hover:bg-gray-700"}`}
        >
          👤 Профиль
        </button>
      </nav>
      <div className="mt-8">
        <div className="text-sm">👤 {user?.username}</div>
        <button onClick={logout} className="text-red-500 text-sm mt-2">Выйти</button>
      </div>
    </div>
  );
}

function MainContent({ activeTab, drinks, cart, orders, profile, addToCart, removeFromCart, checkout }: any) {
  if (activeTab === "shop") {
    return (
      <div className="flex-1 p-6">
        <h1 className="text-2xl font-bold mb-4">Магазин</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {drinks.map((drink: Drink) => (
            <div key={drink.id} className="p-4 rounded" style={{ background: COLORS.card, border: `1px solid ${COLORS.border}` }}>
              <div className="text-4xl mb-2">{drink.emoji}</div>
              <div className="font-bold">{drink.name}</div>
              <div className="text-sm" style={{ color: COLORS.textDim }}>{drink.flavor} • {drink.vol}ml</div>
              <div className="text-lg font-bold mt-2">{drink.price}₽</div>
              <button
                onClick={() => addToCart(drink.id)}
                className="mt-2 w-full py-2 rounded font-bold text-white"
                style={{ background: COLORS.accent }}
              >
                Добавить в корзину
              </button>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (activeTab === "cart") {
    const cartItems = Object.entries(cart).map(([id, qty]) => {
      const drink = drinks.find((d) => d.id === parseInt(id));
      return { ...drink, qty };
    });
    const total = cartItems.reduce((sum, item) => sum + item.price * item.qty, 0);

    return (
      <div className="flex-1 p-6">
        <h1 className="text-2xl font-bold mb-4">Корзина</h1>
        {cartItems.length === 0 ? (
          <p>Корзина пуста</p>
        ) : (
          <>
            {cartItems.map((item: any) => (
              <div key={item.id} className="flex justify-between items-center mb-2 p-2 rounded" style={{ background: COLORS.card }}>
                <div>{item.emoji} {item.name} x{item.qty}</div>
                <div className="flex items-center">
                  <button onClick={() => removeFromCart(item.id)} className="px-2">-</button>
                  <span className="mx-2">{item.qty}</span>
                  <button onClick={() => addToCart(item.id)} className="px-2">+</button>
                  <span className="ml-4">{item.price * item.qty}₽</span>
                </div>
              </div>
            ))}
            <div className="text-xl font-bold mt-4">Итого: {total}₽</div>
            <button
              onClick={checkout}
              className="mt-4 w-full py-2 rounded font-bold text-white"
              style={{ background: COLORS.accent }}
            >
              Оформить заказ
            </button>
          </>
        )}
      </div>
    );
  }

  if (activeTab === "history") {
    return (
      <div className="flex-1 p-6">
        <h1 className="text-2xl font-bold mb-4">История заказов</h1>
        {orders.map((order: Order) => (
          <div key={order.id} className="mb-2 p-4 rounded" style={{ background: COLORS.card }}>
            <div>{order.emoji} {order.drink} x{order.qty} - {order.total}₽</div>
            <div className="text-sm" style={{ color: COLORS.textDim }}>{order.date}</div>
          </div>
        ))}
      </div>
    );
  }

  if (activeTab === "profile") {
    return (
      <div className="flex-1 p-6">
        <h1 className="text-2xl font-bold mb-4">Профиль</h1>
        {profile && (
          <div className="p-4 rounded" style={{ background: COLORS.card }}>
            <div className="text-xl font-bold">{profile.username}</div>
            <div>{profile.email}</div>
            <div>Зарегистрирован: {new Date(profile.created_at).toLocaleDateString("ru-RU")}</div>
            <div className="mt-4">
              <div>Заказов: {profile.orders_count || 0}</div>
              <div>Потрачено: {profile.total_spent || 0}₽</div>
              <div>Напитков: {profile.drinks_count || 0}</div>
            </div>
          </div>
        )}
      </div>
    );
  }

  return null;
}

export default App;
          <div className="flex justify-center mt-4 gap-1 text-xs">
            <span style={{ color: COLORS.textDim }}>Нет аккаунта?</span>
            <button className="font-bold" style={{ color: COLORS.accent }} onClick={() => setMode("register")}>Зарегистрироваться</button>
          </div>
        </div>
      ) : (
        <div className="w-full max-w-xs rounded-xl p-6" style={{ background: COLORS.card, border: `1px solid ${COLORS.border}` }}>
          <div className="text-base font-bold mb-4" style={{ color: COLORS.text }}>Регистрация</div>
          {["Имя пользователя", "Email", "Пароль", "Повторите пароль"].map((label, i) => (
            <div key={i}>
              <div className="text-xs mb-1" style={{ color: COLORS.textDim }}>{label}</div>
              <div className="rounded mb-3 px-3 py-2 text-sm" style={{ background: COLORS.card2, color: COLORS.textDim, border: `1px solid ${COLORS.border}` }}>
                {label.toLowerCase().includes("пароль") ? "••••••••" : label.toLowerCase()}
              </div>
            </div>
          ))}
          <button className="w-full rounded py-2 font-bold text-sm transition-all hover:opacity-80" style={{ background: COLORS.accent3, color: COLORS.bg }}>Создать аккаунт</button>
          <div className="flex justify-center mt-3 gap-1 text-xs">
            <span style={{ color: COLORS.textDim }}>Уже есть аккаунт?</span>
            <button className="font-bold" style={{ color: COLORS.accent }} onClick={() => setMode("login")}>Войти</button>
          </div>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────
//  Компонент превью — Каталог
// ─────────────────────────────────────────────
function CatalogPreview() {
  const [selected, setSelected] = useState<number | null>(null);

  return (
    <div style={{ background: COLORS.bg, minHeight: 540 }} className="p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="font-bold text-lg" style={{ color: COLORS.text }}>Каталог напитков 🥤</div>
        <div className="rounded px-3 py-1 text-sm" style={{ background: COLORS.card2, color: COLORS.textDim, border: `1px solid ${COLORS.border}` }}>🔍 Поиск...</div>
      </div>
      <div className="flex gap-3">
        {/* Бренды */}
        <div className="rounded-lg p-3 w-28 flex-shrink-0" style={{ background: COLORS.card, border: `1px solid ${COLORS.border}` }}>
          <div className="text-xs font-bold mb-2" style={{ color: COLORS.textDim }}>Бренды</div>
          {["🌐 Все", "🔴 Cola", "🔵 Pepsi", "🟢 Sprite", "🟠 Fanta", "🐂 Red Bull"].map((b, i) => (
            <div key={i} className="text-xs rounded px-2 py-1.5 mb-1 cursor-pointer transition-all hover:opacity-80" style={{ background: i === 0 ? COLORS.accent : "transparent", color: i === 0 ? "white" : COLORS.textDim }}>
              {b}
            </div>
          ))}
        </div>
        {/* Карточки */}
        <div className="grid grid-cols-3 gap-2 flex-1">
          {mockDrinks.map((d) => (
            <div key={d.id} className="rounded-lg overflow-hidden cursor-pointer transition-all hover:scale-105" style={{ background: COLORS.card, border: `1px solid ${COLORS.border}` }} onClick={() => setSelected(d.id)}>
              <div style={{ background: d.color, height: 4 }} />
              <div className="p-2">
                <div className="flex items-start gap-1">
                  <span className="text-2xl">{d.emoji}</span>
                  <div>
                    <div className="text-xs font-bold leading-tight" style={{ color: COLORS.text }}>{d.name}</div>
                    <div className="text-xs" style={{ color: COLORS.textDim }}>{d.logo} {d.brand}</div>
                  </div>
                </div>
                <div className="text-xs mt-1" style={{ color: COLORS.textDim }}>{d.vol} мл</div>
                <div className="flex justify-between items-center mt-2">
                  <span className="text-sm font-bold" style={{ color: COLORS.accent }}>{d.price} ₽</span>
                  <button className="text-xs px-2 py-0.5 rounded font-bold" style={{ background: COLORS.accent, color: "white" }}>+</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Диалог заказа */}
      {selected && (
        <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={() => setSelected(null)}>
          <div className="rounded-xl overflow-hidden w-72" style={{ background: COLORS.bg, border: `1px solid ${COLORS.border}` }} onClick={(e) => e.stopPropagation()}>
            {(() => {
              const d = mockDrinks.find((x) => x.id === selected)!;
              return (
                <>
                  <div className="flex items-center justify-center py-8" style={{ background: d.color }}>
                    <span className="text-6xl">{d.emoji}</span>
                  </div>
                  <div className="p-5">
                    <div className="font-bold text-base mb-1" style={{ color: COLORS.text }}>{d.name}</div>
                    <div className="text-xs mb-3" style={{ color: COLORS.textDim }}>{d.logo} {d.brand} • {d.flavor} • {d.vol} мл</div>
                    <div className="text-2xl font-bold mb-4" style={{ color: COLORS.accent }}>{d.price} ₽ / шт</div>
                    <div className="flex items-center gap-2 mb-4">
                      <span className="text-sm" style={{ color: COLORS.textDim }}>Количество:</span>
                      <button className="w-7 h-7 rounded font-bold text-white" style={{ background: COLORS.card2 }}>−</button>
                      <span className="font-bold text-base w-6 text-center" style={{ color: COLORS.text }}>1</span>
                      <button className="w-7 h-7 rounded font-bold text-white" style={{ background: COLORS.card2 }}>+</button>
                    </div>
                    <div className="flex gap-2">
                      <button className="flex-1 py-2 rounded font-bold text-sm" style={{ background: COLORS.card2, color: COLORS.text }}>🛍️ В корзину</button>
                      <button className="flex-1 py-2 rounded font-bold text-sm" style={{ background: COLORS.accent, color: "white" }}>⚡ Купить</button>
                    </div>
                  </div>
                </>
              );
            })()}
          </div>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────
//  Компонент превью — Профиль
// ─────────────────────────────────────────────
function ProfilePreview() {
  return (
    <div style={{ background: COLORS.bg, minHeight: 540 }} className="p-4 overflow-y-auto">
      <div className="font-bold text-lg mb-4" style={{ color: COLORS.text }}>Профиль 👤</div>

      {/* Карточка пользователя */}
      <div className="rounded-xl p-4 flex items-center gap-4 mb-4" style={{ background: COLORS.card, border: `1px solid ${COLORS.border}` }}>
        <div className="w-14 h-14 rounded-lg flex items-center justify-center text-2xl font-bold flex-shrink-0" style={{ background: COLORS.accent, color: "white" }}>A</div>
        <div>
          <div className="font-bold text-base" style={{ color: COLORS.text }}>alexuser</div>
          <div className="text-xs" style={{ color: COLORS.textDim }}>alex@example.com</div>
          <div className="text-xs mt-1" style={{ color: COLORS.textDim }}>📅 Зарегистрирован: 01.01.2025</div>
        </div>
      </div>

      {/* Статистика */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        {[
          { icon: "📋", label: "Заказов",         val: "26",       color: COLORS.accent },
          { icon: "💰", label: "Потрачено",        val: "2 340 ₽",  color: COLORS.warning },
          { icon: "🥤", label: "Напитков куплено", val: "58",       color: COLORS.accent3 },
        ].map((s, i) => (
          <div key={i} className="rounded-xl p-3 text-center" style={{ background: COLORS.card, border: `2px solid ${s.color}` }}>
            <div className="text-2xl">{s.icon}</div>
            <div className="font-bold text-base" style={{ color: s.color }}>{s.val}</div>
            <div className="text-xs" style={{ color: COLORS.textDim }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* История заказов */}
      <div className="font-bold mb-2" style={{ color: COLORS.text }}>История заказов</div>
      <div className="rounded-xl overflow-hidden" style={{ background: COLORS.card, border: `1px solid ${COLORS.border}` }}>
        <div className="grid text-xs font-bold px-3 py-2" style={{ gridTemplateColumns: "3rem 7rem 1fr 4rem 5rem 8rem", background: COLORS.card2, color: COLORS.textDim }}>
          <span>#</span><span>Бренд</span><span>Напиток</span><span>Кол-во</span><span>Сумма</span><span>Дата</span>
        </div>
        {mockHistory.map((h, i) => (
          <div key={h.id} className="grid text-xs px-3 py-2 items-center transition-all hover:opacity-80" style={{ gridTemplateColumns: "3rem 7rem 1fr 4rem 5rem 8rem", background: i % 2 === 0 ? COLORS.card : COLORS.card2, color: COLORS.text }}>
            <span style={{ color: COLORS.textDim }}>#{h.id}</span>
            <span>{h.logo} {h.brand}</span>
            <span>{h.emoji} {h.drink}</span>
            <span style={{ color: COLORS.accent }}>{h.qty} шт.</span>
            <span style={{ color: COLORS.warning }}>{h.total} ₽</span>
            <span style={{ color: COLORS.textDim }}>{h.date}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
//  Главный App
// ─────────────────────────────────────────────
export default function App() {
  const [activeTab, setActiveTab] = useState<"auth" | "catalog" | "profile" | "code">("auth");
  const [authMode, setAuthMode] = useState("login");

  const tabs = [
    { key: "auth",    label: "🔐 Авторизация" },
    { key: "catalog", label: "🥤 Каталог" },
    { key: "profile", label: "👤 Профиль" },
    { key: "code",    label: "📦 Запуск" },
  ] as const;

  const sqlCode = `-- Создание базы данных
CREATE DATABASE soda_shop;

-- Все таблицы создаются автоматически при запуске app.py`;

  const pythonSetup = [
    { step: "1", title: "Установите Python 3.8+", cmd: "python --version", note: "Убедитесь что Python установлен" },
    { step: "2", title: "Установите зависимости", cmd: "pip install psycopg2-binary", note: "Драйвер для PostgreSQL" },
    { step: "3", title: "Создайте базу данных", cmd: sqlCode, note: "Выполните в psql" },
    { step: "4", title: "Настройте DB_CONFIG в app.py", cmd: `DB_CONFIG = {\n  "host":     "localhost",\n  "port":     5432,\n  "dbname":   "soda_shop",\n  "user":     "postgres",\n  "password": "ВАШ_ПАРОЛЬ",\n}`, note: "Укажите ваши данные подключения" },
    { step: "5", title: "Запустите приложение", cmd: "python app.py", note: "Приложение откроется автоматически" },
  ];

  const features = [
    { icon: "🔐", title: "Авторизация",    desc: "Вход и регистрация с хешированием паролей SHA-256 и хранением в PostgreSQL" },
    { icon: "🥤", title: "Каталог",        desc: "17 напитков от 8 брендов с фильтрацией по бренду и поиском" },
    { icon: "🛒", title: "Корзина",        desc: "Добавление, изменение количества, удаление товаров. Оформление одним кликом" },
    { icon: "👤", title: "Профиль",        desc: "Аватар, статистика и полная история заказов с датой и суммой" },
    { icon: "🎨", title: "Тёмная тема",    desc: "Современный тёмный дизайн на Tkinter с плавными переходами" },
    { icon: "🗄️", title: "PostgreSQL",     desc: "Полноценная реляционная БД: пользователи, бренды, напитки, заказы" },
  ];

  return (
    <div className="min-h-screen" style={{ background: "#08081a", fontFamily: "'Segoe UI', sans-serif" }}>
      {/* Hero Header */}
      <div className="relative overflow-hidden" style={{ background: "linear-gradient(135deg, #0D0D1A 0%, #16162A 50%, #1a1035 100%)" }}>
        <div className="absolute inset-0 pointer-events-none" style={{ background: "radial-gradient(ellipse at 30% 50%, rgba(108,99,255,0.15) 0%, transparent 60%), radial-gradient(ellipse at 70% 30%, rgba(255,101,132,0.1) 0%, transparent 50%)" }} />
        <div className="relative max-w-5xl mx-auto px-6 py-16 text-center">
          <div className="inline-flex items-center gap-2 rounded-full px-4 py-1.5 mb-6 text-xs font-semibold" style={{ background: "rgba(108,99,255,0.15)", color: COLORS.accent, border: `1px solid rgba(108,99,255,0.3)` }}>
            🐍 Python + Tkinter + PostgreSQL
          </div>
          <div className="text-7xl mb-4">🥤</div>
          <h1 className="text-4xl md:text-5xl font-extrabold mb-4 leading-tight" style={{ color: COLORS.text }}>
            Soda<span style={{ color: COLORS.accent }}>Shop</span>
          </h1>
          <p className="text-lg max-w-xl mx-auto leading-relaxed" style={{ color: COLORS.textDim }}>
            Десктопное приложение для заказа газированных напитков с авторизацией, каталогом, корзиной и историей заказов
          </p>

          {/* Stats badges */}
          <div className="flex flex-wrap justify-center gap-3 mt-8">
            {["17 напитков", "8 брендов", "PostgreSQL БД", "Тёмная тема", "Tkinter GUI"].map((b) => (
              <span key={b} className="px-3 py-1 rounded-full text-xs font-medium" style={{ background: COLORS.card2, color: COLORS.text, border: `1px solid ${COLORS.border}` }}>{b}</span>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-10">
        {/* Возможности */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-12">
          {features.map((f) => (
            <div key={f.title} className="rounded-xl p-5 transition-all hover:scale-105" style={{ background: COLORS.card, border: `1px solid ${COLORS.border}` }}>
              <div className="text-3xl mb-3">{f.icon}</div>
              <div className="font-bold mb-1" style={{ color: COLORS.text }}>{f.title}</div>
              <div className="text-sm leading-relaxed" style={{ color: COLORS.textDim }}>{f.desc}</div>
            </div>
          ))}
        </div>

        {/* Превью приложения */}
        <div className="mb-12">
          <div className="text-center mb-6">
            <h2 className="text-2xl font-bold mb-2" style={{ color: COLORS.text }}>Предварительный просмотр</h2>
            <p className="text-sm" style={{ color: COLORS.textDim }}>Интерактивный макет интерфейса приложения</p>
          </div>

          {/* Окно Tkinter */}
          <div className="rounded-2xl overflow-hidden shadow-2xl" style={{ background: COLORS.card, border: `1px solid ${COLORS.border}` }}>
            {/* Заголовок окна */}
            <div className="flex items-center gap-2 px-4 py-3" style={{ background: COLORS.card2, borderBottom: `1px solid ${COLORS.border}` }}>
              <div className="w-3 h-3 rounded-full" style={{ background: "#FF5F56" }} />
              <div className="w-3 h-3 rounded-full" style={{ background: "#FFBD2E" }} />
              <div className="w-3 h-3 rounded-full" style={{ background: "#27C93F" }} />
              <span className="ml-3 text-xs" style={{ color: COLORS.textDim }}>SodaShop — alexuser</span>
            </div>

            {/* Основной макет */}
            <div className="flex" style={{ minHeight: 540 }}>
              {/* Sidebar */}
              <div className="w-44 flex-shrink-0 flex flex-col" style={{ background: COLORS.card, borderRight: `1px solid ${COLORS.border}` }}>
                <div className="text-center py-5" style={{ borderBottom: `1px solid ${COLORS.border}` }}>
                  <div className="text-3xl">🥤</div>
                  <div className="text-sm font-bold" style={{ color: COLORS.text }}>SodaShop</div>
                </div>
                <nav className="flex-1 py-2">
                  {tabs.slice(0, 3).map((t) => (
                    <button
                      key={t.key}
                      className="w-full text-left px-4 py-3 text-sm transition-all"
                      style={{
                        background: activeTab === t.key ? COLORS.card2 : "transparent",
                        color: activeTab === t.key ? COLORS.accent : COLORS.text,
                      }}
                      onClick={() => setActiveTab(t.key)}
                    >
                      {t.label}
                    </button>
                  ))}
                </nav>
                <div className="p-4" style={{ borderTop: `1px solid ${COLORS.border}` }}>
                  <div className="text-xs font-bold" style={{ color: COLORS.text }}>👤 alexuser</div>
                  <div className="text-xs mt-1 cursor-pointer" style={{ color: COLORS.accent2 }}>Выйти</div>
                </div>
              </div>

              {/* Контент */}
              <div className="flex-1 overflow-auto">
                {activeTab === "auth"    && <AuthPreview mode={authMode} setMode={setAuthMode} />}
                {activeTab === "catalog" && <CatalogPreview />}
                {activeTab === "profile" && <ProfilePreview />}
              </div>
            </div>
          </div>

          {/* Кнопка запуска */}
          <div className="text-center mt-4">
            <button
              className="px-5 py-2 rounded-lg text-sm font-semibold transition-all hover:opacity-80"
              style={{ background: COLORS.card2, color: COLORS.textDim, border: `1px solid ${COLORS.border}` }}
              onClick={() => setActiveTab("code")}
            >
              📦 Инструкция по запуску →
            </button>
          </div>
        </div>

        {/* Инструкция по запуску */}
        <div id="setup" className="mb-12">
          <h2 className="text-2xl font-bold mb-6 text-center" style={{ color: COLORS.text }}>Как запустить 🚀</h2>
          <div className="space-y-4">
            {pythonSetup.map((s, i) => (
              <div key={i} className="rounded-xl overflow-hidden" style={{ background: COLORS.card, border: `1px solid ${COLORS.border}` }}>
                <div className="flex items-start gap-4 p-5">
                  <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0" style={{ background: COLORS.accent, color: "white" }}>
                    {s.step}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-semibold mb-1" style={{ color: COLORS.text }}>{s.title}</div>
                    <div className="text-xs mb-2" style={{ color: COLORS.textDim }}>{s.note}</div>
                    <pre className="rounded-lg p-3 text-xs overflow-x-auto" style={{ background: "#0a0a18", color: COLORS.accent3, border: `1px solid ${COLORS.border}`, fontFamily: "'Fira Code', 'Consolas', monospace" }}>
                      {s.cmd}
                    </pre>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Структура БД */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold mb-6 text-center" style={{ color: COLORS.text }}>Структура базы данных 🗄️</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              {
                table: "users",
                color: COLORS.accent,
                emoji: "👤",
                fields: [
                  { name: "id",         type: "SERIAL PK",      note: "Уникальный ID" },
                  { name: "username",   type: "VARCHAR(64)",     note: "Имя пользователя" },
                  { name: "email",      type: "VARCHAR(128)",    note: "Email (уникальный)" },
                  { name: "password",   type: "VARCHAR(128)",    note: "SHA-256 хеш пароля" },
                  { name: "created_at", type: "TIMESTAMP",       note: "Дата регистрации" },
                ],
              },
              {
                table: "brands",
                color: COLORS.accent3,
                emoji: "🏷️",
                fields: [
                  { name: "id",   type: "SERIAL PK",   note: "Уникальный ID" },
                  { name: "name", type: "VARCHAR(64)",  note: "Название бренда" },
                  { name: "logo", type: "VARCHAR(8)",   note: "Эмодзи бренда" },
                ],
              },
              {
                table: "drinks",
                color: COLORS.warning,
                emoji: "🥤",
                fields: [
                  { name: "id",        type: "SERIAL PK",    note: "Уникальный ID" },
                  { name: "brand_id",  type: "INTEGER FK",   note: "Ссылка на бренд" },
                  { name: "name",      type: "VARCHAR(128)",  note: "Название напитка" },
                  { name: "flavor",    type: "VARCHAR(128)",  note: "Вкус" },
                  { name: "volume_ml", type: "INTEGER",       note: "Объём в мл" },
                  { name: "price",     type: "NUMERIC(8,2)",  note: "Цена в рублях" },
                  { name: "emoji",     type: "VARCHAR(8)",    note: "Иконка" },
                  { name: "color",     type: "VARCHAR(16)",   note: "Цвет карточки" },
                ],
              },
              {
                table: "orders",
                color: COLORS.accent2,
                emoji: "📋",
                fields: [
                  { name: "id",          type: "SERIAL PK",     note: "Уникальный ID" },
                  { name: "user_id",     type: "INTEGER FK",    note: "Ссылка на пользователя" },
                  { name: "drink_id",    type: "INTEGER FK",    note: "Ссылка на напиток" },
                  { name: "quantity",    type: "INTEGER",        note: "Количество" },
                  { name: "total_price", type: "NUMERIC(10,2)", note: "Сумма заказа" },
                  { name: "ordered_at",  type: "TIMESTAMP",      note: "Дата заказа" },
                  { name: "status",      type: "VARCHAR(32)",    note: "Статус заказа" },
                ],
              },
            ].map((t) => (
              <div key={t.table} className="rounded-xl overflow-hidden" style={{ background: COLORS.card, border: `1px solid ${COLORS.border}` }}>
                <div className="flex items-center gap-2 px-4 py-3" style={{ background: COLORS.card2, borderBottom: `1px solid ${COLORS.border}` }}>
                  <span>{t.emoji}</span>
                  <span className="font-bold font-mono text-sm" style={{ color: t.color }}>{t.table}</span>
                </div>
                <div className="p-2">
                  {t.fields.map((f) => (
                    <div key={f.name} className="flex items-center gap-2 px-3 py-2 rounded-lg mb-1 text-xs" style={{ background: "rgba(0,0,0,0.2)" }}>
                      <span className="font-mono font-bold w-24 flex-shrink-0" style={{ color: t.color }}>{f.name}</span>
                      <span className="w-28 flex-shrink-0 font-mono" style={{ color: COLORS.accent3 }}>{f.type}</span>
                      <span style={{ color: COLORS.textDim }}>{f.note}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="text-center py-8" style={{ borderTop: `1px solid ${COLORS.border}`, color: COLORS.textDim }}>
          <div className="text-3xl mb-2">🥤</div>
          <div className="font-bold text-sm mb-1" style={{ color: COLORS.text }}>SodaShop Tkinter App</div>
          <div className="text-xs">Python • Tkinter • PostgreSQL • psycopg2</div>
          <div className="mt-3 text-xs">Файл приложения: <code className="px-2 py-0.5 rounded" style={{ background: COLORS.card2, color: COLORS.accent }}>app.py</code></div>
        </div>
      </div>
    </div>
  );
}
