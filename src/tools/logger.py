import time


def log(message: str) -> None:
    print(f"{time.strftime('%X')}: {message}'")
