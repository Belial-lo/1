import hashlib
from pathlib import Path
from tkinter import messagebox, ttk
import tkinter as tk

import psycopg2
from PIL import Image, ImageTk
from psycopg2.extras import RealDictCursor


DB_CONFIG = {
    "host": "localhost",
    "database": "DB_p",
    "user": "postgres",
    "password": "admin",
}

APP_DIR = Path(__file__).resolve().parent
IMAGE_DIR = APP_DIR / "image"

COLORS = {
    "bg": "#F8F8F8",
    "panel": "#FFFFFF",
    "accent": "#D4E09B",
    "secondary": "#C2C2C2",
    "text": "#333333",
    "muted": "#666666",
    "danger": "#F2B8B5",
    "discount": "#2E8B57",
    "empty": "#BFD7EA",
}


def get_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)


def hash_password(password):
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


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


def money(value):
    return f"{float(value):.2f} руб."


class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.auth_user = None
        self.title("Авторизация")
        self.geometry("440x450")
        self.minsize(440, 450)
        self.resizable(False, False)
        self.configure(bg=COLORS["bg"])

        self.login_var = tk.StringVar()
        self.password_var = tk.StringVar()

        self.build_ui()

    def build_ui(self):
        card = tk.Frame(self, bg=COLORS["panel"], padx=28, pady=24)
        card.pack(fill="both", expand=True, padx=36, pady=34)

        tk.Label(
            card,
            text="Вход в систему",
            bg=COLORS["panel"],
            fg=COLORS["text"],
            font=("Arial", 18, "bold"),
        ).pack(anchor="w", pady=(0, 18))

        tk.Label(card, text="Логин", bg=COLORS["panel"], fg=COLORS["text"]).pack(anchor="w")
        tk.Entry(card, textvariable=self.login_var, font=("Arial", 11)).pack(fill="x", pady=(4, 12), ipady=4)

        tk.Label(card, text="Пароль", bg=COLORS["panel"], fg=COLORS["text"]).pack(anchor="w")
        tk.Entry(card, textvariable=self.password_var, show="*", font=("Arial", 11)).pack(fill="x", pady=(4, 18), ipady=4)

        tk.Button(
            card,
            text="Войти",
            command=self.login,
            bg=COLORS["accent"],
            fg=COLORS["text"],
            activebackground=COLORS["accent"],
            relief="flat",
            font=("Arial", 11, "bold"),
        ).pack(fill="x", pady=(4, 0), ipady=7)

        tk.Button(
            card,
            text="Войти как гость",
            command=self.login_as_guest,
            bg=COLORS["secondary"],
            fg=COLORS["text"],
            activebackground=COLORS["secondary"],
            relief="flat",
            font=("Arial", 11),
        ).pack(fill="x", pady=(8, 0), ipady=7)

    def login(self):
        login = self.login_var.get().strip()
        password = self.password_var.get().strip()

        if not login or not password:
            messagebox.showwarning("Проверка данных", "Введите логин и пароль.")
            return

        user = fetch_one(
            """
            SELECT u.full_name, r.name AS role_name
            FROM users u
            JOIN roles r ON r.id = u.role_id
            WHERE u.login = %s AND u.password_hash = %s
            """,
            [login, hash_password(password)],
        )

        if user is None:
            messagebox.showerror("Ошибка входа", "Неверный логин или пароль.")
            return

        self.auth_user = (user["role_name"], user["full_name"])
        self.destroy()

    def login_as_guest(self):
        self.auth_user = ("guest", "Гость")
        self.destroy()


class ProductsWindow(tk.Tk):
    def __init__(self, role_name, full_name):
        super().__init__()
        self.role_name = role_name
        self.full_name = full_name
        self.selected_product_id = None
        self.product_cards = {}
        self.images = []

        self.search_var = tk.StringVar()
        self.supplier_var = tk.StringVar(value="Все поставщики")
        self.sort_var = tk.StringVar(value="Без сортировки")

        self.title("Товары")
        self.geometry("1180x760")
        self.minsize(980, 620)
        self.configure(bg=COLORS["bg"])
        self.protocol("WM_DELETE_WINDOW", self.logout)

        self.build_ui()
        self.load_suppliers()
        self.load_products()

    def build_ui(self):
        header = tk.Frame(self, bg=COLORS["accent"], padx=18, pady=14)
        header.pack(fill="x")

        tk.Label(
            header,
            text="Список товаров",
            bg=COLORS["accent"],
            fg=COLORS["text"],
            font=("Arial", 18, "bold"),
        ).pack(side="left")

        tk.Label(
            header,
            text=f"{self.full_name} ({self.role_name})",
            bg=COLORS["accent"],
            fg=COLORS["text"],
            font=("Arial", 10),
        ).pack(side="left", padx=(20, 0))

        tk.Button(header, text="Выход", command=self.logout, bg=COLORS["panel"], relief="flat").pack(side="right")

        tools = tk.Frame(self, bg=COLORS["bg"], padx=18, pady=12)
        tools.pack(fill="x")

        if self.role_name in ("manager", "admin"):
            tk.Label(tools, text="Поиск", bg=COLORS["bg"], fg=COLORS["text"]).pack(side="left")
            search = tk.Entry(tools, textvariable=self.search_var, width=26)
            search.pack(side="left", padx=(6, 14), ipady=3)
            search.bind("<KeyRelease>", lambda event: self.load_products())

            tk.Label(tools, text="Поставщик", bg=COLORS["bg"], fg=COLORS["text"]).pack(side="left")
            self.supplier_combo = ttk.Combobox(tools, textvariable=self.supplier_var, state="readonly", width=20)
            self.supplier_combo.pack(side="left", padx=(6, 14))
            self.supplier_combo.bind("<<ComboboxSelected>>", lambda event: self.load_products())

            tk.Label(tools, text="Сортировка", bg=COLORS["bg"], fg=COLORS["text"]).pack(side="left")
            self.sort_combo = ttk.Combobox(
                tools,
                textvariable=self.sort_var,
                state="readonly",
                width=22,
                values=["Без сортировки", "Количество по возрастанию", "Количество по убыванию"],
            )
            self.sort_combo.pack(side="left", padx=(6, 14))
            self.sort_combo.bind("<<ComboboxSelected>>", lambda event: self.load_products())

        if self.role_name == "admin":
            tk.Button(
                tools,
                text="Добавить товар",
                command=self.add_product,
                bg=COLORS["accent"],
                relief="flat",
                padx=14,
            ).pack(side="right")

            tk.Button(
                tools,
                text="Удалить",
                command=self.delete_product,
                bg=COLORS["danger"],
                relief="flat",
                padx=14,
            ).pack(side="right", padx=(0, 10))

        self.canvas = tk.Canvas(self, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.cards_frame = tk.Frame(self.canvas, bg=COLORS["bg"])

        self.window_id = self.canvas.create_window((0, 0), window=self.cards_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True, padx=(18, 0), pady=(0, 18))
        scrollbar.pack(side="right", fill="y", padx=(0, 18), pady=(0, 18))

        self.cards_frame.bind("<Configure>", lambda event: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda event: self.canvas.itemconfigure(self.window_id, width=event.width))
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)
        self.canvas.bind_all("<Button-4>", self.on_mousewheel)
        self.canvas.bind_all("<Button-5>", self.on_mousewheel)

    def on_mousewheel(self, event):
        if getattr(event, "num", None) == 4 or getattr(event, "delta", 0) > 0:
            self.canvas.yview_scroll(-1, "units")
        else:
            self.canvas.yview_scroll(1, "units")

    def load_suppliers(self):
        if self.role_name not in ("manager", "admin"):
            return

        rows = fetch_all("SELECT DISTINCT supplier FROM products ORDER BY supplier")
        self.supplier_combo["values"] = ["Все поставщики"] + [row["supplier"] for row in rows]

    def load_products(self):
        self.selected_product_id = None
        self.product_cards.clear()
        self.images.clear()

        for widget in self.cards_frame.winfo_children():
            widget.destroy()

        sql = """
            SELECT
                id, article, name, category, description, manufacturer, supplier,
                price, discount, unit, stock_quantity, image_path,
                ROUND(price * (100 - discount) / 100, 2) AS final_price
            FROM products
        """
        conditions = []
        params = []

        if self.role_name in ("manager", "admin"):
            search_text = self.search_var.get().strip()
            if search_text:
                conditions.append(
                    """
                    (
                        article ILIKE %s OR name ILIKE %s OR category ILIKE %s OR
                        description ILIKE %s OR manufacturer ILIKE %s OR supplier ILIKE %s
                    )
                    """
                )
                params.extend([f"%{search_text}%"] * 6)

            supplier = self.supplier_var.get()
            if supplier and supplier != "Все поставщики":
                conditions.append("supplier = %s")
                params.append(supplier)

        if conditions:
            sql += " WHERE " + " AND ".join(conditions)

        if self.sort_var.get() == "Количество по возрастанию":
            sql += " ORDER BY stock_quantity ASC, id"
        elif self.sort_var.get() == "Количество по убыванию":
            sql += " ORDER BY stock_quantity DESC, id"
        else:
            sql += " ORDER BY id"

        try:
            products = fetch_all(sql, params)
        except Exception as error:
            messagebox.showerror("Ошибка базы данных", f"Не удалось загрузить товары.\n{error}")
            return

        if not products:
            tk.Label(
                self.cards_frame,
                text="Товары не найдены",
                bg=COLORS["bg"],
                fg=COLORS["muted"],
                font=("Arial", 14),
            ).pack(pady=30)
            return

        for product in products:
            self.create_card(product)

    def create_card(self, product):
        bg = COLORS["panel"]
        if product["stock_quantity"] == 0:
            bg = COLORS["empty"]
        elif product["discount"] > 15:
            bg = COLORS["discount"]

        fg = "white" if bg == COLORS["discount"] else COLORS["text"]

        card = tk.Frame(self.cards_frame, bg=bg, padx=8, pady=8, highlightthickness=2, highlightbackground=COLORS["text"])
        card.pack(fill="x", padx=2, pady=6)
        self.product_cards[product["id"]] = card

        photo_frame = tk.Frame(card, bg=bg, width=210, height=150, highlightthickness=2, highlightbackground=COLORS["text"])
        photo_frame.grid(row=0, column=0, sticky="ns", padx=(0, 8))
        photo_frame.grid_propagate(False)

        image_path = self.resolve_image_path(product["image_path"])
        is_placeholder = image_path is None or not image_path.exists()
        image = self.load_product_image(product["image_path"])
        image_label = tk.Label(
            photo_frame,
            image=image,
            text="Фото" if is_placeholder else "",
            compound="center",
            bg=bg,
            fg=fg,
            font=("Arial", 12, "bold"),
        )
        image_label.image = image
        image_label.place(relx=0.5, rely=0.5, anchor="center")

        info_frame = tk.Frame(card, bg=bg, padx=12, pady=6, highlightthickness=2, highlightbackground=COLORS["text"])
        info_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 8))

        title = f"{product['category']} | {product['name']}"
        tk.Label(info_frame, text=title, bg=bg, fg=fg, font=("Arial", 13, "bold"), anchor="w").pack(fill="x")

        info_lines = (
            f"Описание товара: {product['description']}",
            f"Производитель: {product['manufacturer']}",
            f"Поставщик: {product['supplier']}",
            f"Цена: {money(product['price'])}",
            f"Единица измерения: {product['unit']}",
            f"Количество на складе: {product['stock_quantity']}",
        )
        for line in info_lines:
            tk.Label(info_frame, text=line, bg=bg, fg=fg, anchor="w", justify="left").pack(fill="x")

        if self.role_name == "admin":
            tk.Button(
                info_frame,
                text="Редактировать",
                command=lambda product_id=product["id"]: self.edit_product(product_id),
                bg=COLORS["accent"],
                relief="flat",
                padx=12,
            ).pack(anchor="e", pady=(5, 0))

        discount_frame = tk.Frame(card, bg=bg, width=150, height=150, highlightthickness=2, highlightbackground=COLORS["text"])
        discount_frame.grid(row=0, column=2, sticky="ns")
        discount_frame.grid_propagate(False)

        tk.Label(
            discount_frame,
            text=f"Действующая\nскидка\n{product['discount']}%",
            bg=bg,
            fg=fg,
            font=("Arial", 11, "bold"),
            justify="center",
        ).place(relx=0.5, rely=0.5, anchor="center")

        card.columnconfigure(1, weight=1)
        self.bind_card_click(card, product["id"])

    def bind_card_click(self, widget, product_id):
        widget.bind("<Button-1>", lambda event: self.select_product(product_id))
        for child in widget.winfo_children():
            self.bind_card_click(child, product_id)

    def resolve_image_path(self, image_path):
        if not image_path:
            return IMAGE_DIR / "picture.png"

        path = Path(image_path)
        if image_path and not path.is_absolute():
            path = APP_DIR / image_path
        return path

    def load_product_image(self, image_path):
        path = self.resolve_image_path(image_path)
        try:
            image = Image.open(path)
            image.thumbnail((120, 90))
            image = ImageTk.PhotoImage(image)
        except Exception:
            image = tk.PhotoImage(width=120, height=90)
            image.put("#EDEDED", to=(0, 0, 120, 90))
            image.put("#C2C2C2", to=(8, 8, 112, 82))

        self.images.append(image)
        return image

    def select_product(self, product_id):
        self.selected_product_id = product_id
        for current_id, card in self.product_cards.items():
            card.configure(highlightthickness=2 if current_id == product_id else 1)
            card.configure(highlightbackground="#333333" if current_id == product_id else COLORS["secondary"])

    def add_product(self):
        ProductForm(self)

    def edit_product(self, product_id=None):
        product_id = product_id or self.selected_product_id
        if product_id is None:
            messagebox.showwarning("Выбор товара", "Выберите товар для редактирования.")
            return
        ProductForm(self, product_id)

    def delete_product(self):
        if self.selected_product_id is None:
            messagebox.showwarning("Выбор товара", "Выберите товар для удаления.")
            return

        if not messagebox.askyesno("Удаление", "Удалить выбранный товар?"):
            return

        try:
            execute("DELETE FROM products WHERE id = %s", [self.selected_product_id])
        except Exception as error:
            messagebox.showerror("Ошибка удаления", f"Не удалось удалить товар.\n{error}")
            return

        self.load_products()

    def logout(self):
        self.destroy()


class ProductForm(tk.Toplevel):
    def __init__(self, parent, product_id=None):
        super().__init__(parent)
        self.parent = parent
        self.product_id = product_id

        self.vars = {
            "article": tk.StringVar(),
            "name": tk.StringVar(),
            "category": tk.StringVar(),
            "description": tk.StringVar(),
            "manufacturer": tk.StringVar(),
            "supplier": tk.StringVar(),
            "price": tk.StringVar(),
            "discount": tk.StringVar(value="0"),
            "unit": tk.StringVar(value="шт"),
            "stock_quantity": tk.StringVar(value="0"),
            "image_path": tk.StringVar(),
        }

        self.title("Редактирование товара" if product_id else "Добавление товара")
        self.geometry("560x760")
        self.minsize(520, 620)
        self.configure(bg=COLORS["bg"])

        self.build_ui()
        if product_id:
            self.load_product()

    def build_ui(self):
        container = tk.Frame(self, bg=COLORS["bg"])
        container.pack(fill="both", expand=True, padx=18, pady=18)

        canvas = tk.Canvas(container, bg=COLORS["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        frame = tk.Frame(canvas, bg=COLORS["panel"], padx=18, pady=16)

        window_id = canvas.create_window((0, 0), window=frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        frame.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window_id, width=event.width))

        def scroll_form(event):
            canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")

        canvas.bind("<MouseWheel>", scroll_form)
        frame.bind("<MouseWheel>", scroll_form)

        title = "Редактирование товара" if self.product_id else "Добавление товара"
        tk.Label(frame, text=title, bg=COLORS["panel"], fg=COLORS["text"], font=("Arial", 16, "bold")).pack(anchor="w", pady=(0, 12))

        for field, label in (
            ("article", "Артикул"),
            ("name", "Наименование"),
            ("category", "Категория"),
            ("description", "Описание"),
            ("manufacturer", "Производитель"),
            ("supplier", "Поставщик"),
            ("price", "Цена"),
            ("discount", "Скидка"),
            ("unit", "Единица измерения"),
            ("stock_quantity", "Количество на складе"),
            ("image_path", "Фото"),
        ):
            tk.Label(frame, text=label, bg=COLORS["panel"], fg=COLORS["text"]).pack(anchor="w")
            tk.Entry(frame, textvariable=self.vars[field]).pack(fill="x", pady=(3, 8), ipady=3)

        tk.Button(frame, text="Сохранить", command=self.save, bg=COLORS["accent"], relief="flat", font=("Arial", 11, "bold")).pack(fill="x", ipady=5)

    def load_product(self):
        product = fetch_one("SELECT * FROM products WHERE id = %s", [self.product_id])
        if product is None:
            messagebox.showerror("Ошибка", "Товар не найден.")
            self.destroy()
            return

        for field in self.vars:
            self.vars[field].set(str(product[field]))

    def save(self):
        try:
            values = {field: var.get().strip() for field, var in self.vars.items()}
            values["price"] = float(values["price"].replace(",", "."))
            values["discount"] = int(values["discount"])
            values["stock_quantity"] = int(values["stock_quantity"])
        except ValueError:
            messagebox.showerror("Проверка данных", "Цена, скидка и количество должны быть числами.")
            return

        if not values["article"] or not values["name"]:
            messagebox.showwarning("Проверка данных", "Заполните артикул и наименование.")
            return

        if values["price"] < 0 or values["discount"] < 0 or values["discount"] > 100 or values["stock_quantity"] < 0:
            messagebox.showwarning("Проверка данных", "Проверьте цену, скидку и количество.")
            return

        params = [
            values["article"],
            values["name"],
            values["category"] or "Без категории",
            values["description"],
            values["manufacturer"] or "Не указан",
            values["supplier"] or "Не указан",
            values["price"],
            values["discount"],
            values["unit"] or "шт",
            values["stock_quantity"],
            values["image_path"],
        ]

        try:
            if self.product_id:
                execute(
                    """
                    UPDATE products
                    SET article=%s, name=%s, category=%s, description=%s, manufacturer=%s,
                        supplier=%s, price=%s, discount=%s, unit=%s, stock_quantity=%s,
                        image_path=%s
                    WHERE id=%s
                    """,
                    params + [self.product_id],
                )
            else:
                execute(
                    """
                    INSERT INTO products (
                        article, name, category, description, manufacturer, supplier,
                        price, discount, unit, stock_quantity, image_path
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    params,
                )
        except Exception as error:
            messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить товар.\n{error}")
            return

        self.parent.load_suppliers()
        self.parent.load_products()
        self.destroy()


if __name__ == "__main__":
    login_window = LoginWindow()
    login_window.mainloop()

    if login_window.auth_user is not None:
        role_name, full_name = login_window.auth_user
        app = ProductsWindow(role_name, full_name)
        app.mainloop()
