from src.tools.parsers import parse_ip, parse_port


class SemiNode:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

    def get_ip(self):
        return self.ip

    def get_port(self):
        return self.port

    def get_address(self):
        return parse_ip(self.ip), parse_port(self.port)
