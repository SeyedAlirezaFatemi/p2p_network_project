import threading
from typing import List


class UserInterface(threading.Thread):
    buffer: List[str] = []

    def run(self):
        while True:
            message = input("Write your command:\n")
            self.buffer.append(message)

    def clear_buffer(self) -> None:
        self.buffer.clear()
