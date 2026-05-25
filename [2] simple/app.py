from tkinter import *
from tkinter import messagebox
from pathlib import Path

import psycopg2
from PIL import Image, ImageTk


BASE_DIR = Path(__file__).parent

DB_CONFIG = {
    "host": "localhost",
    "database": "DB_Ivah",
    "user": "postgres",
    "password": "admin",
}


current_role = "guest"
current_full_name = "Гость"
selected_product_id = None
root = None
cards_frame = None
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


def prepare_database():
    execute("ALTER TABLE products ADD COLUMN IF NOT EXISTS photo VARCHAR(255) NOT NULL DEFAULT ''")


def show_login_window():
    global root

    root = Tk()
    root.title("Авторизация")
    root.geometry("430x430")
    root.config(bg="#F8F8F8")

    login_var = StringVar()
    password_var = StringVar()

    frame = Frame(root, bg="white", padx=25, pady=22)
    frame.pack(fill="both", expand=True, padx=35, pady=35)

    Label(frame, text="Вход", bg="white", font=("Arial", 18, "bold")).pack(anchor="w", pady=(0, 15))

    Label(frame, text="Логин", bg="white").pack(anchor="w")
    Entry(frame, textvariable=login_var).pack(fill="x", pady=(3, 10), ipady=3)

    Label(frame, text="Пароль", bg="white").pack(anchor="w")
    Entry(frame, textvariable=password_var, show="*").pack(fill="x", pady=(3, 15), ipady=3)

    Button(frame, text="Войти", command=lambda: login(login_var, password_var), bg="#D4E09B").pack(fill="x", ipady=7)
    Button(frame, text="Войти как гость", command=login_as_guest, bg="#C2C2C2").pack(fill="x", pady=(8, 0), ipady=7)

    root.mainloop()


def login(login_var, password_var):
    global current_full_name

    login_text = login_var.get().strip()
    password_text = password_var.get().strip()

    if login_text == "" or password_text == "":
        messagebox.showwarning("Внимание", "Введите логин и пароль.")
        return

    user = fetch_one(
        """
        SELECT users.login, roles.name, users.full_name
        FROM users
        JOIN roles ON users.role_id = roles.id
        WHERE users.login=%s AND users.password=%s
        """,
        [login_text, password_text],
    )

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
    root.destroy()
    show_main_window()


def show_main_window():
    global root, cards_frame, canvas, search_var

    root = Tk()
    root.title("Товары")
    root.geometry("900x650")
    root.config(bg="#F8F8F8")

    search_var = StringVar()

    header = Frame(root, bg="#D4E09B", padx=15, pady=12)
    header.pack(fill="x")

    Label(header, text="Список товаров", bg="#D4E09B", font=("Arial", 18, "bold")).pack(side="left")
    Label(header, text=f"{current_full_name} | {current_role}", bg="#D4E09B").pack(side="right")

    tools = Frame(root, bg="#F8F8F8", padx=15, pady=10)
    tools.pack(fill="x")

    Label(tools, text="Поиск:", bg="#F8F8F8").pack(side="left")
    Entry(tools, textvariable=search_var, width=30).pack(side="left", padx=(5, 10))

    if current_role == "admin":
        Button(tools, text="Добавить товар", command=open_add_window, bg="#D4E09B").pack(side="right")
        Button(tools, text="Удалить", command=delete_product, bg="#F2B8B5").pack(side="right", padx=(0, 10))

    search_var.trace_add("write", lambda *args: load_products())

    canvas = Canvas(root, bg="#F8F8F8", highlightthickness=0)
    scrollbar = Scrollbar(root, orient="vertical", command=canvas.yview)
    cards_frame = Frame(canvas, bg="#F8F8F8")

    window_id = canvas.create_window((0, 0), window=cards_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True, padx=(15, 0), pady=(0, 15))
    scrollbar.pack(side="right", fill="y", padx=(0, 15), pady=(0, 15))

    cards_frame.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window_id, width=event.width))
    canvas.bind_all("<MouseWheel>", on_mousewheel)

    load_products()
    root.mainloop()


def on_mousewheel(event):
    if event.delta > 0:
        canvas.yview_scroll(-1, "units")
    else:
        canvas.yview_scroll(1, "units")


def load_products():
    global photo_images

    photo_images = []

    for widget in cards_frame.winfo_children():
        widget.destroy()

    search = search_var.get().strip()

    if search:
        rows = fetch_all(
            """
            SELECT id_p, article_num, product, unit, price, supplier, creator,
                   category, discount, inventory, description, photo
            FROM products
            WHERE product ILIKE %s OR category ILIKE %s OR supplier ILIKE %s
            ORDER BY id_p
            """,
            [f"%{search}%", f"%{search}%", f"%{search}%"],
        )
    else:
        rows = fetch_all(
            """
            SELECT id_p, article_num, product, unit, price, supplier, creator,
                   category, discount, inventory, description, photo
            FROM products
            ORDER BY id_p
            """
        )

    for row in rows:
        create_product_card(row)


def create_product_card(row):
    global selected_product_id

    product_id = row[0]
    article_num = row[1]
    product_name = row[2]
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

    card = Frame(cards_frame, bg=bg, padx=8, pady=8, highlightthickness=2, highlightbackground="#333333")
    card.pack(fill="x", pady=6)

    photo_frame = Frame(card, bg=bg, width=170, height=125, highlightthickness=2, highlightbackground="#333333")
    photo_frame.grid(row=0, column=0, sticky="ns", padx=(0, 8))
    photo_frame.grid_propagate(False)
    show_photo(photo_frame, photo, bg, fg)

    info_frame = Frame(card, bg=bg, padx=10, pady=6, highlightthickness=2, highlightbackground="#333333")
    info_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 8))

    Label(info_frame, text=f"{category} | {product_name}", bg=bg, fg=fg, font=("Arial", 13, "bold"), anchor="w").pack(fill="x")
    Label(info_frame, text=f"Артикул: {article_num}", bg=bg, fg=fg, anchor="w").pack(fill="x")
    Label(info_frame, text=f"Описание товара: {description}", bg=bg, fg=fg, anchor="w").pack(fill="x")
    Label(info_frame, text=f"Производитель: {creator}", bg=bg, fg=fg, anchor="w").pack(fill="x")
    Label(info_frame, text=f"Поставщик: {supplier}", bg=bg, fg=fg, anchor="w").pack(fill="x")
    Label(info_frame, text=f"Цена: {price} руб.", bg=bg, fg=fg, anchor="w").pack(fill="x")
    Label(info_frame, text=f"Единица измерения: {unit}", bg=bg, fg=fg, anchor="w").pack(fill="x")
    Label(info_frame, text=f"Количество на складе: {inventory}", bg=bg, fg=fg, anchor="w").pack(fill="x")

    if current_role == "admin":
        Button(info_frame, text="Редактировать", command=lambda: open_edit_window(product_id), bg="#D4E09B").pack(anchor="e", pady=(5, 0))

    discount_frame = Frame(card, bg=bg, width=130, height=125, highlightthickness=2, highlightbackground="#333333")
    discount_frame.grid(row=0, column=2, sticky="ns")
    discount_frame.grid_propagate(False)
    Label(discount_frame, text=f"Действующая\nскидка\n{discount}%", bg=bg, fg=fg, font=("Arial", 10, "bold")).place(relx=0.5, rely=0.5, anchor="center")

    card.columnconfigure(1, weight=1)
    bind_card_click(card, product_id, card)


def show_photo(parent, photo_path, bg, fg):
    if photo_path:
        path = Path(photo_path)
    else:
        path = Path("image/picture.png")

    if not path.is_absolute():
        path = BASE_DIR / path

    try:
        image = Image.open(path)
        image.thumbnail((150, 110))
        tk_image = ImageTk.PhotoImage(image)
        photo_images.append(tk_image)
        Label(parent, image=tk_image, bg=bg).place(relx=0.5, rely=0.5, anchor="center")
        return
    except Exception:
        Label(parent, text="Фото\nне открыто", bg=bg, fg=fg, font=("Arial", 11, "bold")).place(relx=0.5, rely=0.5, anchor="center")


def bind_card_click(widget, product_id, card):
    widget.bind("<Button-1>", lambda event: select_product(product_id, card))
    for child in widget.winfo_children():
        bind_card_click(child, product_id, card)


def select_product(product_id, selected_card):
    global selected_product_id

    selected_product_id = product_id

    for card in cards_frame.winfo_children():
        card.config(highlightbackground="#333333", highlightthickness=2)

    selected_card.config(highlightbackground="#00FA9A", highlightthickness=3)


def open_add_window():
    open_product_form()


def open_edit_window(product_id):
    open_product_form(product_id)


def open_product_form(product_id=None):
    window = Toplevel(root)
    window.title("Товар")
    window.geometry("540x620")
    window.minsize(480, 500)
    window.config(bg="#F8F8F8")

    product_var = StringVar()
    article_var = StringVar()
    category_var = StringVar()
    description_var = StringVar()
    creator_var = StringVar()
    supplier_var = StringVar()
    price_var = StringVar()
    unit_var = StringVar(value="шт")
    inventory_var = StringVar(value="0")
    discount_var = StringVar(value="0")
    photo_var = StringVar()

    canvas_form = Canvas(window, bg="#F8F8F8", highlightthickness=0)
    scrollbar_form = Scrollbar(window, orient="vertical", command=canvas_form.yview)
    frame = Frame(canvas_form, bg="white", padx=18, pady=18)

    window_id = canvas_form.create_window((0, 0), window=frame, anchor="nw")
    canvas_form.configure(yscrollcommand=scrollbar_form.set)
    canvas_form.pack(side="left", fill="both", expand=True, padx=(20, 0), pady=20)
    scrollbar_form.pack(side="right", fill="y", padx=(0, 20), pady=20)

    frame.bind("<Configure>", lambda event: canvas_form.configure(scrollregion=canvas_form.bbox("all")))
    canvas_form.bind("<Configure>", lambda event: canvas_form.itemconfigure(window_id, width=event.width))

    def scroll_form(event):
        canvas_form.yview_scroll(-1 if event.delta > 0 else 1, "units")

    def form_scroll_on(event=None):
        window.bind_all("<MouseWheel>", scroll_form)

    def form_scroll_off(event=None):
        window.unbind_all("<MouseWheel>")
        root.bind_all("<MouseWheel>", on_mousewheel)

    window.bind("<Enter>", form_scroll_on)
    window.bind("<Leave>", form_scroll_off)
    window.bind("<Destroy>", lambda event: form_scroll_off() if event.widget == window else None)

    add_entry(frame, "Артикул", article_var)
    add_entry(frame, "Наименование", product_var)
    add_entry(frame, "Категория", category_var)
    add_entry(frame, "Описание", description_var)
    add_entry(frame, "Производитель", creator_var)
    add_entry(frame, "Поставщик", supplier_var)
    add_entry(frame, "Цена", price_var)
    add_entry(frame, "Единица измерения", unit_var)
    add_entry(frame, "Количество на складе", inventory_var)
    add_entry(frame, "Скидка", discount_var)
    add_entry(frame, "Фото", photo_var)

    if product_id is not None:
        row = fetch_one(
            """
            SELECT article_num, product, unit, price, supplier, creator,
                   category, discount, inventory, description, photo
            FROM products
            WHERE id_p=%s
            """,
            [product_id],
        )
        article_var.set(row[0])
        product_var.set(row[1])
        unit_var.set(row[2])
        price_var.set(str(row[3]))
        supplier_var.set(row[4])
        creator_var.set(row[5])
        category_var.set(row[6])
        discount_var.set(str(row[7]))
        inventory_var.set(str(row[8]))
        description_var.set(row[9])
        photo_var.set(row[10] or "")

    Button(
        frame,
        text="Сохранить",
        command=lambda: save_product(
            window,
            product_id,
            article_var,
            product_var,
            category_var,
            description_var,
            creator_var,
            supplier_var,
            price_var,
            unit_var,
            inventory_var,
            discount_var,
            photo_var,
        ),
        bg="#D4E09B",
    ).pack(fill="x", pady=(5, 0), ipady=7)


def add_entry(parent, text, variable):
    Label(parent, text=text, bg="white").pack(anchor="w")
    Entry(parent, textvariable=variable).pack(fill="x", pady=(2, 5), ipady=2)


def save_product(window, product_id, article_var, product_var, category_var, description_var, creator_var, supplier_var, price_var, unit_var, inventory_var, discount_var, photo_var):
    article_num = article_var.get().strip()
    product = product_var.get().strip()
    category = category_var.get().strip()
    description = description_var.get().strip()
    creator = creator_var.get().strip()
    supplier = supplier_var.get().strip()
    unit = unit_var.get().strip()
    photo = photo_var.get().strip()

    try:
        price = float(price_var.get().replace(",", "."))
        inventory = int(inventory_var.get())
        discount = int(discount_var.get())
    except ValueError:
        messagebox.showerror("Ошибка", "Цена, количество и скидка должны быть числами.")
        return

    if article_num == "" or product == "" or category == "" or creator == "" or supplier == "":
        messagebox.showwarning("Внимание", "Заполните все обязательные поля.")
        return

    if product_id is None:
        execute(
            """
            INSERT INTO products (
                article_num, product, unit, price, supplier, creator,
                category, discount, inventory, description, photo
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [article_num, product, unit, price, supplier, creator, category, discount, inventory, description, photo],
        )
    else:
        execute(
            """
            UPDATE products
            SET article_num=%s, product=%s, unit=%s, price=%s, supplier=%s,
                creator=%s, category=%s, discount=%s, inventory=%s, description=%s, photo=%s
            WHERE id_p=%s
            """,
            [article_num, product, unit, price, supplier, creator, category, discount, inventory, description, photo, product_id],
        )

    load_products()
    window.destroy()
    messagebox.showinfo("Готово", "Товар сохранен.")


def delete_product():
    if selected_product_id is None:
        messagebox.showwarning("Внимание", "Выберите товар.")
        return

    if not messagebox.askyesno("Удаление", "Удалить выбранный товар?"):
        return

    execute("DELETE FROM products WHERE id_p=%s", [selected_product_id])
    load_products()


prepare_database()
show_login_window()
