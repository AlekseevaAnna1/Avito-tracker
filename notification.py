"""
Модуль для работы с уведомлениями в системе Windows.
Использует библиотеку plyer для кроссплатформенных уведомлений.
"""
from plyer import notification
import logging

# Настройка логирования для уведомлений
logger = logging.getLogger(__name__)


def notify_new_items(search_name, new_items):
    """
    ОСНОВНАЯ фукнция показа уведомлений.
    Args:
        search_name (str): Название поискового запроса
        new_items (list): Список новых объявлений (словарей)
    """
    if not new_items:
        return False
    try:
        if len(new_items) == 1:
            item = new_items[0]
            _show_single_notification(search_name, item)
        else:
            _show_multiple_notification(search_name, new_items)

        logger.info(f"Показано уведомление для запроса '{search_name}' ({len(new_items)} новых объявлений)")
        return True

    except Exception as e:
        logger.error(f"Ошибка при показе уведомления: {e}", exc_info=True)
        return False


def _show_single_notification(search_name, item):
    """Вспомогательная функция показа 1-го объявления."""
    title = f"Новое объявление: {search_name}"

    # Формирование сообщения
    message_parts = []
    if item.get('title'):
        message_parts.append(item['title'])
    if item.get('price'):
        message_parts.append(f"Цена: {item['price']}")
    if item.get('date'):
        message_parts.append(f"Дата: {item['date']}")

    message = " | ".join(
        message_parts) if message_parts else "Найдено новое объявление"

    notification.notify(
        title=title,
        message=message,
        app_name="Avito Tracker",
        timeout=10,  # секунд
        toast=True  # Стиль Windows 10/11 (через win10toast)
    )


def _show_multiple_notification(search_name, new_items):
    """
    Вспомогательная функция показа нескольких объявлений.
    """
    title = f"Новых объявлений: {len(new_items)})"

    # Показ первого объявления в сообщении
    sample_item = new_items[0]
    sample_info = sample_item.get('title', '')[:30]
    if sample_item.get('price'):
        sample_info += f" - {sample_item['price']}"

    message = f"По запросу: {search_name}\nПример: {sample_info}\n..."

    notification.notify(
        title=title,
        message=message,
        app_name="Avito Tracker",
        timeout=10,
        toast=True
    )


def notify_error(error_message, search_name=None):
    """
    Показывает уведомление об ошибке.
    Args:
        error_message (str): Сообщение об ошибке
        search_name (str, optional): Название запроса, в котором произошла ошибка
    """
    try:
        title = "Ошибка Avito Tracker"
        if search_name:
            title = f"Ошибка в запросе: {search_name}"

        notification.notify(
            title=title,
            message=error_message[:100],  # Ограничиваем длину
            app_name="Avito Tracker",
            timeout=10,
            toast=True
        )
        logger.warning(f"Показано уведомление об ошибке: {error_message}")
    except Exception as e:
        logger.error(f"Не удалось показать уведомление об ошибке: {e}")


def notify_system_message(title, message):
    """
    Показывает системное уведомление.
    Args:
        title (str): Заголовок уведомления
        message (str): Текст уведомления
    """
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="Avito Tracker",
            timeout=5,
            toast=True
        )
        logger.info(f"Системное уведомление: {title}")
    except Exception as e:
        logger.error(f"Ошибка системного уведомления: {e}")





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