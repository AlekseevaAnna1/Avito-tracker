import tkinter as tk
from tkinter import ttk, messagebox


class AddSearchDialog(tk.Toplevel):
    """Диалоговое окно для добавления нового поискового запроса."""

    def __init__(self, parent, tracker, on_success_callback):
        super().__init__(parent)
        self.tracker = tracker
        self.on_success = on_success_callback
        self.title("Добавить новый запрос")
        self.geometry("400x350")
        self.resizable(False, False)

        # Контейнер для всего содержимого
        main_frame = ttk.Frame(self, padding="20")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Поле: Поисковый запрос (обязательное)
        ttk.Label(main_frame, text="Что ищем? ").grid(row=0, column=0,
                                                      sticky=tk.W,
                                                      pady=(0, 5))
        self.query_var = tk.StringVar()
        ttk.Entry(main_frame, textvariable=self.query_var, width=30).grid(
            row=0, column=1, sticky="we", pady=(0, 5))

        # Поле: Город (обязательное)
        ttk.Label(main_frame, text="Город/Регион: ").grid(row=1, column=0,
                                                         sticky=tk.W, pady=5)
        self.city_var = tk.StringVar()
        # Можно использовать Combobox с предустановленными городами Avito
        city_combo = ttk.Combobox(main_frame, textvariable=self.city_var,
                                  values=["sankt-peterburg", "moskva",
                                          "ekaterinburg"], state="normal")
        city_combo.grid(row=1, column=1, sticky="we", pady=5)

        # Поля: Диапазон цен (необязательные)
        price_frame = ttk.LabelFrame(main_frame, text="Диапазон цен (необяз.)",
                                     padding=10)
        price_frame.grid(row=2, column=0, columnspan=2, sticky="we",
                         pady=10)

        ttk.Label(price_frame, text="От:").grid(row=0, column=0, sticky=tk.W)
        self.price_min_var = tk.StringVar()
        ttk.Entry(price_frame, textvariable=self.price_min_var, width=15).grid(
            row=0, column=1, sticky=tk.W, padx=(5, 20))

        ttk.Label(price_frame, text="До:").grid(row=0, column=2, sticky=tk.W)
        self.price_max_var = tk.StringVar()
        ttk.Entry(price_frame, textvariable=self.price_max_var, width=15).grid(
            row=0, column=3, sticky=tk.W)

        # Чекбокс: Только с доставкой
        self.delivery_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(main_frame, text="Только товары с доставкой",
                        variable=self.delivery_var).grid(row=3, column=0,
                                                         columnspan=2,
                                                         sticky=tk.W, pady=10)

        # Кнопки действий
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=(20, 0))
        ttk.Button(button_frame, text="Отмена", command=self.destroy).pack(
            side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="Сохранить",
                   command=self._save_search).pack(side=tk.RIGHT)

        self.grab_set()  # Модальное окно

    def _save_search(self):
        """Собирает данные из формы и сохраняет запрос в БД."""
        query = self.query_var.get().strip()
        city = self.city_var.get().strip()

        if not query or not city:
            messagebox.showerror("Ошибка",
                                 "Поля 'Что ищем?' и 'Город' обязательны для заполнения.")
            return

        # Обработка цен (могут быть пустыми)
        price_min = self.price_min_var.get().strip()
        price_max = self.price_max_var.get().strip()
        price_min = int(price_min) if price_min.isdigit() else None
        price_max = int(price_max) if price_max.isdigit() else None

        delivery = self.delivery_var.get()

        # Сохранение в базу данных
        try:
            search_id = self.tracker.create_search(
                query=query,
                city=city,
                price_min=price_min,
                price_max=price_max,
                delivery=delivery
            )
            messagebox.showinfo("Успех",
                                f"Поисковый запрос добавлен (ID: {search_id})")
            self.on_success()  # Обновляем список в главном окне
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка базы данных",
                                 f"Не удалось сохранить запрос: {e}")


class DetailsWindow(tk.Toplevel):
    def __init__(self, parent, item_data):
        super().__init__(parent)
        self.title("Детали объявления")
        self.geometry("600x500")

        # Текст описания
        desc_frame = ttk.LabelFrame(self, text="Описание", padding=10)
        desc_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        text_widget = tk.Text(desc_frame, wrap=tk.WORD, height=10)
        text_widget.insert(1.0, item_data[11] or "Нет описания")
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(fill=tk.BOTH, expand=True)

        # Загрузка фото (если есть URL)
        if item_data[4]:  # image_url
            self._load_image(item_data[4])

    def _load_image(self, url):
        import threading
        threading.Thread(target=self._fetch_image, args=(url,),
                         daemon=True).start()

    def _fetch_image(self, url):
        try:
            import requests
            from PIL import Image, ImageTk
            from io import BytesIO

            response = requests.get(url, timeout=5)
            img = Image.open(BytesIO(response.content))
            img.thumbnail((400, 400))

            # Возврат в главный поток для Tkinter
            self.after(0, self._display_image, ImageTk.PhotoImage(img))
        except:
            pass

    def _display_image(self, photo):
        img_frame = ttk.LabelFrame(self, text="Изображение", padding=10)
        img_frame.pack(fill=tk.BOTH, padx=10, pady=5)
        ttk.Label(img_frame, image=photo).pack()
        self.photo = photo  # сохраняем ссылку


class SearchItemsWindow(tk.Toplevel):
    """Окно для просмотра истории объявлений по конкретному запросу."""

    def __init__(self, parent_app, db, search_id, search_name):
        super().__init__(parent_app)
        self.db = db
        self.search_id = search_id
        self.title(f"История: {search_name}")
        self.geometry("900x500")

        # Сохранение ссылки на родительское окно
        self.parent_app = parent_app

        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Таблица для отображения объявлений
        columns = ("ID", "Название", "Цена", "Дата публикации")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings",
                                 selectmode="extended")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Заголовки колонок
        self.tree.heading("ID", text="ID")
        self.tree.heading("Название", text="Название")
        self.tree.heading("Цена", text="Цена")
        self.tree.heading("Дата публикации", text="Дата публикации")

        self.tree.column("ID", width=40)
        self.tree.column("Название", width=300)
        self.tree.column("Цена", width=100)
        self.tree.column("Дата публикации", width=120)

        # Настраиваем стиль для новых объявлений
        self.tree.tag_configure('new', background='#e8f5e9')
        self.tree.tag_configure('viewed', background='white')

        # Полоса прокрутки
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL,
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Панель кнопок
        button_frame = ttk.Frame(self)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        ttk.Button(button_frame, text="Открыть ссылку",
                   command=self._open_link).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Удалить выбранное",
                   command=self._delete_selected).pack(side=tk.LEFT, padx=5)
        # ttk.Button(button_frame, text="Пометить все как прочитанные",
        #            command=self._mark_as_read).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Обновить",
                   command=self._load_items).pack(side=tk.LEFT, padx=5)

        # Загрузка данных
        self._load_items()

        # При двойном клике по строке открывается ссылка
        self.tree.bind("<Double-1>", lambda event: self._open_link())

        # При клике ПКМ открывается контекстное меню
        self.tree.bind('<Button-3>', self._on_right_click)

    def _load_items(self):
        """Загружает объявления из базы данных и отображает их в таблице."""
        # Очистка текущих данных
        for item in self.tree.get_children():  # Возвр. список id всех строк
            self.tree.delete(item)

        items = self.db.get_items_by_search_id(self.search_id)
        for item in items:
            # Правильные индексы согласно структуре БД
            item_id = item[0]
            title = item[2]
            price = item[3]
            link = item[5]
            date = item[7]
            delivery = item[9]
            fitting = item[10]
            is_new = item[13]

            # Определяем тег в зависимости от статуса + ссылка
            tags = ('new', link) if is_new else ('viewed', link)

            # Добавление строки в таблицу
            self.tree.insert("", tk.END,
                             values=(
                                 item_id, title, price, date,
                                 fitting, delivery),
                             tags=tags)

        # Пометка всех загруженных объявлений is_new = 0
        self.db.mark_items_as_viewed(self.search_id)

    def _mark_single_as_read(self, item_id):
        """Помечает одно объявление как прочитанное."""

        # ID объявления из первого столбца
        item_db_id = self.tree.item(item_id)['values'][0]
        self.db.mark_item_as_viewed(item_db_id)

        # Преобразование кортежа в список для изменения тегов
        current_tags = list(self.tree.item(item_id, 'tags'))

        # Удаление 'new' из тегов
        if 'new' in current_tags:
            current_tags.remove('new')
            # Добавление 'viewed'
            if 'viewed' not in current_tags:
                current_tags.append('viewed')
            self.tree.item(item_id, tags=tuple(current_tags))

    def _open_link(self):
        """Открывает ссылку выбранного объявления в браузере."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Выберите объявление из списка.")
            return
        '''
        Метод self.tree.item(selected_item[0]) возвращает словарь с данными 
        строки.
        selected_item[0] возвращает id  строки в Treeview
        '''
        tags = self.tree.item(selected_item[0])['tags']
        link = tags[-1]

        import webbrowser
        webbrowser.open(link)
        self._mark_single_as_read(selected_item[0])

    def _delete_selected(self):
        """Удаляет выбранные объявления из базы данных."""
        selected_items = self.tree.selection()
        if not selected_items:
            return
        for item in selected_items:
            item_id = self.tree.item(item)['values'][0]
            self.db.delete_item(item_id)
        self._load_items()  # Перезагружаем список

        if hasattr(self.parent_app, '_load_searches'):
            self.parent_app._load_searches()

    # Метод для контекстного меню
    def _on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Открыть ссылку", command=self._open_link)
            menu.add_command(label="Подробности", command=self._show_details)
            menu.tk_popup(event.x_root, event.y_root)

    def _show_details(self):
        selected = self.tree.selection()[0]
        item_id = self.tree.item(selected)['values'][0]
        item_data = self.db.get_item_by_id(item_id)  # Новый метод в Database

        # Окно с описанием и фото
        DetailsWindow(self, item_data)


class AvitoTrackerApp:
    """Главное окно приложения."""

    def __init__(self, root, db, scheduler, tracker):
        self.root = root
        self.db = db
        self.scheduler = scheduler
        self.tracker = tracker
        self.root.title("Avito Tracker")
        self.root.geometry("800x500")

        # Верхняя панель с кнопкой "Добавить запрос"
        toolbar = ttk.Frame(self.root, padding="10")
        toolbar.pack(fill=tk.X)
        ttk.Button(toolbar, text="+ Добавить запрос",
                   command=self._open_add_dialog).pack(side=tk.LEFT)

        # Кнопки управления фоновой проверкой
        ttk.Button(toolbar, text="▶️ Запустить проверку",
                   command=self.scheduler.start).pack(side=tk.RIGHT, padx=5)
        ttk.Button(toolbar, text="⏸️ Остановить проверку",
                   command=self.scheduler.stop).pack(side=tk.RIGHT)

        # Основная область: список активных запросов
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        columns = (
            "ID", "Название запроса", "Город", "Всего",
            "Новые", "Последняя проверка")
        self.tree = ttk.Treeview(main_frame, columns=columns, show="headings",
                                 selectmode="browse")
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Настраиваем заголовки
        for col in columns:
            self.tree.heading(col, text=col)

        # Настраиваем ширину колонок
        self.tree.column("ID", width=40, anchor=tk.CENTER)
        self.tree.column("Название запроса", width=200)
        self.tree.column("Город", width=100)
        self.tree.column("Всего", width=60, anchor=tk.CENTER)
        self.tree.column("Новые", width=60, anchor=tk.CENTER)
        self.tree.column("Последняя проверка", width=150, anchor=tk.CENTER)

        # Строка состояния
        self.status_bar = ttk.Frame(root, relief=tk.SUNKEN, height=25)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_label = ttk.Label(self.status_bar, text="Готов")
        self.status_label.pack(side=tk.LEFT, padx=5)

        # Индикатор состояния проверки
        self.checking_indicator = ttk.Label(
            self.status_bar,
            text="●",
            foreground="gray",
            font=("Arial", 10, "bold")
        )
        self.checking_indicator.pack(side=tk.LEFT, padx=2)

        # Полоса прокрутки
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL,
                                  command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # При двойном клике по запросу открываем его историю
        self.tree.bind("<Double-1>", self._open_search_history)

        # Загрузка активных запросов при старте
        self._load_searches()

    def _load_searches(self):
        """Загружает список активных поисковых запросов из БД."""
        # Очищение текущих данных из таблицы
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Получение запросов из бд
        searches = self.db.get_active_searches()

        for search in searches:
            search_id = search[0]  # id
            name = search[1]  # name
            city = search[3]  # city
            last_check = search[10]  # last_check

            total_count = self.db.get_total_count(search_id)

            # Количество новых объявлений
            new_count = self.db.get_new_items_count(search_id)

            if last_check:
                try:
                    from datetime import datetime
                    last_dt = datetime.strptime(last_check,
                                                '%Y-%m-%d %H:%M:%S')
                    # Только время
                    last_check_str = last_dt.strftime('%H:%M:%S')

                    # Дата и время
                    # last_check_str = last_dt.strftime('%d.%m.%Y %H:%M:%S')
                except:
                    last_check_str = last_check
            else:
                last_check_str = "Никогда"

            item_id = self.tree.insert("", tk.END, values=(
                search_id, name, city, total_count, new_count, last_check_str
            ))

            # Выделение цветом строк с новыми объявлениями
            if new_count > 0:
                self.tree.tag_configure('has_new', background='#f0fff0')
                self.tree.item(item_id, tags=('has_new',))

    # Реализация колбэков
    def on_check_start(self):
        """Вызывается при начале фоновой проверки"""
        self.status_label.config(
            text="Идёт поиск новых объявлений...",
            foreground="orange"
        )
        self.checking_indicator.config(foreground="orange")

    def on_check_complete(self, new_items_total_count):
        """Вызывается при завершении фоновой проверки"""
        # Обновление списка запросов
        self._load_searches()

        # Обновление строки состояния
        if new_items_total_count > 0:
            self.status_label.config(
                text=f"Проверка завершена. Найдено {new_items_total_count} новых объявлений",
                foreground="green"
            )
            self.checking_indicator.config(foreground="green")

        else:
            self.status_label.config(
                text="Проверка завершена. Новых объявлений не найдено",
                foreground="black"
            )
            self.checking_indicator.config(foreground="gray")

        # Через 5 секунд возвращается обычный статус
        self.root.after(5000, self._reset_status)

    def _reset_status(self):
        """Сбрасывает строку статуса в обычное состояние"""
        # Проверяем, не началась ли новая проверка
        if not self.scheduler.is_running:
            self.status_label.config(text="Готов", foreground="black")
            self.checking_indicator.config(foreground="gray")

    def _open_add_dialog(self):
        """Открывает диалог добавления нового запроса."""
        AddSearchDialog(self.root, self.tracker, self._load_searches)

    def _open_search_history(self, event):
        """Открывает окно истории для выбранного поискового запроса."""
        selected_item = self.tree.selection()
        if not selected_item:
            return
        search_data = self.tree.item(selected_item[0])['values']
        search_id, search_name = search_data[0], search_data[1]
        SearchItemsWindow(self.root, self.db, search_id, search_name)
