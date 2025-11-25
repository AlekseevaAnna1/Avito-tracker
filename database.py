import sqlite3

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
