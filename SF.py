import os
import sqlite3
import tkinter as tk
from tkinter import messagebox, ttk


class MarketOrderSystem:

    def __init__(self, root):
        self.root = root
        self.root.title("Электронный магазин — Система формирования заказов с БД")
        self.root.geometry("820x680")


        self.db_path = "market_database.db"
        self.init_database()


        self.cart = {}
        self.discount = 0.0
        self.sort_asc = True


        self.update_local_stats_from_db()

        self.setup_styles()
        self.create_widgets()

    def init_database(self):

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()


            cursor.execute(
                "CREATE TABLE IF NOT EXISTS profile (id INTEGER PRIMARY KEY, balance INTEGER)"
            )
            cursor.execute("SELECT COUNT(*) FROM profile")
            if cursor.fetchone()[0] == 0:

                cursor.execute("INSERT INTO profile (id, balance) VALUES (1, ?)", (150000,))


            cursor.execute(
                "CREATE TABLE IF NOT EXISTS products (name TEXT PRIMARY KEY, price INTEGER, stock INTEGER)"
            )
            cursor.execute("SELECT COUNT(*) FROM products")
            if cursor.fetchone()[0] == 0:
                default_products = [
                    ("Смартфон", 45000, 3),
                    ("Ноутбук", 85000, 1),
                    ("Наушники", 12000, 5),
                    ("Умные часы", 18000, 0),
                    ("Планшет", 35000, 4),
                    ("Монитор", 22000, 2),
                    ("Игровая мышь", 4500, 10),
                    ("Клавиатура", 6000, 7),
                    ("Колонки", 8000, 3),
                ]

                cursor.executemany(
                    "INSERT INTO products (name, price, stock) VALUES (?, ?, ?)", default_products
                )


            cursor.execute(
                "CREATE TABLE IF NOT EXISTS reviews (id INTEGER PRIMARY KEY AUTOINCREMENT, product_name TEXT, rating INTEGER, text TEXT)"
            )
            cursor.execute("SELECT COUNT(*) FROM reviews")
            if cursor.fetchone()[0] == 0:
                default_reviews = [
                    ("Смартфон", 5, "Отличный телефон, камера супер!"),
                    ("Ноутбук", 4, "Мощный, но немного шумит."),
                    ("Наушники", 5, "Звук чистый, басы глубокие."),
                ]
                cursor.executemany(
                    "INSERT INTO reviews (product_name, rating, text) VALUES (?, ?, ?)", default_reviews
                )


            cursor.execute(
                "CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, invoice_text TEXT)"
            )


            cursor.execute(
                "CREATE TABLE IF NOT EXISTS system_stats (key TEXT PRIMARY KEY, value INTEGER)"
            )
            for key in ["stock_failures", "payment_failures"]:
                cursor.execute(
                    "INSERT OR IGNORE INTO system_stats (key, value) VALUES (?, 0)", (key,)
                )
            conn.commit()

    def get_user_balance(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT balance FROM profile WHERE id = 1")
            return cursor.fetchone()[0]

    def update_local_stats_from_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM system_stats WHERE key = 'stock_failures'")
            self.stats_stock_failures = cursor.fetchone()[0]

            cursor.execute("SELECT value FROM system_stats WHERE key = 'payment_failures'")
            self.stats_payment_failures = cursor.fetchone()[0]

    def setup_styles(self):
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TNotebook.Tab", font=("Arial", 10, "bold"), padding=6)
        self.style.configure(
            "Action.TButton", font=("Arial", 10, "bold"), background="#4CAF50", foreground="white"
        )

    def create_widgets(self):
        self.top_panel = ttk.Frame(self.root, padding=10)
        self.top_panel.pack(fill=tk.X)

        self.balance_label = ttk.Label(
            self.top_panel,
            text=f"Ваш баланс: {self.get_user_balance():,} руб.",
            font=("Arial", 12, "bold"),
            foreground="#2E7D32",
        )
        self.balance_label.pack(side=tk.RIGHT, padx=(10, 0))

        self.add_money_btn = ttk.Button(
            self.top_panel, text=" Пополнить баланс (+10к)", command=self.deposit_money
        )
        self.add_money_btn.pack(side=tk.RIGHT)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.tab_catalog = ttk.Frame(self.notebook, padding=10)
        self.tab_cart = ttk.Frame(self.notebook, padding=10)
        self.tab_history = ttk.Frame(self.notebook, padding=10)
        self.tab_analytics = ttk.Frame(self.notebook, padding=10)
        self.tab_log = ttk.Frame(self.notebook, padding=10)

        self.notebook.add(self.tab_catalog, text=" Каталог и Отзывы")
        self.notebook.add(self.tab_cart, text=" Корзина")
        self.notebook.add(self.tab_history, text=" История заказов")
        self.notebook.add(self.tab_analytics, text=" Панель менеджера")
        self.notebook.add(self.tab_log, text="⚙ Лог бизнес-логики")

        self.build_catalog_tab()
        self.build_cart_tab()
        self.build_history_tab()
        self.build_analytics_tab()
        self.build_log_tab()

    def deposit_money(self):
        current_balance = self.get_user_balance()
        new_balance = current_balance + 10000
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute("UPDATE profile SET balance = ? WHERE id = 1", (new_balance,))
            conn.commit()
        self.balance_label.config(text=f"Ваш баланс: {new_balance:,} руб.")
        messagebox.showinfo("Баланс", "Баланс успешно пополнен на 10 000 рублей!")

    def build_catalog_tab(self):
        search_frame = ttk.Frame(self.tab_catalog, padding=5)
        search_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(search_frame, text=" Поиск (SQL Safe): ").pack(side=tk.LEFT)
        self.search_entry = ttk.Entry(search_frame, width=20)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind("<KeyRelease>", lambda event: self.update_catalog_view())

        self.btn_sort = ttk.Button(search_frame, text="↕ Сортировать по цене", command=self.toggle_sort)
        self.btn_sort.pack(side=tk.RIGHT)

        columns = ("name", "price", "stock", "rating")
        self.catalog_tree = ttk.Treeview(self.tab_catalog, columns=columns, show="headings", height=7)
        self.catalog_tree.heading("name", text="Название товара")
        self.catalog_tree.heading("price", text="Цена (руб.)")
        self.catalog_tree.heading("stock", text="Остаток на складе (шт.)")
        self.catalog_tree.heading("rating", text="Рейтинг ")
        self.catalog_tree.pack(fill=tk.X, pady=5)

        self.catalog_tree.bind("<<TreeviewSelect>>", lambda event: self.load_product_reviews())
        self.update_catalog_view()

        cat_btn_frame = ttk.Frame(self.tab_catalog)
        cat_btn_frame.pack(fill=tk.X, pady=5)

        ttk.Button(cat_btn_frame, text=" Добавить выбранный товар в корзину", command=self.add_to_cart).pack(
            side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        ttk.Button(cat_btn_frame, text=" Поставка на склад (+5 шт)", command=self.restock_product).pack(side=tk.RIGHT)

        review_main_frame = ttk.LabelFrame(self.tab_catalog, text=" Отзывы и оценки покупателей", padding=10)
        review_main_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.reviews_txt = tk.Text(review_main_frame, width=45, bg="#F9F9F9", state=tk.DISABLED, font=("Arial", 10))
        self.reviews_txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        review_form = ttk.Frame(review_main_frame)
        review_form.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Label(review_form, text="Ваша оценка:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        self.rating_var = tk.IntVar(value=5)
        stars_frame = ttk.Frame(review_form)
        stars_frame.pack(anchor=tk.W, pady=2)
        for i in range(1, 6):
            ttk.Radiobutton(stars_frame, text=str(i), variable=self.rating_var, value=i).pack(side=tk.LEFT, padx=2)

        ttk.Label(review_form, text="Текст отзыва:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(5, 2))
        self.review_entry = ttk.Entry(review_form, width=25)
        self.review_entry.pack(fill=tk.X, pady=2)

        ttk.Button(review_form, text="Отправить отзыв", command=self.add_review).pack(fill=tk.X, pady=8)

    def toggle_sort(self):
        self.sort_asc = not self.sort_asc
        self.update_catalog_view()

    def restock_product(self):
        selected = self.catalog_tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите товар в таблице для поставки!")
            return
        item_values = self.catalog_tree.item(selected, "values")
        product_name = item_values[0]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE products SET stock = stock + 5 WHERE name = ?", (product_name,))
            conn.commit()

        self.update_catalog_view()
        messagebox.showinfo("Склад пополнен", f"Товар '{product_name}' успешно завезен на склад (+5 шт.)!")

    def update_catalog_view(self):
        for item in self.catalog_tree.get_children():
            self.catalog_tree.delete(item)

        search_query = self.search_entry.get().strip()

        sql_search = f"%{search_query}%"
        order_dir = "ASC" if self.sort_asc else "DESC"

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(f"SELECT name, price, stock FROM products WHERE name LIKE ? ORDER BY price {order_dir}",
                           (sql_search,))
            products_list = cursor.fetchall()

            for name, price, stock in products_list:

                cursor.execute("SELECT AVG(rating), COUNT(rating) FROM reviews WHERE product_name = ?", (name,))
                avg, count = cursor.fetchone()
                rating_str = f"{avg:.1f} ({count} шт.)" if avg else "Нет оценок"

                self.catalog_tree.insert("", tk.END, values=(name, f"{price:,}", stock, rating_str))

    def load_product_reviews(self):
        selected = self.catalog_tree.selection()
        self.reviews_txt.config(state=tk.NORMAL)
        self.reviews_txt.delete("1.0", tk.END)

        if not selected:
            self.reviews_txt.insert(tk.END, "Выберите товар в каталоге, чтобы прочесть отзывы.")
            self.reviews_txt.config(state=tk.DISABLED)
            return

        product_name = self.catalog_tree.item(selected, "values")[0]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT rating, text FROM reviews WHERE product_name = ?", (product_name,))
            reviews = cursor.fetchall()

        if not reviews:
            self.reviews_txt.insert(tk.END, f"У товара '{product_name}' пока нет отзывов. Будьте первым!")
        else:
            self.reviews_txt.insert(tk.END, f"--- Отзывы о товаре '{product_name}' ---\n\n")
            for rating, text in reviews:
                stars = "★" * rating + "☆" * (5 - rating)
                self.reviews_txt.insert(tk.END, f"Оценка: {stars} ({rating}/5)\nКомментарий: {text}\n")
                self.reviews_txt.insert(tk.END, "-" * 35 + "\n")

        self.reviews_txt.config(state=tk.DISABLED)

    def add_review(self):
        selected = self.catalog_tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите товар в таблице каталога, чтобы оставить отзыв!")
            return

        product_name = self.catalog_tree.item(selected, "values")[0]
        text = self.review_entry.get().strip()
        rating = self.rating_var.get()

        if not text:
            messagebox.showwarning("Внимание", "Напишите хотя бы короткий текст отзыва!")
            return


        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO reviews (product_name, rating, text) VALUES (?, ?, ?)",
                           (product_name, rating, text))
            conn.commit()

        self.review_entry.delete(0, tk.END)
        self.update_catalog_view()
        self.load_product_reviews()
        messagebox.showinfo("Спасибо", f"Ваш отзыв на '{product_name}' успешно опубликован!")

    def add_to_cart(self):
        selected = self.catalog_tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Выберите товар из списка!")
            return
        product_name = self.catalog_tree.item(selected, "values")[0]
        self.cart[product_name] = self.cart.get(product_name, 0) + 1
        self.update_cart_view()
        messagebox.showinfo("Корзина", f"Товар '{product_name}' добавлен в корзину.")

    def build_cart_tab(self):
        ttk.Label(self.tab_cart, text="Ваша корзина:", font=("Arial", 12, "bold")).pack(anchor=tk.W, pady=5)
        self.cart_listbox = tk.Listbox(self.tab_cart, font=("Arial", 11), height=8)
        self.cart_listbox.pack(fill=tk.BOTH, expand=True, pady=5)

        delivery_frame = ttk.LabelFrame(self.tab_cart, text=" Выберите способ доставки", padding=10)
        delivery_frame.pack(fill=tk.X, pady=5)

        self.delivery_var = tk.StringVar(value="Самовывоз")
        self.delivery_types = {"Самовывоз": 0, "Обычная доставка": 300, "Экспресс-доставка": 800}

        for d_name, d_price in self.delivery_types.items():
            ttk.Radiobutton(delivery_frame, text=f"{d_name} (+{d_price} руб.)", variable=self.delivery_var,
                            value=d_name, command=self.update_cart_view).pack(side=tk.LEFT, padx=15)

        promo_frame = ttk.Frame(self.tab_cart)
        promo_frame.pack(fill=tk.X, pady=5)
        ttk.Label(promo_frame, text="Промокод (STUDENT - 10%): ", font=("Arial", 10)).pack(side=tk.LEFT)
        self.promo_entry = ttk.Entry(promo_frame, width=15)
        self.promo_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(promo_frame, text="Применить", command=self.apply_promo).pack(side=tk.LEFT)

        self.total_price_label = ttk.Label(self.tab_cart, text="Итого к оплате: 0 руб.", font=("Arial", 11, "bold"))
        self.total_price_label.pack(anchor=tk.E, pady=5)

        btn_frame = ttk.Frame(self.tab_cart)
        btn_frame.pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text=" Удалить 1 шт.", command=self.remove_one_from_cart).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text=" Очистить всё", command=self.clear_cart).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text=" Оформить и оплатить заказ", style="Action.TButton",
                   command=self.checkout_process).pack(side=tk.RIGHT, padx=5)

    def apply_promo(self):
        code = self.promo_entry.get().strip().upper()
        if code == "STUDENT":
            self.discount = 0.10
            messagebox.showinfo("Успех", "Промокод STUDENT успешно применен! Скидка 10%.")
        else:
            self.discount = 0.0
            messagebox.showerror("Ошибка", "Неверный промокод!")
        self.update_cart_view()

    def remove_one_from_cart(self):
        selected_index = self.cart_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("Внимание", "Выберите товар в корзине для удаления!")
            return
        selected_text = self.cart_listbox.get(selected_index)
        product_name = selected_text.split(" x")[0].strip()
        if product_name in self.cart:
            if self.cart[product_name] > 1:
                self.cart[product_name] -= 1
            else:
                del self.cart[product_name]
            self.update_cart_view()

    def update_cart_view(self):
        self.cart_listbox.delete(0, tk.END)
        raw_total = 0

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for name, count in self.cart.items():
                cursor.execute("SELECT price FROM products WHERE name = ?", (name,))
                price = cursor.fetchone()[0]
                cost = price * count
                raw_total += cost
                self.cart_listbox.insert(tk.END, f"{name} x{count} шт. — {cost:,} руб.")

        discounted_total = int(raw_total * (1 - self.discount))
        delivery_cost = self.delivery_types[self.delivery_var.get()]
        final_total = discounted_total + delivery_cost
        self.total_price_label.config(
            text=f"Товары: {discounted_total:,} руб. + Доставка: {delivery_cost} руб. | ИТОГО: {final_total:,} руб.")

    def clear_cart(self):
        self.cart.clear()
        self.discount = 0.0
        self.promo_entry.delete(0, tk.END)
        self.delivery_var.set("Самовывоз")
        self.update_cart_view()

    def build_history_tab(self):
        ttk.Label(self.tab_history, text="Выписанные накладные из Базы Данных:", font=("Arial", 12, "bold")).pack(
            anchor=tk.W, pady=5)
        self.history_txt = tk.Text(self.tab_history, bg="#FAFAFA", state=tk.DISABLED, font=("Courier", 10))
        self.history_txt.pack(fill=tk.BOTH, expand=True)
        self.update_history_view()

    def update_history_view(self):
        self.history_txt.config(state=tk.NORMAL)
        self.history_txt.delete("1.0", tk.END)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT invoice_text FROM orders ORDER BY id DESC")
            for row in cursor.fetchall():
                self.history_txt.insert(tk.END, row[0])
        self.history_txt.config(state=tk.DISABLED)

    def build_analytics_tab(self):
        ttk.Label(self.tab_analytics, text=" Финансовая и складская отчетность:", font=("Arial", 12, "bold")).pack(
            anchor=tk.W, pady=5)
        self.analytics_txt = tk.Text(self.tab_analytics, bg="#F0F4C3", state=tk.DISABLED, font=("Arial", 11))
        self.analytics_txt.pack(fill=tk.BOTH, expand=True)
        self.update_analytics_view()

    def update_analytics_view(self):
        self.analytics_txt.config(state=tk.NORMAL)
        self.analytics_txt.delete("1.0", tk.END)
        self.update_local_stats_from_db()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM orders")
            success_count = cursor.fetchone()[0]

            report = (
                f" Успешно оформлено заказов: {success_count} шт.\n"
                f" Отказов из-за отсутствия товара: {self.stats_stock_failures} раз\n"
                f" Отказов из-за ошибки оплаты: {self.stats_payment_failures} раз\n\n"
                f" Актуальные остатки на складе (БД):\n"
            )
            cursor.execute("SELECT name, stock FROM products")
            for name, stock in cursor.fetchall():
                report += f"  - {name}: остаток {stock} шт.\n"

        self.analytics_txt.insert(tk.END, report)
        self.analytics_txt.config(state=tk.DISABLED)

    def build_log_tab(self):
        ttk.Label(self.tab_log, text="Технический отчет прохождения шагов блок-схемы:", font=("Arial", 10, "italic"),
                  foreground="gray")
        self.log_txt = tk.Text(self.tab_log, bg="#1E1E1E", fg="#FFFFFF", state=tk.DISABLED, font=("Courier", 10))
        self.log_txt.pack(fill=tk.BOTH, expand=True)

    def system_log(self, text: str):
        self.log_txt.config(state=tk.NORMAL)
        self.log_txt.insert(tk.END, text + "\n")
        self.log_txt.see(tk.END)
        self.log_txt.config(state=tk.DISABLED)

    def checkout_process(self):
        if not self.cart:
            messagebox.showwarning("Пусто", "Ваша корзина пуста!")
            return

        self.system_log("\n======= ЗАПУСК ПРОЦЕССА ФОРМИРОВАНИЯ ЗАКАЗА =======")
        self.system_log("Начало\nПолучение запроса на заказ...")

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            raw_total = 0
            for name, count in self.cart.items():
                cursor.execute("SELECT price, stock FROM products WHERE name = ?", (name,))
                price, stock = cursor.fetchone()
                raw_total += price * count


                if stock < count:
                    self.system_log(f"Товар доступен? -> Нет ({name})")
                    cursor.execute("UPDATE system_stats SET value = value + 1 WHERE key = 'stock_failures'")
                    conn.commit()
                    self.update_analytics_view()
                    messagebox.showerror("Ошибка схемы", f"Товар '{name}' закончился на складе БД!")
                    return

            discounted_total = int(raw_total * (1 - self.discount))
            delivery_cost = self.delivery_types[self.delivery_var.get()]
            total_cost = discounted_total + delivery_cost


            self.system_log("Товар доступен? -> Да\nСбор данных о товаре...\nОбработка платежа...")
            user_balance = self.get_user_balance()
            if user_balance < total_cost:
                self.system_log("Платеж успешен? -> Нет (Недостаточно средств)")
                cursor.execute("UPDATE system_stats SET value = value + 1 WHERE key = 'payment_failures'")
                conn.commit()
                self.update_analytics_view()
                messagebox.showerror("Ошибка оплаты", f"Недостаточно средств на балансе! Требуется {total_cost:,} руб.")
                return


            cursor.execute("UPDATE profile SET balance = balance - ? WHERE id = 1", (total_cost,))


            self.system_log("Платеж успешен? -> Да\nПодтверждение заказа...")
            for product_name, count in self.cart.items():
                cursor.execute("UPDATE products SET stock = stock - ? WHERE name = ?", (count, product_name))


            self.system_log("Формирование накладной...\nПодготовка к отправке...\nОтправка товара...")

            cursor.execute("SELECT COUNT(*) FROM orders")
            invoice_number = cursor.fetchone()[0] + 5001

            invoice_text = f"НАКЛАДНАЯ №{invoice_number}\nТовары:\n"
            for product_name, count in self.cart.items():
                invoice_text += f" - {product_name}: {count} шт.\n"
            if self.discount > 0:
                invoice_text += f"Скидка по промокоду: 10%\n"
            invoice_text += f"Способ доставки: {self.delivery_var.get()} ({delivery_cost} руб.)\n"
            invoice_text += f"ИТОГО К ОПЛАТЕ: {total_cost:,} руб. СТАТУС: Оплачено\n---------------------------------------\n"


            cursor.execute("INSERT INTO orders (invoice_text) VALUES (?)", (invoice_text,))
            conn.commit()


        file_name = f"invoice_{invoice_number}.txt"
        try:
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(invoice_text)
        except Exception:
            pass

        self.balance_label.config(text=f"Ваш баланс: {self.get_user_balance():,} руб.")
        self.update_history_view()
        self.update_analytics_view()

        self.system_log("Уведомление клиента о статусе заказа...\n--- Конец ---")
        messagebox.showinfo("Успех!", "Заказ сохранен в БД и успешно отправлен!")

        self.cart.clear()
        self.discount = 0.0
        self.promo_entry.delete(0, tk.END)
        self.delivery_var.set("Самовывоз")
        self.update_cart_view()
        self.update_catalog_view()


if __name__ == "__main__":
    root = tk.Tk()
    app = MarketOrderSystem(root)
    root.mainloop()
