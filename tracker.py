from improvedParser import ImprovedAvitoParser
from database import Database
import notification as my_notifications


class AvitoTracker:
    def __init__(self, db, check_interval_minutes=15):
        self.db = db
        self.check_interval = check_interval_minutes
        self.is_running = False

    def create_search(self, query, city, price_min=None,
                      price_max=None, delivery=False, fitting=False,
                      name=None):
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
        items = parser.main_parse_func(headless=True)
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

        # Распаковка кортежа (обращаемся по индексам)
        # Порядок колонок в таблице searches:
        # 0: id, 1: name, 2: query, 3: city, 4: price_min, 5: price_max,
        # 6: delivery, 7: fitting, 8: is_active, 9: created_date, 10: last_check
        search_name = search[1]
        # Создание парсера для запроса
        try:
            parser = ImprovedAvitoParser(
                city=search[3],
                query=search[2],
                price_min=search[4],
                price_max=search[5],
                delivery=bool(search[6])
            )

            # Парсинг 1-ой страницы (недавние объявления)
            items = parser.main_parse_func(headless=True)
            new_items = self.db.process_items(items, search_id)

            # Обновление времени проверки
            self.db.update_last_check(search_id)

            print(f"Для '"
                  f"{search_name}' найдено {len(new_items)} новых объявлений")

            # # Показ уведомлений о новых объявлениях
            if new_items:
                my_notifications.notify_new_items(search_name, new_items)
            return new_items

        except Exception as e:
            error_msg = f"Ошибка при проверке запроса '{search_name}': {str(e)}"
            print(f"{error_msg}")
            # notification.notify_error(error_msg, search_name)
            return []

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


if __name__ == "__main__":
    tracker = AvitoTracker()
    # search_id1, _ = tracker.create_search(
    #     query="Куртка jnby женская",
    #     city="sankt-peterburg", price_max=10000,
    #     delivery=True
    # )
    # search_id2, _ = tracker.create_search(
    #     query="Джинсы levis женские",
    #     city="sankt-peterburg",
    #     price_min=1000,
    #     price_max=7000
    # )
    #
    # search_id3, _ = tracker.create_search(
    #     query="Сапоги кожаные черные",
    #     city="sankt-peterburg", price_min=100, price_max=5000,
    # )

    print("\n--- Все активные запросы из БД ---")
    active_searches = tracker.db.get_active_searches()

    for search in active_searches:
        id = search[0]
        name = search[1]
        print(f"ID запроса: {id} | название: {name}")

    print("\n--- Проверка всех активных запросов ---")
    all_new_items = tracker.check_all_active_searches()
    # new_items = tracker.check_search(search_id5)
    print(f"Всего новых объявлений по всем запросам: {len(all_new_items)}")