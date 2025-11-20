import requests
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import quote_plus


class AvitoParser:
    def __init__(self, city, query, price_min=None, price_max=None, delivery=False, fitting=False):
        self.city = city
        self.query = query
        self.price_min = price_min
        self.price_max = price_max
        self.delivery = delivery
        self.session = requests.Session()
        self.set_headers()

    # Формирование ссылки на основе запроса
    def build_search_url(self, page=1):
        """Строим URL для поиска на основе параметров"""
        # Базовый URL
        base_url = f"https://www.avito.ru/{self.city}/lichnye_veschi"

        encoded_query = quote_plus(self.query)
        # Параметр s отвечает за сортировку по дате
        params = [f"q={encoded_query}", f"s=104"]
        # # Ценовой фильтр (закодированный)
        # if self.price_min is not None and self.price_max is not None:
        #     price_filter = self.encode_price_filter(self.price_min, self.price_max)
        #     if price_filter:
        #         params.append(f"f={price_filter}")

        # Цены (если указаны)
        if self.price_min is not None:
            params.append(f"pmin={self.price_min}")
        if self.price_max is not None:
            params.append(f"pmax={self.price_max}")

        if self.delivery:
            params.append("d=1")

        # Номер страницы
        if page > 1:
            params.append(f"p={page}")

        search_url = f"{base_url}?{'&'.join(params)}"
        return search_url
    def set_headers(self):
        """Устанавливаем типичные заголовки Chrome на Windows"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive', # будут отправлены ещё запросы
            'Upgrade-Insecure-Requests': '1' # перевод на HTTPS
        })

    def get_page(self, url, delay=5):
        """Получаем страницу с со случайной задержкой"""
        print(f"Ждем {delay} секунд перед запросом...")
        time.sleep(delay + random.uniform(0, 2))

        try:
            response = self.session.get(url, timeout=10)

            if response.status_code == 200:
                print("Успешно получили страницу!")
                return response.text
            else:
                print(f"Ошибка: статус код {response.status_code}")
                return None

        except Exception as e:
            print(f"Ошибка при запросе: {e}")
            return None

    """Проверяем новые объявления на первой странице"""

    def check_new_items(self):
        print("Проверяем новые объявления...")
        search_url = self.build_search_url(page=1)
        html = self.get_page(search_url, delay=random.uniform(5, 10))

        if html:
            new_items = self.extract_items(html)
            print(f"Найдено {len(new_items)} объявлений на первой странице")
            return new_items
        else:
            print("Не удалось проверить новые объявления")
            return []

    """Полный парсинг при создании нового поискового запроса"""

    def initial_full_parse(self, max_pages=3):
        print("Выполняем первоначальный полный парсинг...")
        return self.parse_search_results(max_pages)

    # Парсинг нескольких страниц
    def parse_search_results(self, max_pages=3):
        all_items = []

        for page in range(1, max_pages + 1):
            # Формируем URL для каждой страницы
            page_url = self.build_search_url(page)

            # Делаем запрос со случайной задержкой
            html = self.get_page(page_url, delay=random.uniform(5, 10))

            if html:
                # Парсим объявления с этой страницы
                items = self.extract_items(html)
                all_items.extend(items)
                print(f"На странице {page} найдено {len(items)} объявлений")
            else:
                print(f"Не удалось получить страницу {page}")
            # Случайная задержка между страницами
            time.sleep(random.uniform(2, 5))

    # Функция извлечения данных со страницы
    def extract_items(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        items = []

        # Находим ВСЕ контейнеры объявлений
        item_containers = soup.find_all('div', {'data-marker': 'item'})

        for container in item_containers:
            # Извлекаем данные из каждого контейнера
            item_data = self.parse_item(container)
            if item_data:
                items.append(item_data)
        return items

    # Функция извлечения данных из одного контейнера
    def parse_item(self, container):
        try:
            # 1) Название и ссылка
            title_elem = container.find('a', {'data-marker': 'item-title'})
            title = title_elem.text.strip() if title_elem else None
            link = "https://www.avito.ru" + title_elem['href'] if title_elem else None

            # 2) Цена
            # Ищем любой элемент с data-marker="item-price" независимо от тега
            price_container = container.find(attrs={'data-marker': 'item-price'})
            if price_container:
                # Поиск meta-тега с itemprop="price"
                meta_elem = price_container.find('meta', {'itemprop': 'price'})
                if meta_elem and meta_elem.get('content'):
                    price = meta_elem['content']

            # Первое фото: ищем тег <img itemprop="image">
            image_container = container.find('img', {'itemprop': 'image'})
            image_url = image_container.get('src') if image_container else None
            # Если фото не найдено, можно использовать заглушку
            if not image_url:
                image_url = "No image"
            # 3) Дата публикации
            date_elem = container.find(attrs={'data-marker': 'item-date'})
            date = date_elem.text.strip() if date_elem else None

            # 4) Местоположение товара
            location_elem = container.find(attrs={'data-marker': 'item-location'})
            location = location_elem.text.strip() if location_elem else None
            # 5) Дополнительные параметры (доставка, примерка)
            extra_elem = container.find('div', {'class': 'iva-item-listMiddleBlock-W7qtU'})
            if extra_elem and "Доставка" in extra_elem.text:
                delivery = True
            else:
                delivery = False

            if extra_elem and "Можно примерить" in extra_elem.text:
                fitting = True
            else:
                fitting = False
            return {
                'title': title,
                'price': price + " р.",
                'image_url': image_url,
                'link': link,
                'date': date,
                'delivery': delivery,
                'location': location,
                'fitting': fitting
            }

        except Exception as e:
            print(f"Ошибка при парсинге объявления: {e}")
            return None


if __name__ == "__main__":

    parser = AvitoParser(
        city="sankt-peterburg",
        query="куртка",
        price_min=1000,
        price_max=5000,
        delivery=True,
    )

    # Тестируем построение URL
    print("Построенный URL:", parser.build_search_url())

    # Проверяем новые объявления
    new_items = parser.check_new_items()

    print(f"Найдено {len(new_items)} объявлений")
    for i, item in enumerate(new_items[:3], 1):
        print(f"\n--- Объявление {i} ---")
        for key, value in item.items():
            print(f"{key}: {value}")
