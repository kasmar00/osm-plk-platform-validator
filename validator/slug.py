import re

TRANSLATION_TABLE = str.maketrans(
    {
        "ą": "a",
        "ć": "c",
        "ę": "e",
        "ł": "l",
        "ó": "o",
        "ń": "n",
        "ó": "o",
        "ś": "s",
        "ź": "z",
        "ż": "z",
    }
)


def slug(s: str) -> str:
    text = s.translate(TRANSLATION_TABLE)
    return re.sub(r"[ -]+", "-", re.sub(r"[^\x00-\x7F]+", "", text)).lower()
