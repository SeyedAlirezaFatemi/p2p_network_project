from typing import Union


def parse_ip(ip: str) -> str:
    """
    Automatically change the input IP format like '192.168.001.001'.
    :param ip: Input IP
    :type ip: str

    :return: Formatted IP
    :rtype: str
    """
    return '.'.join(str(int(part)).zfill(3) for part in ip.split('.'))


def parse_port(port: Union[str, int]) -> str:
    """
    Automatically change the input IP format like '05335'.
    :param port: Input IP
    :type port: str

    :return: Formatted IP
    :rtype: str
    """
    return str(int(port)).zfill(5)
