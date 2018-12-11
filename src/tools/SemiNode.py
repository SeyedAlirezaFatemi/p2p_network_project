class SemiNode:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port

    def get_ip(self):
        return self.ip

    def get_port(self):
        return self.port

    def get_address(self):
        return SemiNode.parse_ip(self.ip), SemiNode.parse_port(self.port)

    @staticmethod
    def parse_ip(ip):
        """
        Automatically change the input IP format like '192.168.001.001'.
        :param ip: Input IP
        :type ip: str

        :return: Formatted IP
        :rtype: str
        """
        return '.'.join(str(int(part)).zfill(3) for part in ip.split('.'))

    @staticmethod
    def parse_port(port):
        """
        Automatically change the input IP format like '05335'.
        :param port: Input IP
        :type port: str

        :return: Formatted IP
        :rtype: str
        """
        return str(int(port)).zfill(5)

