from improvedParser import ImprovedAvitoParser
from database import Database
from datetime import datetime
import time
import random

class AvitoTracker:
    def __init__(self, check_interval_minutes=15):
        self.db = Database()
        self.check_interval = check_interval_minutes
        self.is_running = False


    def create_search(self, query, city, price_min=None,
                      price_max=None, delivery=False, fitting=False, name=None):
        '''
        Добавление запроса и первоначальный парсинг.
        Сохраняет найденные объявления в бд (с id запроса).
        Возвр. id запроса и кол-во добавленных объявлений.
        '''
        # Сохранение запроса в БД
        search_id = self.db.add_search(
            query=query,
            city=city,
            price_min=price_min,
            price_max=price_max,
            delivery=delivery,
            fitting=fitting,
            name=name
        )
        print(f"Создан поисковый запрос с id: {search_id}")

        # Создание парсера с теми же параметрами
        parser = ImprovedAvitoParser(
            query=query,
            city=city,
            price_min=price_min,
            price_max=price_max,
            delivery=delivery,
        )
        # Полный парсинг страницы для начальной базы
        items = parser.main_parse_func()
        new_items = self.db.process_items(items, search_id)

        # Обновление времени проверки
        self.db.update_last_check(search_id)

        print(f"Найдено {len(items)} объявлений, новых: {len(new_items)}")
        return search_id, len(new_items)



    def check_search(self, search_id):
        '''
        Проверка одного запроса - принимает id запроса.
        Возвращает список найденных объявлений. Между вызовами 10 минут минимум.
        '''
        search = self.db.get_search_by_id(search_id)
        if not search:
            print(f"Поисковый запрос с ID {search_id} не найден")
            return []

        # Создание парсера для запроса
        parser = ImprovedAvitoParser(
            city=search['city'],
            query=search['query'],
            price_min=search['price_min'],
            price_max=search['price_max'],
            delivery=search['delivery']
        )

        # Парсинг 1-ой страницы (недавние объявления)
        items = parser.main_parse_func()
        new_items = self.db.process_items(items, search_id)

        # Обновление времени проверки
        self.db.update_last_check(search_id)

        print(f"Для '"
              f"{search['name']}' найдено {len(new_items)} новых объявлений")

        # # Показ уведомлений о новых объявлениях
        # if new_items:
        #     self._notify_new_items(name, new_items)

        return new_items

    # Проверка всех активных запросов - возвращ. новые объявления по всем
    # запросам
    def check_all_active_searches(self):
        active_searches = self.db.get_active_searches()
        all_new_items = []

        for search in active_searches:
            search_id = search[0]
            # Проверяем только новые объявления (1 страница)
            new_items = self.check_search(search_id)
            all_new_items.extend(new_items)

        return all_new_items