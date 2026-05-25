from tkinter import *
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

tk = None
search_var = None
cards_frame = None
photo_images = []

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def fetch_all(sql, params=None):
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or [])
            return cursor.fetchall()

def show_main_window():
    global tk, search_var, cards_frame
    tk = Tk()
    tk.title("Товары")
    tk.geometry("900x650")
    tk.config(bg="#F8F8F8")

    search_var = StringVar()

    header = Frame(tk, bg="#D4E09B", padx=15, pady=12)
    header.pack(fill="x")
    Label(header, text="Список товаров", bg="#D4E09B", font=("Arial", 18, "bold")).pack(side="left")

    tools = Frame(tk, bg="#F8F8F8", padx=15, pady=10)
    tools.pack(fill="x")
    Label(tools, text="Поиск:", bg="#F8F8F8").pack(side="left")
    Entry(tools, textvariable=search_var, width=30).pack(side="left", padx=(5, 10))

    canvas = Canvas(tk, bg="#F8F8F8", highlightthickness=0)
    scrollbar = Scrollbar(tk, orient="vertical", command=canvas.yview)
    cards_frame = Frame(canvas, bg="#F8F8F8")

    window_id = canvas.create_window((0, 0), window=cards_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True, padx=(15, 0), pady=(0, 15))
    scrollbar.pack(side="right", fill="y", padx=(0, 15), pady=(0, 15))
    cards_frame.bind("<Configure>", lambda event: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window_id, width=event.width))

    search_var.trace_add("write", lambda *args: load_products())
    load_products()
    tk.mainloop()

def create_card(row):
    article_num, product, unit, price, supplier, creator, category, discount, inventory, photo = row

    bg = "white"
    if inventory == 0:
        bg = "#BFD7EA"
    elif discount > 15:
        bg = "#2E8B57"

    fg = "white" if bg == "#2E8B57" else "#333333"

    card = Frame(cards_frame, bg=bg, padx=10, pady=10, highlightthickness=2, highlightbackground="#333333")
    card.pack(fill="x", pady=6)

    photo_box = Frame(card, bg=bg, width=140, height=110, highlightthickness=1, highlightbackground="#333333")
    photo_box.grid(row=0, column=0, sticky="ns", padx=(0, 10))
    photo_box.grid_propagate(False)
    show_photo(photo_box, photo, bg, fg)

    info = Frame(card, bg=bg)
    info.grid(row=0, column=1, sticky="nsew", padx=(0, 10))
    Label(info, text=f"{category} | {product}", bg=bg, fg=fg, font=("Arial", 13, "bold"), anchor="w").pack(fill="x")
    Label(info, text=f"Артикул: {article_num}", bg=bg, fg=fg, anchor="w").pack(fill="x")
    Label(info, text=f"Производитель: {creator}", bg=bg, fg=fg, anchor="w").pack(fill="x")
    Label(info, text=f"Поставщик: {supplier}", bg=bg, fg=fg, anchor="w").pack(fill="x")
    Label(info, text=f"Цена: {price} руб.", bg=bg, fg=fg, anchor="w").pack(fill="x")
    Label(info, text=f"Единица: {unit}", bg=bg, fg=fg, anchor="w").pack(fill="x")
    Label(info, text=f"Остаток: {inventory}", bg=bg, fg=fg, anchor="w").pack(fill="x")

    discount_box = Frame(card, bg=bg, width=120, height=110, highlightthickness=1, highlightbackground="#333333")
    discount_box.grid(row=0, column=2, sticky="ns")
    discount_box.grid_propagate(False)
    Label(discount_box, text=f"Скидка\n{discount}%", bg=bg, fg=fg, font=("Arial", 12, "bold")).place(relx=0.5, rely=0.5, anchor="center")

    card.columnconfigure(1, weight=1)

def load_products():
    global photo_images
    photo_images = []

    for widget in cards_frame.winfo_children():
        widget.destroy()

    search = search_var.get().strip()
    if search:
        rows = fetch_all("""
            SELECT article_num, product, unit, price, supplier, creator, category, discount, inventory, photo
            FROM products
            WHERE product ILIKE %s OR category ILIKE %s OR supplier ILIKE %s
            ORDER BY id_p
        """, [f"%{search}%", f"%{search}%", f"%{search}%"])
    else:
        rows = fetch_all("""
            SELECT article_num, product, unit, price, supplier, creator, category, discount, inventory, photo
            FROM products
            ORDER BY id_p
        """)

    for row in rows:
        create_card(row)

def show_photo(parent, photo, bg, fg):
    path = BASE_DIR / photo if photo else BASE_DIR / "image/picture.png"
    if not path.exists():
        path = BASE_DIR / "image/picture.png"

    try:
        image = Image.open(path)
        image.thumbnail((120, 90))
        tk_image = ImageTk.PhotoImage(image)
        photo_images.append(tk_image)
        Label(parent, image=tk_image, bg=bg).place(relx=0.5, rely=0.5, anchor="center")
    except Exception:
        Label(parent, text="Фото\nнет", bg=bg, fg=fg).place(relx=0.5, rely=0.5, anchor="center")

show_main_window()
