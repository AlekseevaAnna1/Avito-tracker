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
                interval_minutes INTEGER DEFAULT 30,
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
                FOREIGN KEY (search_id) REFERENCES searches (id)
            )
        ''')

        conn.commit()
        conn.close()

    # Добавление нового поискового запроса
    def add_search(self, name, query, city, price_min=None, price_max=None,
                   delivery=False, fitting=False, interval_minutes=30):
        # Добавление нового поискового запроса
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Вставка данных в таблицу searches
        cursor.execute('''
            INSERT INTO searches 
            (name, query, city, price_min, price_max, delivery, fitting, interval_minutes, last_check)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, query, city, price_min, price_max, delivery, fitting, interval_minutes, datetime.now()))

        search_id = cursor.lastrowid  # Получение id только что добав. запроса
        conn.commit()
        conn.close()
        return search_id

    # Получение всех активных поисковых запросов
    def get_active_searches(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM searches WHERE is_active = 1
        ''')

        searches = cursor.fetchall()
        conn.close()

        return searches

    # Добавление найденного объявления (нового)
    def add_item(self, search_id, title, price, link, date=None, location=None,
                 delivery=False, fitting=False, image_url=None):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT OR IGNORE INTO items 
                (search_id, title, price, link, date, location, delivery, fitting, image_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
            search_id, title, price, link, date, location, delivery, fitting,
            image_url))

            # Проверяем, была ли вставлена новая запись
            is_new = cursor.rowcount > 0

            conn.commit()
            return is_new

        except sqlite3.IntegrityError:
            # Ограничение UNIQUE (поле link)
            return False
        finally:
            conn.close()

    # Проверка существования объявления с данной ссылкой
    def item_exists(self, link):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM items WHERE link = ?', (link,))
        exists = cursor.fetchone() is not None

        conn.close()
        return exists

    # Получение запроса по id
    def get_search_by_id(self, search_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM searches WHERE id = ?', (search_id,))
        search = cursor.fetchone()

        conn.close()
        return search

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

