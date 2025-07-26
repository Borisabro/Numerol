from datetime import datetime
from typing import Tuple, Dict

# Mapping letters to numbers based on the Pythagorean system
LETTER_MAP: Dict[str, int] = {
    **{chr(c): ((c - 64) % 9 or 9) for c in range(ord('A'), ord('Z') + 1)}
}

MASTER_NUMBERS = {11, 22, 33}


def _reduce(number: int) -> int:
    """Reduce a number to a single digit unless it is a master number (11, 22, 33)."""
    while number > 9 and number not in MASTER_NUMBERS:
        number = sum(int(d) for d in str(number))
    return number


def life_path(date_str: str) -> Tuple[int, str]:
    """Calculate the Life Path number from a date string (YYYY-MM-DD)."""
    try:
        birth_date = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Формат даты должен быть ГГГГ-ММ-ДД (например, 1984-10-27)")

    total = sum(int(d) for d in birth_date.strftime("%Y%m%d"))
    number = _reduce(total)
    description = LIFE_PATH_DESCRIPTIONS.get(number, "Описание отсутствует.")
    return number, description


def expression(name: str) -> Tuple[int, str]:
    """Calculate the Expression (Destiny) number from a full name."""
    cleaned = [ch for ch in name.upper() if ch.isalpha()]
    if not cleaned:
        raise ValueError("Имя должно содержать хотя бы одну букву.")

    total = sum(LETTER_MAP[ch] for ch in cleaned)
    number = _reduce(total)
    description = EXPRESSION_DESCRIPTIONS.get(number, "Описание отсутствует.")
    return number, description


# --- Example descriptions (stub, can be expanded) ---
LIFE_PATH_DESCRIPTIONS: Dict[int, str] = {
    1: "Вы — лидер, обладающий инициативой и сильной волей.",
    2: "Вы — дипломат, ценящий гармонию и партнёрство.",
    3: "Вы — творческая личность с ярким самовыражением.",
    4: "Вы — практичны и надёжны, стремитесь к стабильности.",
    5: "Вы — свободолюбивый дух, ценящий перемены и приключения.",
    6: "Вы — заботливы и ответственны, ищете гармонию в семье.",
    7: "Вы — исследователь, стремящийся к знаниям и духовности.",
    8: "Вы — амбициозны и ориентированы на материальный успех.",
    9: "Вы — гуманист с широкими взглядами и состраданием.",
    11: "Мастер-число: интуиция и вдохновение, духовный лидер.",
    22: "Мастер-число: мастер-строитель, способный реализовать великие идеи.",
    33: "Мастер-число: учитель безусловной любви и служения миру.",
}

EXPRESSION_DESCRIPTIONS: Dict[int, str] = {
    1: "Ваше предназначение — быть первопроходцем и лидером.",
    2: "Вы рождены для сотрудничества и гармонии.",
    3: "Ваш дар — творчество и коммуникация.",
    4: "Вы строите прочные основы и структуры.",
    5: "Ваша судьба — перемены и свобода.",
    6: "Вы призваны служить и заботиться об окружающих.",
    7: "Ваш путь — мудрость и анализ.",
    8: "Вы управляете материальными ресурсами и властью.",
    9: "Ваша миссия — служение человечеству.",
    11: "Мастер-число: духовное вдохновение и идеализм.",
    22: "Мастер-число: реализация великих замыслов на практике.",
    33: "Мастер-число: вселенская любовь и наставничество.",
}


COLOR_MAP = {
    "life_path": "#4285F4",  # blue
    "expression": "#0F9D58",  # green
}