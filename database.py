import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path="avito_tracker.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        # Инициализация базы данных и таблиц
        conn = sqlite3.connect(self.db_path)  # Файл создается автоматически
        cursor = conn.cursor()

        '''
        Таблицы searches (поисковые запросы) и items (найденные объявления)
        '''
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                query TEXT NOT NULL,
                city TEXT NOT NULL,
                price_min INTEGER,
                price_max INTEGER,
                delivery BOOLEAN DEFAULT 0,
                fitting BOOLEAN DEFAULT 0,  # Будет реализовано в будущем
                is_active BOOLEAN DEFAULT 1,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_check TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_id INTEGER,
                title TEXT NOT NULL,
                price TEXT,
                image_url TEXT,
                link TEXT UNIQUE,
                date TEXT,
                location TEXT,
                delivery BOOLEAN DEFAULT 0,
                fitting BOOLEAN DEFAULT 0,
                found_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_new BOOLEAN DEFAULT 1,
                FOREIGN KEY (search_id) REFERENCES searches (id) ON DELETE 
                CASCADE
            )
        ''')
        conn.commit()
        conn.close()



    def add_search(self, query, city, price_min=None, price_max=None,
                   delivery=False, fitting=False, name=None):
        """Добавление нового поискового запроса, возвращает уникальный id
        запроса"""
        # Генерация названия на основе запроса
        if name is None:
            first_query_words = ' '.join(query.split()[:3])
            name = first_query_words if len(first_query_words) < 25 else \
                first_query_words[:-3] + '...'

        # Добавление нового поискового запроса
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Вставка данных в таблицу searches
        cursor.execute('''
            INSERT INTO searches 
            (name, query, city, price_min, price_max, delivery, fitting,  last_check)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, query, city, price_min, price_max, delivery, fitting))

        search_id = cursor.lastrowid  # Получение id только что добав. запроса
        conn.commit()
        conn.close()
        return search_id

    def get_active_searches(self):
        """Получение всех активных поисковых запросов"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM searches WHERE is_active = 1
        ''')

        searches = cursor.fetchall()
        conn.close()

        return searches

    def add_item(self, item, search_id):
        """Добавление найденного объявления (нового)
        Возвращает true/false - новое ли объявление"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT OR IGNORE INTO items 
                (search_id, title, price, link, date, location, delivery, 
                fitting, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                search_id,
                item.get('title'),
                item.get('price'),
                item.get('link'),
                item.get('date'),
                item.get('location'),
                item.get('delivery', False),
                item.get('fitting', False),
                item.get('image_url')
            ))

            # Проверяем, была ли вставлена новая запись
            is_new = cursor.rowcount > 0

            conn.commit()
            return is_new

        except sqlite3.IntegrityError:
            # Ограничение UNIQUE (уникальное поле link)
            return False
        finally:
            conn.close()

    def process_items(self, items, search_id):
        """
        Обрабатывает список объявлений: сохраняет только новые
        Возвращает список новых объявлений
        """
        new_items_list = []

        for item in items:
            if self.add_item(item, search_id):
                new_items_list.append(item)

        return new_items_list

    # def item_exists(self, link):
    #     """Проверка существования объявления с данной ссылкой в бд"""
    #     conn = sqlite3.connect(self.db_path)
    #     cursor = conn.cursor()
    #
    #     cursor.execute('SELECT id FROM items WHERE link = ?', (link,))
    #     exists = cursor.fetchone() is not None
    #
    #     conn.close()
    #     return exists

    def get_search_by_id(self, search_id):
        """Получение запроса по id"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM searches WHERE id = ?', (search_id,))
        search = cursor.fetchone()

        conn.close()
        return search

    def update_last_check(self, search_id):
        """Время последней проверки (устанавливается текущее) конкретного
        запроса
        (по id)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE searches
            SET last_check = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (search_id,))
        conn.commit()
        conn.close()

    def toggle_search_active(self, search_id, is_active):
        """Активация/деактивация запроса"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            UPDATE searches 
            SET is_active = ?
            WHERE id = ?
        ''', (is_active, search_id))

        conn.commit()
        conn.close()

    def get_search_history(self, search_id, limit=30):
        """Просмотр истории объявлений по конкретному запросу"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT title, price, link, date, location, delivery, fitting, 
            found_date
            FROM items
            WHERE search_id = ?
            ORDER BY found_date DESC
            LIMIT ?
        ''', (search_id, limit))
        items = cursor.fetchall()
        conn.close()

        # Преобразование в список словарей
        history=[]
        for item in items:
            history.append({
                'title': item[0],
                'price': item[1],
                'link': item[2],
                'date': item[3],
                'location': item[4],
                'delivery': bool(item[5]),
                'fitting': bool(item[6]),
                'found_date': item[7]
            })
        return history

    def get_search_stats(self, search_id):
        """
        Получение статистики для поискового запроса:
        - кол-во найденных объявлений
        - кол-во новых объялений
        - дата последней проверки
        """
        # Общее количество объявлений
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM items WHERE search_id = ?',
                       (search_id,))
        total_count = cursor.fetchone()[0]

        # Количество новых объявлений
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM items WHERE search_id = ? '
                       'AND is_new = 1',
                       (search_id,))
        new_count = cursor.fetchone()[0]

        # Дата последней проверки
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT last_check FROM searches WHERE id = ? ',
                       (search_id,))
        last_check = cursor.fetchone()[0]

        conn.close()
        return {
            'total_items': total_count,
            'new_items': new_count,
            'last_check': last_check
        }

    def mark_item_as_seen(self, item_id):
        """Помечает объявление как просмотренное (не новое)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE items
            SET is_new = 0
            WHERE id = ?
            ''', (item_id,))
        conn.commit()
        conn.close()

# Тестирование
if __name__ == "__main__":
    db = Database()

    # Тест добавления поискового запроса
    search_id = db.add_search(
        name="Тестовый запрос",
        query="куртка",
        city="sankt-peterburg",
        price_min=1000,
        price_max=5000,
        delivery=True
    )
    print(f"Добавлен запрос с ID: {search_id}")

    # Тест получения активных запросов
    searches = db.get_active_searches()
    print(f"Активные запросы: {searches}")
