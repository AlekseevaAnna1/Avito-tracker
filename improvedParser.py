import time
import random
import os
from urllib.parse import quote_plus
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains  # Цепочки действий
import undetected_chromedriver as uc
from webdriver_manager.chrome import ChromeDriverManager


class ImprovedAvitoParser:
    def __init__(self, city, query, price_min=None, price_max=None,
                 delivery=False):
        self.city = city
        self.query = query
        self.price_min = price_min
        self.price_max = price_max
        self.delivery = delivery
        self.driver = None

    # Возвращает driver/None
    def _setup_undetected_driver(self, headless=True):
        # Обход reCAPTCHA (эмуляция реального браузера)
        options = uc.ChromeOptions()
        if headless:
            options.add_argument('--headless=new')  # Без граф.интерфейса
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-gpu')  # Важно для headless
        else:
            options.add_argument('--start-maximized')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        # Скрываются признаки автоматизации
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')

        # Реалистичный User-Agent
        options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        # Создание пользовательского профиля
        user_data_dir = os.path.join(os.getcwd(), "avito_profile")
        if not os.path.exists(user_data_dir):
            os.makedirs(user_data_dir)

        options.add_argument(f"--user-data-dir={user_data_dir}")

        try:
            # Использование undetected-chromedriver
            driver = uc.Chrome(
                options=options,
                driver_executable_path=ChromeDriverManager().install()
            )

            # Доп. скрипты для обхода защиты (выполняется до кода
            # сайта)
            driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
                'source': '''
                    // Обход hCaptcha детекции
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });

                    // Обход QRATOR fingerprinting (кол-во плагинов)
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5]
                    });

                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['ru-RU', 'ru', 'en-US', 'en']
                    });

                    // Скрытие Chrome Automation
                    window.chrome = {
                        runtime: {},
                        loadTimes: function() {},
                        csi: function() {},
                        app: {}
                    };
                '''
            })

            return driver

        except Exception as e:
            print(f"Ошибка настройки драйвера: {e}")
            return None

    # Возвращает True/False (занимает максимум 30 с.)
    def _wait_for_captcha(self, timeout=30):
        # Ожидание и обработка капчи
        # print("Проверка наличия hCaptcha")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Проверка наличия hCaptcha iframe
                captcha_iframes = self.driver.find_elements(By.CSS_SELECTOR,
                                                            'iframe[src*="hcaptcha.com"]')
                if captcha_iframes:
                    print("Обнаружена hCaptcha, требуется ручное решение...")
                    print("Решите капчу в браузере и нажмите Enter чтобы продолжить")
                    input()
                    return True
                # Проверка наличия блокировки
                page_text = self.driver.page_source.lower()
                if any(text in page_text for text in
                       ['доступ ограничен', 'bot detected', 'automation']):
                    print("Обнаружена блокировка!")
                    return False
                # Если загрузились нормальные объявления - выходим
                items = self.driver.find_elements(By.CSS_SELECTOR,
                                                  '[data-marker="item"]')
                if items:
                    # print("Капча не обнаружена, страница загружена")
                    return True
                time.sleep(2)
            except Exception as e:
                print(f"Ошибка при проверке капчи: {e}")
                time.sleep(2)
                return False

    # Ничего не возвращает (занимает максимум 22 с.)
    def _advanced_human_behavior(self):
        # Имитация пользователя для обхода Qrator
        driver = self.driver
        actions = ActionChains(driver)

        # print("Имитация действий пользователя...")

        # Сложные паттерны прокрутки (координаты)
        scroll_sequences = [
            (0, 300), (100, 500), (-50, 200), (0, 800),
            (30, 400), (-20, 600), (0, 300), (150, 450)
        ]

        for x, y in scroll_sequences:
            driver.execute_script(f"window.scrollBy({x}, {y});")
            time.sleep(random.uniform(0.5, 1.5))

            # Случайные движения мышью
            try:
                body = driver.find_element(By.TAG_NAME, 'body')
                actions.move_to_element_with_offset(
                    body,
                    random.randint(100, 700),  # Случ. смещение по горизонтали
                    random.randint(100, 500)  # Случ. смещение по вертикали
                ).pause(random.uniform(0.1, 0.7)).perform()
            except:
                pass

        # Клик по случайному элементу
        try:
            clickable_elements = driver.find_elements(By.CSS_SELECTOR,
                                                      'body, [class*="header"],[class*="footer"]')
            if clickable_elements:
                random_element = random.choice(clickable_elements[:10])
                try:
                    actions.move_to_element(random_element).click().pause(
                        1).perform()
                    # print("Случайный клик")
                    time.sleep(random.uniform(1, 3))
                except:
                    pass
        except:
            pass

    # Возвращает строку url
    def _build_search_url(self, page=1):
        # Формирование URL для поиска
        base_url = f"https://www.avito.ru/{self.city}"
        encoded_query = quote_plus(self.query)

        params = [f"q={encoded_query}", "s=104"]  # Сортировка по дате

        if self.price_min is not None:
            params.append(f"pmin={self.price_min}")
        if self.price_max is not None:
            params.append(f"pmax={self.price_max}")
        if self.delivery:
            params.append("d=1")
        if page > 1:
            params.append(f"p={page}")

        search_url = f"{base_url}?{'&'.join(params)}"
        # print(f"Поисковый URL: {search_url}")
        return search_url

    # Возвращает список найденных объектов
    def main_parse_func(self, max_pages=1, headless=True):
        print("Запуск парсера")
        print("=" * 50)

        self.driver = self._setup_undetected_driver(headless=headless)
        if not self.driver:
            print("Не удалось инициализировать драйвер")
            return []
        all_items = []

        # Занимает максимум 120 с.
        try:
            for page in range(1, max_pages + 1):
                print(f"Страница {page}/{max_pages}")
                # Переход на главную страницу
                if page == 1:
                    self.driver.get("https://www.avito.ru/")
                    time.sleep(random.uniform(5, 8))
                    # Имитация поведения на главной
                    self._advanced_human_behavior()
                # Переход на страницу поиска
                search_url = self._build_search_url(page)
                self.driver.get(search_url)

                # Длительная задержка для обхода Qrator
                wait_time = random.uniform(8, 15)
                time.sleep(wait_time)

                if not self._wait_for_captcha():
                    print("Не удалось обойти защиту")
                    break

                self._advanced_human_behavior()

                # Парсинг объявлений на странице
                items = self._parse_page()
                if items:
                    all_items.extend(items)
                    # print(f"Найдено {len(items)} объявлений")
                else:
                    print("Не удалось найти объявления")
                    break

                # Пауза между страницами
                if page < max_pages:
                    delay = random.uniform(10, 20)
                    print(
                        f"Пауза {delay:.1f} сек перед следующей страницей")
                    time.sleep(delay)

        except Exception as e:
            print(f"Ошибка: {e}")
        finally:
            if self.driver:
                self.driver.quit()
                # print("Браузер закрыт")

        print(f"Найдено: {len(all_items)} объявлений")
        return all_items

    # Занимает максимум 15 с.
    def _parse_page(self):
        # Парсинг одной страницы
        try:
            # Создание объекта ожидания
            wait = WebDriverWait(self.driver, 15)
            # Ждет 15 с. пока не выполнится условие
            wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, '[data-marker="item"]')))

            containers = self.driver.find_elements(By.CSS_SELECTOR,
                                                   '[data-marker="item"]')
            print(f"Найдено контейнеров: {len(containers)}")

            items = []
            for container in containers[:20]:  # Ограничиваем для скорости
                item_data = self._extract_data_from_container(container)
                if item_data:
                    items.append(item_data)

            return items

        except TimeoutException:
            print("Таймаут при загрузке объявлений")
            # Пробуем парсить из исходного кода
            return self._parse_from_page_source()
        except Exception as e:
            print(f"Ошибка парсинга: {e}")
            return []

    def _parse_from_page_source(self):
        # Аварийный парсинг из исходного кода
        try:
            source = self.driver.page_source
            items = []
            # Сохраняем HTML для отладки
            with open("avito_debug.html", "w", encoding="utf-8") as f:
                f.write(source)
            print("💾 HTML сохранен как avito_debug.html")

            # Простой поиск по ключевым словам в исходном коде
            if self.query.lower() in source.lower():
                print("Запрос найден в исходном коде")

            return items
        except Exception as e:
            print(f"Ошибка аварийного парсинга: {e}")
            return []

    # Возвращает словарь
    def _extract_data_from_container(self, container):
        # Извлечение данных из  объявления
        try:
            title = "No title"
            link = "No link"
            price = "Не указана"
            location = "Не указано"
            date = "Не указано"
            image_url = "No image"
            delivery = False
            fitting = False

            # Название и ссылка
            main_elem = container.find_element(By.CSS_SELECTOR,
                                               '[data-marker="item-title"]')
            if main_elem:
                title = main_elem.text.strip()
                link = main_elem.get_attribute('href')

            # Цена
            try:
                price_elem = container.find_element(By.CSS_SELECTOR,
                                                    '[data-marker="item-price"]')

                if price_elem:
                    price = price_elem.text.strip()
            except NoSuchElementException:
                pass  # Оставляем значение по умолчанию

            # Локация
            try:
                location_selectors = [
                    '[data-marker="item-location"]',
                    '[class*="geo-address"]',
                    '[class*="address"]',
                    '.style-item-address-H3k6v'
                ]

                for selector in location_selectors:
                    try:
                        location_elem = container.find_element(
                            By.CSS_SELECTOR, selector)
                        location = location_elem.text.strip()
                        if location:
                            break
                    except:
                        continue
            except Exception as e:
                print(f"Ошибка извлечения локации: {e}")

            # Дата публикации
            try:
                date_elem = container.find_element(By.CSS_SELECTOR,
                                                   '[data-marker="item-date"]')
                date = date_elem.text.strip()
            except NoSuchElementException:
                pass

            # Первое фото
            try:
                img_selectors = [
                    'img[data-marker="item-image"]',
                    'img[itemprop="image"]',
                    'img[class*="image"]',
                    'source[type="image/jpeg"]'
                ]

                for selector in img_selectors:
                    try:
                        img_elem = container.find_element(By.CSS_SELECTOR,
                                                          selector)
                        temp_url = img_elem.get_attribute(
                            'src') or img_elem.get_attribute('data-src')
                        if temp_url and temp_url != "No image":
                            # Очищаем URL от мусора
                            if ';' in temp_url:
                                temp_url = temp_url.split(';')[0]
                            image_url = temp_url
                            break
                    except:
                        continue
            except Exception as e:
                print(f"Ошибка извлечения изображения: {e}")

            # Примерка и доставка
            try:
                location_selectors = [
                    '[class*="iva-item-listMiddleBlock-W7qtU"]',
                ]

                for selector in location_selectors:
                    try:
                        extra_elem = container.find_element(
                            By.CSS_SELECTOR,
                            selector)
                        if "Доставка" in extra_elem.text:
                            delivery = True
                        if "Можно примерить" in extra_elem.text:
                            fitting = True
                    except:
                        continue
            except Exception as e:
                print(f"Ошибка извлечения доп. параметров: {e}")
            return {
                'title': title,
                'price': price,
                'link': link,
                'date': date,
                'location': location,
                'delivery': delivery,
                'fitting': fitting,
                'image_url': image_url,
            }
        except Exception as e:
            print(f"Ошибка извлечения данных: {e}")
            return None



if __name__ == "__main__":
    print("Тестируем парсер с обходом защиты:")

    parser = ImprovedAvitoParser(
        city="sankt-peterburg",
        query="куртка юникло",
        price_min=1000,
        price_max=9000,
        delivery=True,
    )
    print("Построенный URL:", parser._build_search_url())
    start = time.time()

    items = parser.main_parse_func(max_pages=1, headless=False)

    end = time.time()

    if items:
        for i, item in enumerate(items[:3], 1):
            print(f"\n--- Объявление {i} ---")
            for key, value in item.items():
                print(f"{key}: {value}")
    print(f"На парсинг одной страницы ушло {end - start}")  # Обычно 2-3 минуты


