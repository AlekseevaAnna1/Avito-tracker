import sqlite3
from datetime import datetime, timezone, timedelta
import re


class Database:
    # Константа часового пояса
    MSK_TIMEZONE = timezone(timedelta(hours=3))

    def __init__(self, db_path="avito_tracker_test.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        # Инициализация базы данных и таблиц
        conn = sqlite3.connect(self.db_path)  # Файл создается автоматически
        cursor = conn.cursor()

        """Таблицы searches (поисковые запросы) и items (найденные объявления)"""
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                query TEXT NOT NULL,
                city TEXT NOT NULL,
                price_min INTEGER,
                price_max INTEGER,
                delivery BOOLEAN DEFAULT 0,
                fitting BOOLEAN DEFAULT 0,  
                is_active BOOLEAN DEFAULT 1,
                created_date TIMESTAMP,
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
                link TEXT NOT NULL,   
                normalized_link TEXT UNIQUE,  
                date TEXT,
                location TEXT,
                delivery BOOLEAN DEFAULT 0,
                fitting BOOLEAN DEFAULT 0,
                description TEXT,
                found_date TIMESTAMP,
                is_new BOOLEAN DEFAULT 1,
                FOREIGN KEY (search_id) REFERENCES searches (id) ON DELETE 
                CASCADE
            )
        ''')
        conn.commit()
        conn.close()

    def _normalize_avito_url(self, url):
        """
        Извлекает базовую часть ссылки Avito до параметров.
        Пример:
        Вход: https://www.avito.ru/.../puhovik_nume_s_vishnyami_s_7812646131?context=...
        Выход: https://www.avito.ru/sankt-peterburg/odezhda_obuv_aksessuary/puhovik_nume_s_vishnyami_s_7812646131
        """
        # Паттерн ищет ID объявления (цифры перед ? или в конце строки)
        pattern = r'(https://www\.avito\.ru/[^?]+?_(\d+))(?:\?|$)'

        match = re.search(pattern, url)
        if match:
            # Возвращаем всю ссылку до ID + сам ID
            return match.group(1)

        # Если не нашли паттерн, возвращаем оригинал
        return url.split('?')[0]  # Отрезаем параметры

    def _get_current_time_msk(self):
        """Вспомогательный метод для получения текущего времени в MSK"""
        return datetime.now(self.MSK_TIMEZONE).strftime('%Y-%m-%d %H:%M:%S')

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

        # Создаем метку времени
        current_time = self._get_current_time_msk()

        # Вставка данных в таблицу searches
        cursor.execute('''
            INSERT INTO searches 
            (name, query, city, price_min, price_max, delivery, fitting, 
            created_date, last_check)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (name, query, city, price_min, price_max, delivery, fitting,
              current_time, current_time))

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
        Возвращает id, если объявление новое, иначе None"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        current_time = self._get_current_time_msk()

        # Сокращение ссылки перед сохранением
        normalized_link = self._normalize_avito_url(item['link'])

        try:
            cursor.execute('''
                INSERT OR IGNORE INTO items 
                (search_id, title, price, image_url, link, normalized_link, 
                date, 
                location, delivery, fitting, description, found_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (search_id,
                  item['title'],
                  item['price'],
                  item['image_url'],
                  item['link'],  # Оригинальная ссылка (с параметрами)
                  normalized_link,  # Должна быть уникальна
                  item['date'],
                  item['location'],
                  item['delivery'],
                  item['fitting'],
                  item['description'],
                  current_time))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError as e:
            # Этот блок сработает, если будет конфликт по normalized_link
            print(f"Объявление уже существует: {normalized_link}")
            return None
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
        """Получение запроса по id в виде кортежа"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM searches WHERE id = ?', (search_id,))
        search = cursor.fetchone()

        conn.close()
        return search

    def get_item_by_id(self, item_id):
        """Получение объявления по id в виде кортежа"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM items WHERE id = ?', (item_id,))
        item = cursor.fetchone()
        conn.close()
        return item

    def get_active_searches(self):
        """Получает список всех активных поисковых запросов."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT s.*, COUNT(i.id) as items_count
            FROM searches s
            LEFT JOIN items i ON s.id = i.search_id
            GROUP BY s.id
            ORDER BY s.last_check DESC
        ''')
        searches = cursor.fetchall()
        conn.close()
        return searches

    def get_items_by_search_id(self, search_id):
        """Получает все объявления для указанного поискового запроса."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM items 
            WHERE search_id = ? 
            ORDER BY found_date DESC
        ''', (search_id,))
        items = cursor.fetchall()
        conn.close()
        return items

    def mark_items_as_viewed(self, search_id):
        """Помечает все объявления в поисковом запросе как просмотренные."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE items 
            SET is_new = 0 
            WHERE search_id = ? AND is_new = 1
        ''', (search_id,))
        conn.commit()
        conn.close()

    def delete_item(self, item_id):
        """Удаляет объявление по его ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM items WHERE id = ?', (item_id,))
        conn.commit()
        conn.close()

    def get_new_items_count(self, search_id):
        """Возвращает количество непросмотренных объявлений для запроса"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM items 
            WHERE search_id = ? AND is_new = 1
        ''', (search_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count


    def get_total_count(self, search_id):
        """Возвращает количество всех объявлений для запроса"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM items 
            WHERE search_id = ?
        ''', (search_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def update_last_check(self, search_id):
        """Время последней проверки (устанавливается текущее) конкретного
        запроса
        (по id)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Создаем метку времени с учетом часового пояса MSK (UTC+3)
        current_time = self._get_current_time_msk()
        cursor.execute('''
            UPDATE searches
            SET last_check = ?
            WHERE id = ?
        ''', (current_time, search_id))
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
        history = []
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

    def mark_item_as_viewed(self, item_id):
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
