from typing import List

from src.Packet import Packet
from src.tools.parsers import parse_ip
from src.tools.simpletcp.clientsocket import ClientSocket
from src.tools.type_repo import Address
from tools.logger import log


class Node:
    def __init__(self, server_address: Address, set_register: bool = False) -> None:
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

        log(f"Node({server_address}): Initialized.")

        self.out_buff: List[Packet] = []
        self.is_register = set_register

    def __initialize_client_socket(self):
        try:
            self.client = ClientSocket(self.server_ip, self.server_port)
        except:
            # TODO: What should we do? The warning in the constructor.
            pass

    def send_message(self) -> None:
        """
        Final function to send buffer to the client's socket.

        :return:
        """
        for packet in self.out_buff:
            self.__initialize_client_socket()
            response = self.client.send(packet.get_buf())
            if response != b'ACK':
                log(f"Node({self.get_server_address()}): Message of type {packet.get_type()} not ACKed.")
        self.out_buff.clear()

    def add_message_to_out_buff(self, message: Packet) -> None:
        """
        Here we will add a new message to the server out_buff, then in 'send_message' will send them.

        :param message: The message we want to add to out_buff
        :return:
        """
        self.out_buff.append(message)

    def close(self) -> None:
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
