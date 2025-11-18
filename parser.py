# import requests  # получать html
# import time
# import random
#
#
# def delayed_request(url, headers, delay=5):
#     """Делаем запрос с задержкой"""
#     time.sleep(delay + random.uniform(0, 2))  # случайная задержка 5-7 секунд
#     # Используем сессию для сохранения куки
#     session = requests.Session()
#     session.headers.update(headers)
#     return session.get(url, timeout=10)
#
#
# url = 'https://www.avito.ru/sankt-peterburg/odezhda_obuv_aksessuary/yubka_v_kletku_midi_s-m_7738326443?context=H4sIAAAAAAAA_wEmANn_YToxOntzOjE6IngiO3M6MTY6Iklhb2o3VEM1U0NZT21yVGkiO30XAyvwJgAAAA'
#
# headers = {
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
#     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
#     'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
#     'Accept-Encoding': 'gzip, deflate, br',
#     'Connection': 'keep-alive',
#     'Upgrade-Insecure-Requests': '1',
#     'Sec-Fetch-Dest': 'document',
#     'Sec-Fetch-Mode': 'navigate',
#     'Sec-Fetch-Site': 'none',
#     'Cache-Control': 'max-age=0',
# }
# try:
#     response = delayed_request(url, headers)
#     print(f"Статус код: {response.status_code}")
#     print(f"Кодировка: {response.encoding}")
#     print("Первые 1000 символов HTML:")
#     print(response.text[:1000])
# except Exception as e:
#     print(f'Ошибка: {e}')


import requests
import time
import random
from bs4 import BeautifulSoup


class AvitoParser:
    def __init__(self):
        self.session = requests.Session()
        self.set_headers()

    def set_headers(self):
        """Устанавливаем реалистичные заголовки"""
        self.session.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }

    def get_page(self, url, delay=5):
        """Получаем страницу с задержкой"""
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


# Тестируем
if __name__ == "__main__":
    parser = AvitoParser()

    # Простая тестовая страница (главная Avito)
    test_url = "https://www.avito.ru/"

    html = parser.get_page(test_url, delay=10)  # Большая задержка для теста

    if html:
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.find('title')
        print(f"Заголовок страницы: {title.text if title else 'Не найден'}")
    else:
        print("Не удалось получить страницу")