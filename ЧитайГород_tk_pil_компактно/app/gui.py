from __future__ import annotations

import tkinter as tk
from dataclasses import replace
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont

from PIL import Image, ImageOps, ImageTk

from . import core


class ScrollableFrame(ttk.Frame):
    def __init__(self, master: tk.Widget, **kwargs):
        super().__init__(master, **kwargs)
        self.canvas = tk.Canvas(self, highlightthickness=0, borderwidth=0, bg=master.cget("bg"))
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=master.cget("bg"))
        self.inner_id = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.inner.bind("<Configure>", self._on_inner_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self._mousewheel_bound = True

    def _on_inner_configure(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self.inner_id, width=event.width)

    def _on_mousewheel(self, event):
        if self.winfo_exists():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class LoginFrame(ttk.Frame):
    def __init__(self, app: "BookstoreApp", master: tk.Widget):
        super().__init__(master, padding=24)
        self.app = app
        self.configure(style="Root.TFrame")
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        left = tk.Frame(self, bg=app.colors["bg"], padx=18, pady=18)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        right = tk.Frame(self, bg=app.colors["card_bg"], highlightthickness=1, highlightbackground=app.colors["accent"])
        right.grid(row=0, column=1, sticky="nsew")

        left.columnconfigure(0, weight=1)
        hero = tk.Frame(left, bg=app.colors["accent"], highlightthickness=0)
        hero.grid(row=0, column=0, sticky="ew")
        hero.columnconfigure(1, weight=1)
        try:
            logo = app.get_photo(core.ICON_PATH, (96, 96))
            logo_label = tk.Label(hero, image=logo, bg=app.colors["accent"])
            logo_label.image = logo
            logo_label.grid(row=0, column=0, rowspan=2, padx=14, pady=14)
        except Exception:
            pass
        tk.Label(hero, text="ЧитайГород", font=app.fonts["title"], bg=app.colors["accent"], fg="white").grid(row=0, column=1, sticky="w", pady=(14, 0), padx=(0, 14))
        tk.Label(hero, text="Учёт книг, товаров и заказов", font=app.fonts["body"], bg=app.colors["accent"], fg="white").grid(row=1, column=1, sticky="w", pady=(0, 14), padx=(0, 14))

        info = tk.Frame(left, bg=app.colors["bg"], highlightthickness=1, highlightbackground=app.colors["accent"])
        info.grid(row=1, column=0, sticky="nsew", pady=(18, 0))
        info.columnconfigure(0, weight=1)
        tk.Label(
            info,
            text="Вход по логину и паролю из базы данных\nили продолжение в роли гостя",
            font=app.fonts["body"],
            justify="left",
            bg=app.colors["bg"],
            fg=app.colors["text"],
            padx=16,
            pady=16,
        ).pack(anchor="w")

        form = tk.Frame(right, bg=app.colors["card_bg"])
        form.pack(fill="both", expand=True, padx=28, pady=28)
        tk.Label(form, text="Вход в систему", font=app.fonts["headline"], bg=app.colors["card_bg"], fg=app.colors["accent_dark"]).pack(anchor="w")
        tk.Label(form, text="Логин", font=app.fonts["body"], bg=app.colors["card_bg"], fg=app.colors["text"]).pack(anchor="w", pady=(24, 4))
        self.login_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.login_entry = ttk.Entry(form, textvariable=self.login_var, width=34)
        self.login_entry.pack(fill="x")
        tk.Label(form, text="Пароль", font=app.fonts["body"], bg=app.colors["card_bg"], fg=app.colors["text"]).pack(anchor="w", pady=(16, 4))
        self.password_entry = ttk.Entry(form, textvariable=self.password_var, show="*")
        self.password_entry.pack(fill="x")
        self.error_label = tk.Label(form, text="", font=app.fonts["small"], fg="#b00020", bg=app.colors["card_bg"])
        self.error_label.pack(anchor="w", pady=(10, 0))

        button_row = tk.Frame(form, bg=app.colors["card_bg"])
        button_row.pack(fill="x", pady=20)
        ttk.Button(button_row, text="Войти", command=self.submit).pack(side="left")
        ttk.Button(button_row, text="Продолжить как гость", command=self.guest).pack(side="left", padx=12)

        self.login_entry.focus_set()
        self.login_entry.bind("<Return>", lambda _e: self.submit())
        self.password_entry.bind("<Return>", lambda _e: self.submit())

    def submit(self):
        self.error_label.config(text="")
        login = self.login_var.get().strip()
        password = self.password_var.get().strip()
        if not login or not password:
            self.error_label.config(text="Введите логин и пароль.")
            return
        try:
            self.app.login(login, password)
        except ValueError as exc:
            self.error_label.config(text=str(exc))

    def guest(self):
        self.app.login_as_guest()


class ProductCard(tk.Frame):
    def __init__(self, master, app: "BookstoreApp", product: core.ProductView, editable: bool):
        bg = app.colors["card_bg"]
        if product.is_out_of_stock:
            bg = app.colors["out_of_stock"]
        elif product.is_discount_highlight:
            bg = app.colors["discount_highlight"]
        super().__init__(master, bg=bg, highlightthickness=1, highlightbackground=app.colors["card_border"])
        self.app = app
        self.product = product
        self.configure(padx=10, pady=10)
        self.columnconfigure(1, weight=1)

        image = app.get_photo(core.product_photo_path(product.photo_path), (150, 100))
        image_label = tk.Label(self, image=image, bg=bg)
        image_label.image = image
        image_label.grid(row=0, column=0, rowspan=4, sticky="nw", padx=(0, 12))

        title = tk.Label(self, text=f"{product.name}", font=app.fonts["card_title"], bg=bg, fg=app.colors["text"])
        title.grid(row=0, column=1, sticky="w")
        article = tk.Label(self, text=f"Артикул: {product.article}", font=app.fonts["small"], bg=bg, fg=app.colors["text"])
        article.grid(row=1, column=1, sticky="w", pady=(2, 0))

        details_text = (
            f"Категория: {product.category}\n"
            f"Описание: {product.description}\n"
            f"Производитель: {product.manufacturer}\n"
            f"Поставщик: {product.supplier}\n"
            f"Ед. изм.: {product.unit}\n"
            f"На складе: {product.stock_qty}\n"
            f"Скидка: {product.discount}%"
        )
        details = tk.Label(self, text=details_text, font=app.fonts["body"], justify="left", wraplength=700, bg=bg, fg=app.colors["text"])
        details.grid(row=2, column=1, sticky="nw", pady=(8, 0))

        price_box = tk.Frame(self, bg=bg)
        price_box.grid(row=0, column=2, rowspan=3, sticky="ne", padx=(16, 0))
        if product.discount > 0:
            strike_font = tkfont.Font(font=app.fonts["body"])
            strike_font.configure(overstrike=True)
            tk.Label(price_box, text=f"{core.format_money(product.price)} ₽", font=strike_font, fg="#cc0000", bg=bg).pack(anchor="e")
            tk.Label(price_box, text=f"{core.format_money(product.final_price)} ₽", font=app.fonts["price"], fg="#111111", bg=bg).pack(anchor="e", pady=(4, 0))
        else:
            tk.Label(price_box, text=f"{core.format_money(product.price)} ₽", font=app.fonts["price"], fg=app.colors["accent_dark"], bg=bg).pack(anchor="e")
        if product.is_out_of_stock:
            tk.Label(price_box, text="Нет на складе", font=app.fonts["body"], fg="#555555", bg=bg).pack(anchor="e", pady=(8, 0))
        elif product.discount > 0:
            tk.Label(price_box, text="Цена со скидкой", font=app.fonts["small"], fg="#444444", bg=bg).pack(anchor="e", pady=(8, 0))

        if editable:
            btns = tk.Frame(self, bg=bg)
            btns.grid(row=3, column=1, columnspan=2, sticky="se", pady=(10, 0))
            ttk.Button(btns, text="Редактировать", command=lambda: app.open_product_editor(product.id)).pack(side="left")
            ttk.Button(btns, text="Удалить", command=lambda: app.delete_product(product.id)).pack(side="left", padx=10)
        self.bind_all_children(self)

    def bind_all_children(self, widget):
        if self.app.current_session.role != core.ROLE_ADMIN:
            return
        for child in widget.winfo_children():
            child.bind("<Double-Button-1>", lambda _e, pid=self.product.id: self.app.open_product_editor(pid))
            if child.winfo_children():
                self.bind_all_children(child)


class ProductsFrame(ttk.Frame):
    def __init__(self, app: "BookstoreApp", master: tk.Widget):
        super().__init__(master, padding=0)
        self.app = app
        self.configure(style="Root.TFrame")
        self.conn = core.connect()
        self.reference = core.get_reference_data(self.conn)
        self.search_var = tk.StringVar()
        self.sort_field_var = tk.StringVar(value="По умолчанию")
        self.sort_dir_var = tk.StringVar(value="По возрастанию")
        self.discount_var = tk.StringVar(value=core.DISCOUNT_FILTERS[0])
        self.sort_map = {
            "По умолчанию": "id",
            "Наименование": "name",
            "Цена": "price",
            "Количество": "stock_qty",
            "Скидка": "discount",
        }
        self.dir_map = {
            "По возрастанию": "asc",
            "По убыванию": "desc",
        }

        header = tk.Frame(self, bg=app.colors["accent"])
        header.pack(fill="x")
        self._build_header(header)

        body = tk.Frame(self, bg=app.colors["bg"])
        body.pack(fill="both", expand=True, padx=18, pady=18)
        body.rowconfigure(1, weight=1)
        body.columnconfigure(0, weight=1)

        controls = tk.Frame(body, bg=app.colors["bg"])
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        controls.columnconfigure(1, weight=1)
        if self.app.current_session.role in {core.ROLE_MANAGER, core.ROLE_ADMIN}:
            tk.Label(controls, text="Поиск", bg=app.colors["bg"], fg=app.colors["text"], font=app.fonts["body"]).grid(row=0, column=0, sticky="w")
            ttk.Entry(controls, textvariable=self.search_var, width=34).grid(row=0, column=1, sticky="ew", padx=(8, 16))
            tk.Label(controls, text="Сортировка", bg=app.colors["bg"], fg=app.colors["text"], font=app.fonts["body"]).grid(row=0, column=2, sticky="w")
            sort_box = ttk.Combobox(controls, textvariable=self.sort_field_var, values=list(self.sort_map.keys()), state="readonly", width=18)
            sort_box.grid(row=0, column=3, padx=(8, 16))
            dir_box = ttk.Combobox(controls, textvariable=self.sort_dir_var, values=list(self.dir_map.keys()), state="readonly", width=14)
            dir_box.grid(row=0, column=4, padx=(0, 16))
            tk.Label(controls, text="Фильтр скидки", bg=app.colors["bg"], fg=app.colors["text"], font=app.fonts["body"]).grid(row=0, column=5, sticky="w")
            filter_box = ttk.Combobox(controls, textvariable=self.discount_var, values=core.DISCOUNT_FILTERS, state="readonly", width=18)
            filter_box.grid(row=0, column=6, padx=(8, 0))
            for var in (self.search_var, self.sort_field_var, self.sort_dir_var, self.discount_var):
                var.trace_add("write", lambda *_: self.refresh())
        else:
            tk.Label(controls, text="Просмотр товаров без фильтрации и поиска", bg=app.colors["bg"], fg=app.colors["text"], font=app.fonts["body"]).grid(row=0, column=0, sticky="w")

        self.info_label = tk.Label(body, text="", bg=app.colors["bg"], fg=app.colors["text"], font=app.fonts["small"])
        self.info_label.grid(row=1, column=0, sticky="nw")

        self.scroll = ScrollableFrame(body)
        self.scroll.grid(row=2, column=0, sticky="nsew")
        body.rowconfigure(2, weight=1)

        self.refresh()

    def _build_header(self, header: tk.Frame):
        header.columnconfigure(1, weight=1)
        logo_img = self.app.get_photo(core.ICON_PATH, (56, 56))
        logo = tk.Label(header, image=logo_img, bg=self.app.colors["accent"])
        logo.image = logo_img
        logo.grid(row=0, column=0, rowspan=2, padx=16, pady=10)
        tk.Label(header, text="ЧитайГород", font=self.app.fonts["headline"], bg=self.app.colors["accent"], fg="white").grid(row=0, column=1, sticky="w", pady=(10, 0))
        tk.Label(header, text="Каталог товаров", font=self.app.fonts["body"], bg=self.app.colors["accent"], fg="white").grid(row=1, column=1, sticky="w", pady=(0, 10))
        user_text = f"{self.app.current_session.full_name}"
        role_text = self.app.current_session.role
        tk.Label(header, text=user_text, font=self.app.fonts["body"], bg=self.app.colors["accent"], fg="white").grid(row=0, column=2, sticky="e", padx=12)
        tk.Label(header, text=role_text, font=self.app.fonts["small"], bg=self.app.colors["accent"], fg="white").grid(row=1, column=2, sticky="e", padx=12, pady=(0, 10))

        buttons = tk.Frame(header, bg=self.app.colors["accent"])
        buttons.grid(row=1, column=2, sticky="e", padx=12, pady=(0, 10))
        if self.app.current_session.role in {core.ROLE_MANAGER, core.ROLE_ADMIN}:
            ttk.Button(buttons, text="Заказы", command=self.app.show_orders).pack(side="left", padx=(0, 8))
        if self.app.current_session.role == core.ROLE_ADMIN:
            ttk.Button(buttons, text="Добавить товар", command=lambda: self.app.open_product_editor(None)).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Выйти", command=self.app.logout).pack(side="left")

    def refresh(self):
        for child in self.scroll.inner.winfo_children():
            child.destroy()
        sort_key = self.sort_map.get(self.sort_field_var.get(), "id")
        sort_dir = self.dir_map.get(self.sort_dir_var.get(), "asc")
        products = core.get_products(
            self.conn,
            search=self.search_var.get() if self.app.current_session.role in {core.ROLE_MANAGER, core.ROLE_ADMIN} else "",
            sort_key=sort_key if self.app.current_session.role in {core.ROLE_MANAGER, core.ROLE_ADMIN} else "id",
            sort_dir=sort_dir if self.app.current_session.role in {core.ROLE_MANAGER, core.ROLE_ADMIN} else "asc",
            discount_filter=self.discount_var.get() if self.app.current_session.role in {core.ROLE_MANAGER, core.ROLE_ADMIN} else core.DISCOUNT_FILTERS[0],
        )
        if self.app.current_session.role not in {core.ROLE_MANAGER, core.ROLE_ADMIN}:
            self.info_label.config(text=f"Показано товаров: {len(products)}")
        else:
            self.info_label.config(text=f"Показано товаров: {len(products)}")
        if not products:
            tk.Label(self.scroll.inner, text="Товары не найдены.", bg=self.app.colors["bg"], fg=self.app.colors["text"], font=self.app.fonts["body"]).pack(anchor="w")
            return
        editable = self.app.current_session.role == core.ROLE_ADMIN
        for product in products:
            card = ProductCard(self.scroll.inner, self.app, product, editable=editable)
            card.pack(fill="x", expand=True, pady=6)


class OrdersFrame(ttk.Frame):
    def __init__(self, app: "BookstoreApp", master: tk.Widget):
        super().__init__(master, padding=0)
        self.app = app
        self.configure(style="Root.TFrame")
        self.conn = core.connect()
        header = tk.Frame(self, bg=app.colors["accent"])
        header.pack(fill="x")
        header.columnconfigure(1, weight=1)
        logo_img = self.app.get_photo(core.ICON_PATH, (56, 56))
        logo = tk.Label(header, image=logo_img, bg=self.app.colors["accent"])
        logo.image = logo_img
        logo.grid(row=0, column=0, rowspan=2, padx=16, pady=10)
        tk.Label(header, text="ЧитайГород", font=self.app.fonts["headline"], bg=self.app.colors["accent"], fg="white").grid(row=0, column=1, sticky="w", pady=(10, 0))
        tk.Label(header, text="Заказы", font=self.app.fonts["body"], bg=self.app.colors["accent"], fg="white").grid(row=1, column=1, sticky="w", pady=(0, 10))
        user_text = f"{self.app.current_session.full_name}"
        role_text = self.app.current_session.role
        tk.Label(header, text=user_text, font=self.app.fonts["body"], bg=self.app.colors["accent"], fg="white").grid(row=0, column=2, sticky="e", padx=12)
        tk.Label(header, text=role_text, font=self.app.fonts["small"], bg=self.app.colors["accent"], fg="white").grid(row=1, column=2, sticky="e", padx=12, pady=(0, 10))
        btns = tk.Frame(header, bg=self.app.colors["accent"])
        btns.grid(row=1, column=2, sticky="e", padx=12, pady=(0, 10))
        ttk.Button(btns, text="Товары", command=self.app.show_products).pack(side="left", padx=(0, 8))
        if self.app.current_session.role == core.ROLE_ADMIN:
            ttk.Button(btns, text="Добавить заказ", command=lambda: self.app.open_order_editor(None)).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="Выйти", command=self.app.logout).pack(side="left")

        body = tk.Frame(self, bg=app.colors["bg"])
        body.pack(fill="both", expand=True, padx=18, pady=18)
        body.rowconfigure(1, weight=1)
        body.columnconfigure(0, weight=1)

        self.search_var = tk.StringVar()
        tk.Label(body, text="Поиск по заказам", bg=app.colors["bg"], fg=app.colors["text"], font=app.fonts["body"]).grid(row=0, column=0, sticky="w")
        entry = ttk.Entry(body, textvariable=self.search_var)
        entry.grid(row=0, column=0, sticky="ew", padx=(140, 0))
        self.search_var.trace_add("write", lambda *_: self.refresh())

        columns = ("number", "status", "customer", "pickup", "order_date", "delivery_date", "articles", "code")
        self.tree = ttk.Treeview(body, columns=columns, show="headings", height=16)
        headings = {
            "number": "№",
            "status": "Статус",
            "customer": "Клиент",
            "pickup": "Пункт выдачи",
            "order_date": "Дата заказа",
            "delivery_date": "Дата выдачи",
            "articles": "Состав заказа",
            "code": "Код",
        }
        widths = {"number": 70, "status": 120, "customer": 220, "pickup": 260, "order_date": 110, "delivery_date": 110, "articles": 280, "code": 90}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], anchor="w")
        yscroll = ttk.Scrollbar(body, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)
        self.tree.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        yscroll.grid(row=1, column=1, sticky="ns", pady=(12, 0))

        bottom = tk.Frame(body, bg=app.colors["bg"])
        bottom.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        bottom.columnconfigure(0, weight=1)
        self.status_label = tk.Label(bottom, text="", bg=app.colors["bg"], fg=app.colors["text"], font=app.fonts["small"])
        self.status_label.grid(row=0, column=0, sticky="w")
        if self.app.current_session.role == core.ROLE_ADMIN:
            ttk.Button(bottom, text="Редактировать", command=self.edit_selected).grid(row=0, column=1, padx=6)
            ttk.Button(bottom, text="Удалить", command=self.delete_selected).grid(row=0, column=2, padx=6)
        self.tree.bind("<Double-Button-1>", lambda _e: self.edit_selected() if self.app.current_session.role == core.ROLE_ADMIN else None)
        self.refresh()

    def refresh(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        orders = core.get_orders(self.conn, self.search_var.get())
        for order in orders:
            self.tree.insert(
                "",
                "end",
                iid=str(order.id),
                values=(
                    order.order_number,
                    order.status,
                    order.customer_name,
                    order.pickup_point,
                    order.order_date or "",
                    order.delivery_date or "",
                    order.articles_text,
                    order.receive_code,
                ),
            )
        self.status_label.config(text=f"Показано заказов: {len(orders)}")

    def _selected_order_id(self) -> int | None:
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Заказы", "Выберите заказ в списке.")
            return None
        return int(sel[0])

    def edit_selected(self):
        order_id = self._selected_order_id()
        if order_id is None:
            return
        self.app.open_order_editor(order_id)

    def delete_selected(self):
        order_id = self._selected_order_id()
        if order_id is None:
            return
        if not messagebox.askyesno("Удаление заказа", "Удалить выбранный заказ? Действие необратимо."):
            return
        try:
            core.delete_order(self.conn, order_id)
            self.refresh()
            messagebox.showinfo("Заказы", "Заказ удалён.")
        except Exception as exc:
            messagebox.showerror("Ошибка удаления", str(exc))


class ProductForm(tk.Toplevel):
    def __init__(self, app: "BookstoreApp", product_id: int | None):
        super().__init__(app)
        self.app = app
        self.product_id = product_id
        self.conn = core.connect()
        self.title("Добавление товара" if product_id is None else "Редактирование товара")
        self.configure(bg=app.colors["bg"])
        self.resizable(False, False)
        self.transient(app)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.photo_source: str | None = None
        self.reference = core.get_reference_data(self.conn)
        self._build_ui()
        self._load_product()
        self.center()

    def _build_ui(self):
        frame = tk.Frame(self, bg=self.app.colors["bg"], padx=16, pady=16)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)
        row = 0
        if self.product_id is not None:
            tk.Label(frame, text="ID", bg=self.app.colors["bg"], fg=self.app.colors["text"]).grid(row=row, column=0, sticky="w", pady=4)
            self.id_var = tk.StringVar()
            ttk.Entry(frame, textvariable=self.id_var, state="readonly", width=18).grid(row=row, column=1, sticky="w", pady=4)
            row += 1
        else:
            self.id_var = tk.StringVar(value="Будет назначен автоматически")
            tk.Label(frame, text="ID", bg=self.app.colors["bg"], fg=self.app.colors["text"]).grid(row=row, column=0, sticky="w", pady=4)
            ttk.Entry(frame, textvariable=self.id_var, state="readonly", width=18).grid(row=row, column=1, sticky="w", pady=4)
            row += 1
        self.article_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.category_var = tk.StringVar()
        self.supplier_var = tk.StringVar()
        self.manufacturer_var = tk.StringVar()
        self.unit_var = tk.StringVar()
        self.price_var = tk.StringVar()
        self.stock_var = tk.StringVar()
        self.discount_var = tk.StringVar()
        self.description_text = tk.Text(frame, width=40, height=5, wrap="word")

        widgets = [
            ("Артикул", ttk.Entry(frame, textvariable=self.article_var, width=40)),
            ("Наименование", ttk.Entry(frame, textvariable=self.name_var, width=40)),
            ("Категория", ttk.Combobox(frame, textvariable=self.category_var, values=self.reference["categories"], state="readonly", width=37)),
            ("Поставщик", ttk.Combobox(frame, textvariable=self.supplier_var, values=self.reference["suppliers"], state="readonly", width=37)),
            ("Производитель", ttk.Combobox(frame, textvariable=self.manufacturer_var, values=self.reference["manufacturers"], state="readonly", width=37)),
            ("Единица измерения", ttk.Entry(frame, textvariable=self.unit_var, width=40)),
            ("Цена", ttk.Entry(frame, textvariable=self.price_var, width=40)),
            ("Количество на складе", ttk.Entry(frame, textvariable=self.stock_var, width=40)),
            ("Действующая скидка", ttk.Entry(frame, textvariable=self.discount_var, width=40)),
        ]
        for label, widget in widgets:
            tk.Label(frame, text=label, bg=self.app.colors["bg"], fg=self.app.colors["text"]).grid(row=row, column=0, sticky="w", pady=4)
            widget.grid(row=row, column=1, sticky="ew", pady=4)
            row += 1

        tk.Label(frame, text="Описание", bg=self.app.colors["bg"], fg=self.app.colors["text"]).grid(row=row, column=0, sticky="nw", pady=4)
        self.description_text.grid(row=row, column=1, sticky="ew", pady=4)
        row += 1

        self.preview_label = tk.Label(frame, bg=self.app.colors["bg"])
        self.preview_label.grid(row=0, column=2, rowspan=8, padx=(16, 0), sticky="n")
        ttk.Button(frame, text="Выбрать фото", command=self.choose_photo).grid(row=8, column=2, sticky="n", padx=(16, 0), pady=(4, 0))
        ttk.Button(frame, text="Сохранить", command=self.save).grid(row=row + 1, column=1, sticky="w", pady=(14, 0))
        ttk.Button(frame, text="Отмена", command=self.close).grid(row=row + 1, column=1, sticky="e", pady=(14, 0))

    def _load_product(self):
        if self.product_id is None:
            self._set_preview(core.PLACEHOLDER_PATH)
            return
        row = self.conn.execute(
            """
            SELECT p.*, c.name AS category_name, s.name AS supplier_name, m.name AS manufacturer_name
            FROM products p
            JOIN categories c ON c.id = p.category_id
            JOIN suppliers s ON s.id = p.supplier_id
            JOIN manufacturers m ON m.id = p.manufacturer_id
            WHERE p.id = ?
            """,
            (self.product_id,),
        ).fetchone()
        if row is None:
            messagebox.showerror("Ошибка", "Товар не найден.")
            self.close()
            return
        self.id_var.set(str(row["id"]))
        self.article_var.set(row["article"])
        self.name_var.set(row["name"])
        self.category_var.set(row["category_name"])
        self.supplier_var.set(row["supplier_name"])
        self.manufacturer_var.set(row["manufacturer_name"])
        self.unit_var.set(row["unit"])
        self.price_var.set(core.format_money(row["price"]))
        self.stock_var.set(str(row["stock_qty"]))
        self.discount_var.set(str(row["discount"]))
        self.description_text.delete("1.0", "end")
        self.description_text.insert("1.0", row["description"])
        self._set_preview(core.product_photo_path(row["photo_path"]))

    def _set_preview(self, image_path: Path):
        try:
            preview = self.app.get_photo(Path(image_path), (260, 170))
            self.preview_label.configure(image=preview)
            self.preview_label.image = preview
        except Exception:
            pass

    def choose_photo(self):
        filename = filedialog.askopenfilename(
            title="Выберите фото товара",
            filetypes=[("Изображения", "*.png *.jpg *.jpeg *.webp")],
        )
        if not filename:
            return
        self.photo_source = filename
        self._set_preview(Path(filename))

    def save(self):
        try:
            product_id = core.save_product(
                self.conn,
                product_id=self.product_id,
                article=self.article_var.get(),
                name=self.name_var.get(),
                category=self.category_var.get(),
                supplier=self.supplier_var.get(),
                manufacturer=self.manufacturer_var.get(),
                unit=self.unit_var.get(),
                price=self.price_var.get(),
                stock_qty=self.stock_var.get(),
                discount=self.discount_var.get(),
                description=self.description_text.get("1.0", "end"),
                photo_source=self.photo_source,
            )
            self.app.unlock_editor()
            self.app.refresh_after_product_change()
            messagebox.showinfo("Товары", f"Товар {'сохранён' if self.product_id else 'добавлен'}.")
            self.destroy()
        except Exception as exc:
            messagebox.showerror("Ошибка сохранения", str(exc))

    def close(self):
        self.app.unlock_editor()
        self.destroy()

    def center(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")


class OrderForm(tk.Toplevel):
    def __init__(self, app: "BookstoreApp", order_id: int | None):
        super().__init__(app)
        self.app = app
        self.order_id = order_id
        self.conn = core.connect()
        self.title("Добавление заказа" if order_id is None else "Редактирование заказа")
        self.configure(bg=app.colors["bg"])
        self.resizable(False, False)
        self.transient(app)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.reference = core.get_reference_data(self.conn)
        self._build_ui()
        self._load_order()
        self.center()

    def _build_ui(self):
        frame = tk.Frame(self, bg=self.app.colors["bg"], padx=16, pady=16)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)
        self.order_number_var = tk.StringVar()
        self.status_var = tk.StringVar()
        self.pickup_var = tk.StringVar()
        self.date_var = tk.StringVar()
        self.delivery_var = tk.StringVar()
        self.customer_var = tk.StringVar()
        self.receive_code_var = tk.StringVar()
        self.articles_text = tk.Text(frame, width=44, height=5, wrap="word")

        fields = [
            ("Номер заказа", ttk.Entry(frame, textvariable=self.order_number_var, width=40, state="readonly")),
            ("Статус заказа", ttk.Combobox(frame, textvariable=self.status_var, values=core.STATUS_OPTIONS, state="readonly", width=37)),
            ("Клиент", ttk.Combobox(frame, textvariable=self.customer_var, values=self.reference["customers"], state="readonly", width=37)),
            ("Адрес пункта выдачи", ttk.Combobox(frame, textvariable=self.pickup_var, values=self.reference["pickup_points"], state="readonly", width=37)),
            ("Дата заказа", ttk.Entry(frame, textvariable=self.date_var, width=40)),
            ("Дата выдачи", ttk.Entry(frame, textvariable=self.delivery_var, width=40)),
            ("Код для получения", ttk.Entry(frame, textvariable=self.receive_code_var, width=40)),
        ]
        row = 0
        for label, widget in fields:
            tk.Label(frame, text=label, bg=self.app.colors["bg"], fg=self.app.colors["text"]).grid(row=row, column=0, sticky="w", pady=4)
            widget.grid(row=row, column=1, sticky="ew", pady=4)
            row += 1
        tk.Label(frame, text="Артикулы и количество (например: A123 × 2; B456 × 1)", bg=self.app.colors["bg"], fg=self.app.colors["text"]).grid(row=row, column=0, sticky="nw", pady=4)
        self.articles_text.grid(row=row, column=1, sticky="ew", pady=4)
        row += 1
        ttk.Button(frame, text="Сохранить", command=self.save).grid(row=row, column=1, sticky="w", pady=(14, 0))
        ttk.Button(frame, text="Отмена", command=self.close).grid(row=row, column=1, sticky="e", pady=(14, 0))

    def _load_order(self):
        if self.order_id is None:
            self.order_number_var.set(str(core.next_order_number_hint(self.conn)))
            self.receive_code_var.set(str(int(core.next_order_number_hint(self.conn)) + 899))
            if self.reference["statuses"] if False else False:
                pass
            self.status_var.set(core.STATUS_OPTIONS[0])
            if self.reference["customers"]:
                self.customer_var.set(self.reference["customers"][0])
            if self.reference["pickup_points"]:
                self.pickup_var.set(self.reference["pickup_points"][0])
            return
        row = self.conn.execute(
            """
            SELECT o.*, u.full_name AS customer_name, pp.address AS pickup_point
            FROM orders o
            JOIN users u ON u.id = o.customer_id
            JOIN pickup_points pp ON pp.id = o.pickup_point_id
            WHERE o.id = ?
            """,
            (self.order_id,),
        ).fetchone()
        if row is None:
            messagebox.showerror("Ошибка", "Заказ не найден.")
            self.close()
            return
        self.order_number_var.set(str(row["order_number"]))
        self.status_var.set(row["status"])
        self.customer_var.set(row["customer_name"])
        self.pickup_var.set(row["pickup_point"])
        self.date_var.set(row["order_date"] or "")
        self.delivery_var.set(row["delivery_date"] or "")
        self.receive_code_var.set(str(row["receive_code"]))
        self.articles_text.delete("1.0", "end")
        items = self.conn.execute(
            """
            SELECT p.article, oi.quantity
            FROM order_items oi
            JOIN products p ON p.id = oi.product_id
            WHERE oi.order_id = ?
            ORDER BY oi.id ASC
            """,
            (self.order_id,),
        ).fetchall()
        raw = "; ".join(f"{item['article']} × {item['quantity']}" for item in items)
        self.articles_text.insert("1.0", raw)

    def save(self):
        try:
            core.save_order(
                self.conn,
                order_id=self.order_id,
                order_number=self.order_number_var.get(),
                status=self.status_var.get(),
                pickup_point=self.pickup_var.get(),
                order_date=self.date_var.get(),
                delivery_date=self.delivery_var.get(),
                customer=self.customer_var.get(),
                articles_text=self.articles_text.get("1.0", "end"),
                receive_code=self.receive_code_var.get(),
            )
            self.app.unlock_editor()
            self.app.refresh_after_order_change()
            messagebox.showinfo("Заказы", f"Заказ {'сохранён' if self.order_id else 'добавлен'}.")
            self.destroy()
        except Exception as exc:
            messagebox.showerror("Ошибка сохранения", str(exc))

    def close(self):
        self.app.unlock_editor()
        self.destroy()

    def center(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"+{x}+{y}")


class BookstoreApp(tk.Tk):
    def __init__(self):
        super().__init__()
        core.initialize_database()
        self.current_session = core.SessionUser(id=None, role="Гость", full_name="Гость")
        self.editor_lock: str | None = None
        self.image_cache: dict[tuple[str, tuple[int, int]], ImageTk.PhotoImage] = {}
        self.colors = {
            "bg": "#FFFFFF",
            "accent": "#ABCFCE",
            "accent_dark": "#546F94",
            "text": "#1f1f1f",
            "card_bg": "#FFFFFF",
            "card_border": "#D0D0D0",
            "discount_highlight": "#23E1EF",
            "out_of_stock": "#D9D9D9",
        }
        self.fonts = {
            "title": ("Comic Sans MS", 28, "bold"),
            "headline": ("Comic Sans MS", 18, "bold"),
            "body": ("Comic Sans MS", 11),
            "small": ("Comic Sans MS", 9),
            "card_title": ("Comic Sans MS", 14, "bold"),
            "price": ("Comic Sans MS", 16, "bold"),
        }
        self.title("ЧитайГород")
        self.geometry("1440x920")
        self.minsize(1200, 780)
        self.configure(bg=self.colors["bg"])
        self._configure_style()
        self._apply_fonts()
        self._set_window_icon()
        self.container = ttk.Frame(self, style="Root.TFrame")
        self.container.pack(fill="both", expand=True)
        self.current_frame: tk.Widget | None = None
        self.show_login()

    def _configure_style(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Root.TFrame", background=self.colors["bg"])
        style.configure("TFrame", background=self.colors["bg"])
        style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["text"], font=self.fonts["body"])
        style.configure("TButton", font=self.fonts["body"], padding=6)
        style.configure("TEntry", padding=4)
        style.configure("TCombobox", padding=4)
        style.configure("Treeview", font=self.fonts["body"], rowheight=28)
        style.configure("Treeview.Heading", font=self.fonts["body"])

    def _apply_fonts(self):
        for name in ["TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont", "TkCaptionFont", "TkSmallCaptionFont"]:
            try:
                font = tkfont.nametofont(name)
                font.configure(family="Comic Sans MS", size=11)
            except Exception:
                pass

    def _set_window_icon(self):
        for path in (core.ICON_ICO_PATH, core.ICON_PATH):
            if path.exists():
                try:
                    if path.suffix.lower() == ".ico":
                        self.iconbitmap(default=str(path))
                    else:
                        icon = ImageTk.PhotoImage(Image.open(path))
                        self.iconphoto(True, icon)
                        self._window_icon = icon
                    break
                except Exception:
                    continue

    def get_photo(self, path: Path, size: tuple[int, int]) -> ImageTk.PhotoImage:
        resolved = Path(path)
        if not resolved.exists():
            resolved = core.PLACEHOLDER_PATH
        key = (str(resolved), size)
        cached = self.image_cache.get(key)
        if cached is not None:
            return cached
        with Image.open(resolved) as img:
            image = ImageOps.contain(img.convert("RGB"), size, method=Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", size, self.colors["bg"])
            x = (size[0] - image.width) // 2
            y = (size[1] - image.height) // 2
            canvas.paste(image, (x, y))
        photo = ImageTk.PhotoImage(canvas)
        self.image_cache[key] = photo
        return photo

    def clear_frame(self):
        if self.current_frame is not None:
            self.current_frame.destroy()
            self.current_frame = None

    def show_login(self):
        self.current_session = core.SessionUser(id=None, role="Гость", full_name="Гость")
        self.unlock_editor(force=True)
        self.title("Вход | ЧитайГород")
        self.clear_frame()
        self.current_frame = LoginFrame(self, self.container)
        self.current_frame.pack(fill="both", expand=True)

    def show_products(self):
        self.title("Товары | ЧитайГород")
        self.clear_frame()
        self.current_frame = ProductsFrame(self, self.container)
        self.current_frame.pack(fill="both", expand=True)

    def show_orders(self):
        self.title("Заказы | ЧитайГород")
        self.clear_frame()
        self.current_frame = OrdersFrame(self, self.container)
        self.current_frame.pack(fill="both", expand=True)

    def login(self, login: str, password: str):
        conn = core.connect()
        row = conn.execute("SELECT id, role, full_name, password_hash FROM users WHERE login = ?", (login,)).fetchone()
        if row is None or not core.verify_password(password, row["password_hash"]):
            raise ValueError("Неверный логин или пароль.")
        if row["role"] not in core.ROLES:
            raise ValueError("Роль пользователя не поддерживается.")
        self.current_session = core.SessionUser(id=int(row["id"]), role=row["role"], full_name=row["full_name"])
        self.show_products()

    def login_as_guest(self):
        self.current_session = core.SessionUser(id=None, role="Гость", full_name="Гость")
        self.show_products()

    def logout(self):
        self.show_login()

    def open_product_editor(self, product_id: int | None):
        if self.current_session.role != core.ROLE_ADMIN:
            return
        if self.editor_lock is not None:
            messagebox.showwarning("Редактирование", "Уже открыта форма редактирования. Завершите её перед открытием новой.")
            return
        self.editor_lock = f"product:{product_id if product_id is not None else 'new'}"
        ProductForm(self, product_id)

    def open_order_editor(self, order_id: int | None):
        if self.current_session.role != core.ROLE_ADMIN:
            return
        if self.editor_lock is not None:
            messagebox.showwarning("Редактирование", "Уже открыта форма редактирования. Завершите её перед открытием новой.")
            return
        self.editor_lock = f"order:{order_id if order_id is not None else 'new'}"
        OrderForm(self, order_id)

    def unlock_editor(self, force: bool = False):
        if force or self.editor_lock is not None:
            self.editor_lock = None

    def refresh_after_product_change(self):
        if isinstance(self.current_frame, ProductsFrame):
            self.current_frame.refresh()
        elif self.current_session.role in {core.ROLE_MANAGER, core.ROLE_ADMIN}:
            self.show_products()

    def refresh_after_order_change(self):
        if isinstance(self.current_frame, OrdersFrame):
            self.current_frame.refresh()
        elif self.current_session.role in {core.ROLE_MANAGER, core.ROLE_ADMIN}:
            self.show_orders()

    def delete_product(self, product_id: int):
        if self.current_session.role != core.ROLE_ADMIN:
            return
        if not messagebox.askyesno("Удаление товара", "Удалить выбранный товар? Действие необратимо."):
            return
        conn = core.connect()
        try:
            core.delete_product(conn, product_id)
            self.refresh_after_product_change()
            messagebox.showinfo("Товары", "Товар удалён.")
        except Exception as exc:
            messagebox.showerror("Ошибка удаления", str(exc))


if __name__ == "__main__":
    app = BookstoreApp()
    app.mainloop()
