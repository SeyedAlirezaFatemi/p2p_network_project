from typing import Any

from src.tools.parsers import parse_ip
from tools.type_repo import Address


class SemiNode:
    def __init__(self, ip: str, port: int):
        self.ip = parse_ip(ip)
        self.port = port

    def get_ip(self) -> str:
        return self.ip

    def get_port(self) -> int:
        return self.port

    def get_address(self) -> Address:
        return self.ip, self.port

    def __eq__(self, other: Any) -> bool:
        return self.ip == other.ip and self.port == other.port
