from improvedParser import ImprovedAvitoParser
from database import Database


class AvitoTracker:
    def __init__(self, check_interval_minutes=15):
        self.db = Database()
        self.check_interval = check_interval_minutes
        self.is_running = False

    '''
    Добавление запроса и первоначальный парсинг.
    Сохраняет найденные объявления в бд (с id запроса).
    Возвр. id запроса и кол-во добавленных объявлений.
    '''

    def create_search(self, name, query, city, **kwargs):

        # Сохраняем запрос в БД
        search_id = self.db.add_search(
            name=name,
            query=query,
            city=city,
            **kwargs
        )
        print(f"Создан поисковый запрос с id: {search_id}")

        # Создание парсера с теми же параметрами
        parser = ImprovedAvitoParser(
            city=city,
            query=query,
            **kwargs
        )
        # Полный парсинг страницы для начальной базы
        items = parser.main_parse_func(max_pages=1)
        new_item_count = 0
        for item in items:
            self.db.save_item(item, search_id)
            new_item_count += 1
        # print(f"Найдено {len(items)} объявлений, новых: {new_item_count}")
        return search_id, new_item_count

    # Проверка всех активных запросов - вывод новых объявлений
    # def check_active_searches(self):
    #     active_searches = self.db.get_active_searches()
    #     all_new_items = []
    #
    #     for search in active_searches:
    #         print(f"Проверяем запрос: {search['name']}")
    #
    #         search_params = {
    #             'city': search['city'],
    #             'query': search['query'],
    #             'price_min': search['price_min'],
    #             'price_max': search['price_max'],
    #             'delivery': search['delivery']
    #         }
    #
    #         # Проверяем только новые объявления (1 страница)
    #         new_items = self.check_search(search_params, max_pages=1)
    #
    #         # Сохраняем только новые
    #         for item in new_items:
    #             if self.db.save_item(item, search['id']):
    #                 all_new_items.append(item)
    #
    #         # Обновляем время последней проверки
    #         self.db.update_last_check(search['id'])
    #
    #     return all_new_items

    '''
    Проверка одного запроса - принимает id запроса.
    Возвращает список найденных объявлений. Между вызовами 10 минут минимум.
    '''

    # Проверка одного запроса - вывод новых объявлений
    def check_search(self, search_id):
        search = self.db.get_search_by_id(search_id)
        if not search:
            # print(f"Поисковый запрос с ID {search_id} не найден")
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
        new_items = []
        items = parser.main_parse_func()
        for item in items:
            if self.db.save_item(item, search_id):
                new_items.append(item)
        self.db.update_last_check(search_id)
        print(f"Для '{name}' найдено {len(new_items)} новых объявлений")

        # # Показ уведомлений о новых объявлениях
        # if new_items:
        #     self._notify_about_new_items(name, new_items)

        return new_items
