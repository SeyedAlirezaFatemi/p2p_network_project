# from src.tools.simpletcp.clientsocket import ClientSocket

from src.tools.parsers import parse_ip
from src.tools.type_repo import Address


class Node:
    def __init__(self, server_address: Address, set_root: bool = False, set_register: bool = False):
        """
        The Node object constructor.

        This object is our low-level abstraction for other peers in the network.
        Every node has a ClientSocket that should bind to the Node TCPServer address.

        Warnings:
            1. Insert an exception handler when initializing the ClientSocket; when a socket closed here we will face to
               an exception and we should detach this Node and clear its output buffer.

        :param server_address:
        :param set_root:
        :param set_register:
        """
        self.server_ip = parse_ip(server_address[0])
        self.server_port = server_address[1]

        print("Server Address: ", server_address)

        self.out_buff = []
        self.is_root = set_root
        self.is_register = set_register

    def send_message(self):
        """
        Final function to send buffer to the client's socket.

        :return:
        """
        pass

    def add_message_to_out_buff(self, message):
        """
        Here we will add a new message to the server out_buff, then in 'send_message' will send them.

        :param message: The message we want to add to out_buff
        :return:
        """
        self.out_buff.append(message)

    def close(self):
        """
        Closing client's object.
        :return:
        """
        self.client.close()

    def get_server_address(self) -> Address:
        """

        :return: Server address in a pretty format.
        :rtype: tuple
        """
        return self.server_ip, self.server_port
