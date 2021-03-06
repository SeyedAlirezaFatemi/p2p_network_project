import threading
from typing import Callable, List, Optional

from src.Packet import Packet
from src.tools.Node import Node
from src.tools.parsers import parse_ip
from src.tools.simpletcp.tcpserver import TCPServer
from src.tools.type_repo import Address
from tools.logger import log


class Stream:

    def __init__(self, ip: str, port: int):
        """
        The Stream object constructor.

        Code design suggestion:
            1. Make a separate Thread for your TCPServer and start immediately.


        :param ip: str
        :param port: int
        """

        self.ip = parse_ip(ip)
        self.port = port

        self.nodes: List[Node] = []
        self._server_in_buf: List[bytearray] = []

        def callback(address, queue, data):
            """
            The callback function will run when a new data received from server_buffer.

            :param address: Source address.
            :param queue: Response queue.
            :param data: The data received from the socket.
            :return:
            """
            log('New data received.')
            queue.put(bytes('ACK', 'utf8'))
            self._server_in_buf.append(data)

        # ServerThread(ip, port, callback).start()
        formatted_ip = ".".join(str(int(part)) for part in ip.split("."))
        self.tcp = TCPServer(formatted_ip, port, callback)
        self.th = threading.Thread(target=self.tcp.run).start()

    def get_server_address(self) -> Address:
        """

        :return: Our TCPServer address
        :rtype: Address
        """
        return self.ip, self.port

    def clear_in_buff(self) -> None:
        """
        Discard any data in TCPServer input buffer.

        :return:
        """
        self._server_in_buf.clear()

    def add_node(self, server_address: Address, set_register_connection: bool = False) -> bool:
        """
        Will add new a node to our Stream.

        :param server_address: New node TCPServer address.
        :param set_register_connection: Shows that is this connection a register_connection or not.

        :type server_address: Address
        :type set_register_connection: bool

        :return:
        """
        try:
            node = Node(server_address, set_register=set_register_connection)
        except:
            log(f"Wrong address. Cannot connect to {server_address}")
            return False
        else:
            self.nodes.append(node)
            return True

    def remove_node(self, node: Node):
        """
        Remove the node from our Stream.

        Warnings:
            1. Close the node after deletion.

        :param node: The node we want to remove.
        :type node: Node

        :return:
        """
        try:
            log(f"Something happened to Node({node.get_server_address()}).\n\tI'm Going to kill him. Right NOW!")
            self.nodes.remove(node)
            node.close()
        except:
            return

    def get_node_by_address(self, ip: str, port: int, want_register: bool = False) -> Optional[Node]:
        """

        Will find the node that has IP/Port address of input.

        Warnings:
            1. Before comparing the address parse it to a standard format with parse_### functions.

        :param ip: input address IP
        :param port: input address Port
        :param want_register: do you want a register node?

        :return: The node that input address.
        :rtype: Node
        """
        for node in self.nodes:
            if node.get_server_address() == (parse_ip(ip), port) and node.is_register == want_register:
                return node

    def add_message_to_out_buff(self, address: Address, message: Packet, want_register: bool = False):
        """
        In this function, we will add the message to the output buffer of the node that has the input address.
        Later we should use send_out_buf_messages to send these buffers into their sockets.

        :param address: Node address that we want to send the message
        :param message: Message we want to send
        :param want_register: do you want a register node?

        Warnings:
            1. Check whether the node address is in our nodes or not.

        :return:
        """
        ip, port = address
        node = self.get_node_by_address(ip, port, want_register)
        if node:
            node.add_message_to_out_buff(message)

    def read_in_buf(self) -> List[bytearray]:
        """
        Only returns the input buffer of our TCPServer.

        :return: TCPServer input buffer.
        :rtype: list
        """
        return self._server_in_buf

    def send_messages_to_node(self, node: Node):
        """
        Send buffered messages to the 'node'

        Warnings:
            1. Insert an exception handler here; Maybe the node socket you want to send the message has turned off and
            you need to remove this node from stream nodes.

        :param node:
        :type node Node

        :return:
        """
        try:
            node.send_message()
        except:
            self.remove_node(node)

    def send_out_buf_messages(self, only_register: bool = False):
        """
        In this function, we will send hole out buffers to their own clients.

        :return:
        """
        for node in self.nodes:
            if only_register:
                if node.is_register:
                    self.send_messages_to_node(node)
            else:
                self.send_messages_to_node(node)


class ServerThread(threading.Thread):
    def __init__(self, ip: str, port: int, callback: Callable) -> None:
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.callback = callback

    def run(self):
        TCPServer(self.ip, self.port, self.callback).run()
