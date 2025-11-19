import requests
import time
import random
from bs4 import BeautifulSoup


class AvitoParser:
    def __init__(self):
        self.session = requests.Session()
        self.set_headers()

    def set_headers(self):
        """Устанавливаем типичные заголовки Chrome на Windows"""
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive', # будут отправлены ещё запросы
            'Upgrade-Insecure-Requests': '1', # перевод на HTTPS
        }

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

    # основная функция, принимающая URL
    def parse_search_results(self, search_url, max_pages=3):
        for page in range(1, max_pages + 1):
            # Формируем URL для каждой страницы
            page_url = f"{search_url}&p={page}"

            # Делаем запрос со случайной задержкой
            html = self.get_page(page_url, delay=random.uniform(5, 10))

            if html:
                # Парсим объявления с этой страницы
                items = self.extract_items(html)
            # Случайная задержка между страницами
            time.sleep(random.uniform(2, 5))

    # функция извлечения данных со страницы

    def extract_items(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        items = []

        # Находим ВСЕ контейнеры объявлений
        item_containers = soup.find_all('div', {'data-marker': 'item'})

        for container in item_containers:
            # Извлекаем данные из каждого контейнера
            item_data = self.extract_item_data(container)
            if item_data:
                items.append(item_data)

        return items

    # функция извлечения данных из одного контейнера
    def extract_item_data(self, container):
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
    parser = AvitoParser()
    # Тестовая поисковая выдача
    test_search_url = "https://www.avito.ru/sankt-peterburg?cd=1&p=1&q=куртка+jnby"

    html = parser.get_page(test_search_url)

    if html:
        items = parser.extract_items(html)
        print(f"Найдено {len(items)} объявлений")
        for item in items[:5]:  # Покажем первые 3
            print(item)