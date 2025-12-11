"""
Модуль для работы с уведомлениями в системе Windows.
Использует библиотеку plyer для кроссплатформенных уведомлений.
"""
from plyer import notification
import logging

logging.basicConfig(
    filename='notifications.log',
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S',
    encoding='utf-8'
)
# Создание логгера с именем модуля
logger = logging.getLogger(__name__)

# === Функции уведомлений (с логированием) ===

def notify_new_items(search_name, new_items):
    """
    ОСНОВНАЯ фукнция показа уведомлений.
    Args:
        search_name (str): Название поискового запроса
        new_items (list): Список новых объявлений (словарей)
    """
    if not new_items:
        logger.debug(f"Нет новых объявлений для '{search_name}'")
        return False
    item = new_items[0]
    try:
        if len(new_items) == 1:
            title = f"Новое объявление: {search_name}"
            message_parts = []
            if item.get('title'):
                message_parts.append(item['title'])
            if item.get('price'):
                message_parts.append(item['price'])
            if item.get('date'):
                message_parts.append(item['date'])
            message = ' | '.join(message_parts) if message_parts else \
                "Найдено новое объявление!"
        else:
            title = f"Новых объявлений: {len(new_items)}"
            # Показ первого объявления в сообщении
            sample_info = item.get('title', '')[:30]
            if item.get('price'):
                sample_info += f" - {item['price']}"
            message = f"По запросу: {search_name}\n{sample_info}\n..."
        notification.notify(
            title=title,
            message=message,
            app_name="Avito Tracker",
            timeout=10,  # секунд
            toast=True  # Стиль Windows 10/11 (через win10toast)
        )
        logger.info(f"Уведомление: '{search_name}' - {len(new_items)} новых")
        return True

    except Exception as e:
        logger.error(f"Ошибка уведомления для '{search_name}': {e}")
    return False


# def notify_error(error_message, search_name=None):
#     """
#     Показывает уведомление об ошибке.
#     Args:
#         error_message (str): Сообщение об ошибке
#         search_name (str, optional): Название запроса, в котором произошла ошибка
#     """
#     try:
#         title = "Ошибка Avito Tracker"
#         if search_name:
#             title = f"Ошибка в запросе: {search_name}"
#
#         notification.notify(
#             title=title,
#             message=error_message[:100],  # Ограничиваем длину
#             app_name="Avito Tracker",
#             timeout=10,
#             toast=True
#         )
#         logger.warning(f"Показано уведомление об ошибке: {error_message}")
#     except Exception as e:
#         logger.error(f"Не удалось показать уведомление об ошибке: {e}")
#
#
# def notify_system_message(title, message):
#     """
#     Показывает системное уведомление.
#     Args:
#         title (str): Заголовок уведомления
#         message (str): Текст уведомления
#     """
#     try:
#         notification.notify(
#             title=title,
#             message=message,
#             app_name="Avito Tracker",
#             timeout=5,
#             toast=True
#         )
#         logger.info(f"Системное уведомление: {title}")
#     except Exception as e:
#         logger.error(f"Ошибка системного уведомления: {e}")



if __name__=="__main__":
    try:
        notification.notify(
            title="Тест уведомления",
            message="Проверка работы Avito Tracker",
            app_name="Avito Tracker",
            timeout=5,
            toast=True
        )
        print("Уведомление отправлено")
    except Exception as e:
        print(f"Ошибка: {e}")