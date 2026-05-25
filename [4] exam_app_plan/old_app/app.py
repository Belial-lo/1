from tkinter import *
from tkinter import messagebox
from pathlib import Path

import psycopg2
from PIL import Image, ImageTk


DB_CONFIG = {
    "host": "localhost",
    "database": "DB_Ivah",
    "user": "postgres",
    "password": "admin",
}

BASE_DIR = Path(__file__).parent


current_role = "guest"
current_full_name = "Гость"
tk = None
canvas = None
search_var = None
photo_images = []


def get_connection():
    return psycopg2.connect(**DB_CONFIG)


def fetch_all(sql, params=None):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or [])
            return cursor.fetchall()


def fetch_one(sql, params=None):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or [])
            return cursor.fetchone()


def execute(sql, params=None):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or [])
        conn.commit()


def show_login_window():
    global tk

    tk = Tk()
    tk.title("Авторизация")
    tk.geometry("430x430")
    tk.config(bg="#F8F8F8")

    login_var = StringVar()
    password_var = StringVar()

    frame = Frame(tk, bg="white", padx=30, pady=20)
    frame.pack(fill="both", expand=True, padx=35, pady=35)

    Label(frame, text="Вход", bg="white", font=("Arial", 18, "bold")).pack(anchor="w", pady=(0, 15))

    Label(frame, text="Логин:", bg="white").pack(anchor="w")
    Entry(frame, textvariable=login_var).pack(fill="x", pady=(3, 10), ipady=3)

    Label(frame, text="Пароль:", bg="white").pack(anchor="w")
    Entry(frame, textvariable=password_var, show="*").pack(fill="x", pady=(3, 15), ipady=3)

    Button(frame, text="Войти", bg="#B4E2AC", command=lambda: login(login_var, password_var)).pack(fill="x", ipady=7)
    Button(frame, text="Войти как гость", bg="#C2C2C2", command=login_as_guest).pack(fill="x", pady=(8, 0), ipady=7)

    tk.mainloop()


def login(login_var, password_var):
    global current_full_name

    login_text = login_var.get().strip()
    password_text = password_var.get().strip()

    user = fetch_one("""
        SELECT users.login, roles.name, users.full_name
        FROM users
        JOIN roles ON users.role_id = roles.id
        WHERE users.login=%s AND users.password=%s
        """, [login_text, password_text])

    if user is None:
        messagebox.showerror("Ошибка", "Неверный логин или пароль.")
        return

    current_full_name = user[2]
    open_main_window(user[1])


def login_as_guest():
    global current_full_name

    current_full_name = "Гость"
    open_main_window("guest")


def open_main_window(role):
    global current_role

    current_role = role
    tk.destroy()
    show_main_window()


def show_main_window():
    global tk, canvas, search_var

    tk = Tk()
    tk.title("Товары")
    tk.geometry("900x650")
    tk.config(bg="#F8F8F8")

    search_var = StringVar()

    header = Frame(tk, bg="#D4E09B", padx=15, pady=12)
    header.pack(fill="x")

    Label(header, text="Список товаров", bg="#D4E09B", font=("Arial", 18, "bold")).pack(side="left")
    Label(header, text=f"{current_full_name} | {current_role}", bg="#D4E09B").pack(side="right")

    tools = Frame(tk, bg="#F8F8F8", padx=15, pady=10)
    tools.pack(fill="x")

    Label(tools, text="Поиск:", bg="#F8F8F8").pack(side="left")
    Entry(tools, textvariable=search_var, width=30).pack(side="left", padx=(5, 10))
    add_role_buttons(tools)

    canvas = Canvas(tk, bg="#F8F8F8", highlightthickness=0)
    scrollbar = Scrollbar(tk, orient="vertical", command=canvas.yview)
    cards_frame = Frame(canvas, bg="#F8F8F8")

    window_id = canvas.create_window((0, 0), window=cards_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True, padx=(15, 0), pady=(0, 15))
    scrollbar.pack(side="right", fill="y", padx=(0, 15), pady=(0, 15))

    cards_frame.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window_id, width=event.width))

    search_var.trace_add("write", lambda *args: load_products(cards_frame))

    load_products(cards_frame)
    tk.mainloop()


def add_role_buttons(parent):
    if current_role == "admin":
        Button(parent, text="Добавить", bg="#D4E09B").pack(side="right")
        Button(parent, text="Редактировать", bg="#D4E09B").pack(side="right", padx=(0, 8))
        Button(parent, text="Удалить", bg="#F2B8B5").pack(side="right", padx=(0, 8))
    elif current_role == "manager":
        Button(parent, text="Заказы", bg="#D4E09B").pack(side="right")
    elif current_role == "client":
        Button(parent, text="Корзина", bg="#D4E09B").pack(side="right")


def load_products(cards_frame):
    global photo_images

    photo_images = []

    for widget in cards_frame.winfo_children():
        widget.destroy()

    search = search_var.get().strip()

    if search:
        rows = fetch_all("""
            SELECT id_p, article_num, product, unit, price, supplier, creator,
                   category, discount, inventory, description, photo
            FROM products
            WHERE product ILIKE %s OR category ILIKE %s OR supplier ILIKE %s
            ORDER BY id_p
            """, [f"%{search}%", f"%{search}%", f"%{search}%"])
    else:
        rows = fetch_all("""
            SELECT id_p, article_num, product, unit, price, supplier, creator,
                   category, discount, inventory, description, photo
            FROM products
            ORDER BY id_p
            """)

    for row in rows:
        create_product_card(cards_frame, row)


def create_product_card(cards_frame, row):
    article_num = row[1]
    product = row[2]
    unit = row[3]
    price = row[4]
    supplier = row[5]
    creator = row[6]
    category = row[7]
    discount = row[8]
    inventory = row[9]
    description = row[10]
    photo = row[11]

    bg = "white"
    if inventory == 0:
        bg = "#BFD7EA"
    elif discount > 15:
        bg = "#2E8B57"

    fg = "white" if bg == "#2E8B57" else "#333333"

    card = Frame(cards_frame, bg=bg, padx=10, pady=10, highlightthickness=2, highlightbackground="#333333")
    card.pack(fill="x", pady=6)

    photo_frame = Frame(card, bg=bg, width=140, height=110, highlightthickness=1, highlightbackground="#333333")
    photo_frame.grid(row=0, column=0, padx=(0, 10), sticky="ns")
    photo_frame.grid_propagate(False)

    info_frame = Frame(card, bg=bg)
    info_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 10))

    show_photo(photo_frame, photo, bg, fg)

    Label(info_frame, text=f"{category} | {product}", bg=bg, fg=fg, font=("Arial", 13, "bold"), anchor="w").pack(fill="x")
    Label(info_frame, text=f"Артикул: {article_num}", bg=bg, fg=fg, anchor="w").pack(fill="x")
    Label(info_frame, text=f"Описание: {description}", bg=bg, fg=fg, anchor="w").pack(fill="x")
    Label(info_frame, text=f"Производитель: {creator}", bg=bg, fg=fg, anchor="w").pack(fill="x")
    Label(info_frame, text=f"Поставщик: {supplier}", bg=bg, fg=fg, anchor="w").pack(fill="x")
    Label(info_frame, text=f"Цена: {price} руб.", bg=bg, fg=fg, anchor="w").pack(fill="x")
    Label(info_frame, text=f"Единица: {unit}", bg=bg, fg=fg, anchor="w").pack(fill="x")
    Label(info_frame, text=f"Остаток: {inventory}", bg=bg, fg=fg, anchor="w").pack(fill="x")

    discount_frame = Frame(card, bg=bg, width=120, height=110, highlightthickness=1, highlightbackground="#333333")
    discount_frame.grid(row=0, column=2, sticky="ns")
    discount_frame.grid_propagate(False)
    Label(discount_frame, text=f"Скидка\n{discount}%", bg=bg, fg=fg, font=("Arial", 12, "bold")).place(relx=0.5, rely=0.5, anchor="center")

    card.columnconfigure(1, weight=1)


def show_photo(parent, photo, bg, fg):
    if photo:
        path = BASE_DIR / photo
    else:
        path = BASE_DIR / "image/picture.png"

    try:
        image = Image.open(path)
        image.thumbnail((120, 90))
        tk_image = ImageTk.PhotoImage(image)
        photo_images.append(tk_image)
        Label(parent, image=tk_image, bg=bg).place(relx=0.5, rely=0.5, anchor="center")
    except Exception:
        Label(parent, text="Фото\nнет", bg=bg, fg=fg).place(relx=0.5, rely=0.5, anchor="center")


show_login_window()
