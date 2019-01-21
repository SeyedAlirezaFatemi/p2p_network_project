from src.Packet import Packet
from src.tools.parsers import parse_ip
from src.tools.simpletcp.clientsocket import ClientSocket
from src.tools.type_repo import Address
from tools.logger import log


class Node:
    def __init__(self, server_address: Address, set_register: bool = False):
        """
        The Node object constructor.

        This object is our low-level abstraction for other peers in the network.
        Every node has a ClientSocket that should bind to the Node TCPServer address.

        Warnings:
            1. Insert an exception handler when initializing the ClientSocket; when a socket closed here we will face to
               an exception and we should detach this Node and clear its output buffer.

        :param server_address:
        :param set_register:
        """
        self.server_ip = parse_ip(server_address[0])
        self.server_port = server_address[1]

        log(f"Server Address: {server_address}")

        self.out_buff = []
        self.is_register = set_register

        try:
            self.client = ClientSocket(server_address[0], server_address[1])
        except:
            pass

    def send_message(self):
        """
        Final function to send buffer to the client's socket.

        :return:
        """
        for message in self.out_buff:
            response = self.client.send(message.get_buf())
            if response != b'ACK':
                # TODO: Something went wrong
                pass
        self.out_buff.clear()

    def add_message_to_out_buff(self, message: Packet):
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
        :rtype: Address
        """
        return self.server_ip, self.server_port

    def __eq__(self, other) -> bool:
        return self.server_ip == other.server_ip and self.server_port == other.server_port \
               and self.is_register == other.is_register
