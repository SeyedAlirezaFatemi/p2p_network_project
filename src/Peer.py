import os
import sys
import threading
import time
from enum import Enum
from typing import Callable, List

from src.Packet import AdvertiseType, Packet, PacketFactory, PacketType, RegisterType, ReunionType
from src.Stream import Stream
from src.UserInterface import UserInterface
from src.tools.Graph import GraphNode, NetworkGraph
from src.tools.SemiNode import SemiNode
from src.tools.parsers import parse_ip
from src.tools.type_repo import Address
from tools.logger import log

"""
    Peer is our main object in this project.
    In this network Peers will connect together to make a tree graph.
    This network is not completely decentralised but will show you some real-world challenges in Peer to Peer networks.    
"""

MAX_PENDING_TIME = 36
MAX_HELLO_INTERVAL = 24


class ReunionMode(Enum):
    FAILED = 'FAILED'
    ACCEPTANCE = 'ACCEPTANCE'


class Peer:
    def __init__(self, server_ip: str, server_port: int, is_root: bool = False, root_address: Address = None) -> None:
        """
        The Peer object constructor.

        Code design suggestions:
            1. Initialise a Stream object for our Peer.
            2. Initialise a PacketFactory object.
            3. Initialise our UserInterface for interaction with user commandline.
            4. Initialise a Thread for handling reunion daemon.

        Warnings:
            1. For root Peer, we need a NetworkGraph object.
            2. In root Peer, start reunion daemon as soon as possible.
            3. In client Peer, we need to connect to the root of the network, Don't forget to set this connection
               as a register_connection.


        :param server_ip: Server IP address for this Peer that should be pass to Stream.
        :param server_port: Server Port address for this Peer that should be pass to Stream.
        :param is_root: Specify that is this Peer root or not.
        :param root_address: Root IP/Port address if we are a client.

        :type server_ip: str
        :type server_port: int
        :type is_root: bool
        :type root_address: Address
        """
        self.server_ip = parse_ip(server_ip)
        self.server_port = server_port
        self.address = (self.server_ip, self.server_port)
        self.is_root = is_root
        self.root_address = root_address
        self.reunion_daemon = ReunionThread(self.run_reunion_daemon)
        self.reunion_mode = ReunionMode.ACCEPTANCE

        self.registered: List[SemiNode] = []
        self.parent_address: Address = None
        self.children_addresses: List[Address] = []
        self.stream = Stream(server_ip, server_port)
        self.user_interface = UserInterface()

        self.last_hello_back_time = None  # When you received your last hello back from root
        self.last_hello_time = None  # When you sent your last hello to root

        if is_root:
            self.network_graph = NetworkGraph(GraphNode((self.server_ip, self.server_port)))
            self.reunion_daemon.start()
        else:
            self.start_user_interface()

    def start_user_interface(self) -> None:
        """
        For starting UserInterface thread.

        :return:
        """
        if not self.is_root:
            log('UserInterface started.')
            self.user_interface.start()

    def handle_user_interface_buffer(self) -> None:
        """
        In every interval, we should parse user command that buffered from our UserInterface.
        All of the valid commands are listed below:
            1. Register:  With this command, the client send a Register Request packet to the root of the network.
            2. Advertise: Send an Advertise Request to the root of the network for finding first hope.
            3. SendMessage: The following string will be added to a new Message packet and broadcast through the network.

        Warnings:
            1. Ignore irregular commands from the user.
            2. Don't forget to clear our UserInterface buffer.
        :return:
        """
        user_interface_buffer = self.user_interface.buffer
        for command in user_interface_buffer:
            if command.lower() == 'register':
                self.__handle_register_command()
            elif command.lower() == 'advertise':
                self.__handle_advertise_command()
            elif command.lower().startswith('sendmessage'):
                self.__handle_message_command(command)
            else:
                log('Are you on drugs?')
        self.user_interface.clear_buffer()

    def __handle_register_command(self) -> None:
        self.__register()

    def __register(self) -> None:
        self.stream.add_node(self.root_address, set_register_connection=True)
        register_packet = PacketFactory.new_register_packet(RegisterType.REQ, self.address, self.root_address)
        self.stream.add_message_to_out_buff(self.root_address, register_packet, want_register=True)
        log(f'Register packet added to out buff of Node({self.root_address}).')

    def __handle_advertise_command(self) -> None:
        advertise_packet = PacketFactory.new_advertise_packet(AdvertiseType.REQ, self.address)
        self.stream.add_message_to_out_buff(self.root_address, advertise_packet, want_register=True)
        log(f'Advertise packet added to out buff of Node({self.root_address}).')

    def __handle_message_command(self, command: str) -> None:
        message = command[12:]
        broadcast_packet = PacketFactory.new_message_packet(message, self.address)
        self.send_broadcast_packet(broadcast_packet)

    def run(self):
        """
        The main loop of the program.

        Code design suggestions:
            1. Parse server in_buf of the stream.
            2. Handle all packets were received from our Stream server.
            3. Parse user_interface_buffer to make message packets.
            4. Send packets stored in nodes buffer of our Stream object.
            5. ** sleep the current thread for 2 seconds **

        Warnings:
            1. At first check reunion daemon condition; Maybe we have a problem in this time
               and so we should hold any actions until Reunion acceptance.
            2. In every situation checkout Advertise Response packets; even is Reunion in failure mode or not

        :return:
        """
        try:
            while True:
                in_buff = self.stream.read_in_buf()
                for message in in_buff:
                    packet = PacketFactory.parse_buffer(message)
                    self.handle_packet(packet)
                self.stream.clear_in_buff()
                self.handle_user_interface_buffer()
                self.stream.send_out_buf_messages(self.reunion_mode == ReunionMode.FAILED)
                time.sleep(2)
        except KeyboardInterrupt:
            log('KeyboardInterrupt')
            try:
                sys.exit(0)
            except SystemExit:
                os._exit(0)

    def run_reunion_daemon(self):
        """

        In this function, we will handle all Reunion actions.

        Code design suggestions:
            1. Check if we are the network root or not; The actions are identical.
            2. If it's the root Peer, in every interval check the latest Reunion packet arrival time from every node;
               If time is over for the node turn it off (Maybe you need to remove it from our NetworkGraph).
            3. If it's a non-root peer split the actions by considering whether we are waiting for Reunion Hello Back
               Packet or it's the time to send new Reunion Hello packet.

        Warnings:
            1. If we are the root of the network in the situation that we want to turn a node off, make sure that you will not
               advertise the nodes sub-tree in our GraphNode.
            2. If we are a non-root Peer, save the time when you have sent your last Reunion Hello packet; You need this
               time for checking whether the Reunion was failed or not.
            3. For choosing time intervals you should wait until Reunion Hello or Reunion Hello Back arrival,
               pay attention that our NetworkGraph depth will not be bigger than 8. (Do not forget main loop sleep time)
            4. Suppose that you are a non-root Peer and Reunion was failed, In this time you should make a new Advertise
               Request packet and send it through your register_connection to the root; Don't forget to send this packet
               here, because in the Reunion Failure mode our main loop will not work properly and everything will be got stock!

        :return:
        """
        while True:
            if self.is_root:
                self.__run_root_reunion_daemon()
            else:
                self.__run_non_root_reunion_daemon()
            time.sleep(4)

    def __run_root_reunion_daemon(self):
        graph_nodes = self.network_graph.nodes
        for graph_node in graph_nodes:
            if graph_node.address == self.address:
                continue
            time_passed_since_last_hello = time.time() - graph_node.last_hello
            log(f'Time passed since last hello from Node({graph_node.address}): {time_passed_since_last_hello}')
            if time_passed_since_last_hello > MAX_HELLO_INTERVAL:
                self.stream.remove_node(self.stream.get_node_by_address(graph_node.address[0], graph_node.address[1]))
                self.network_graph.remove_node(graph_node.address)

    def __run_non_root_reunion_daemon(self):
        time_between_last_hello_and_last_hello_back = self.last_hello_time - self.last_hello_back_time
        log(f'Time between last hello and last hello back: {time_between_last_hello_and_last_hello_back}')
        if self.last_hello_time - self.last_hello_back_time > MAX_PENDING_TIME:
            log('Seems like we are disconnected from the root. Trying to reconnect...')
            self.reunion_mode = ReunionMode.FAILED
            self.__handle_advertise_command()  # Send new Advertise packet
            time.sleep(3)
        else:
            log(f'Sending new Reunion Hello packet.')
            packet = PacketFactory.new_reunion_packet(ReunionType.REQ, self.address, [self.address])
            self.stream.add_message_to_out_buff(self.parent_address, packet)
            self.last_hello_time = time.time()

    def send_broadcast_packet(self, broadcast_packet: Packet) -> None:
        """

        For setting broadcast packets buffer into Nodes out_buff.

        Warnings:
            1. Don't send Message packets through register_connections.

        :param broadcast_packet: The packet that should be broadcast through the network.
        :type broadcast_packet: Packet

        :return:
        """
        for neighbor_address in [*self.children_addresses, self.parent_address]:
            self.stream.add_message_to_out_buff(neighbor_address, broadcast_packet)
            log(f'Message packet added to out buff of Node({neighbor_address}).')

    def handle_packet(self, packet):
        """

        This function act as a wrapper for other handle_###_packet methods to handle the packet.

        Code design suggestion:
            1. It's better to check packet validation right now; For example Validation of the packet length.

        :param packet: The arrived packet that should be handled.

        :type packet Packet

        """
        if not self.__validate_received_packet(packet):
            return
        packet_type = packet.get_type()
        log(f'Packet of type {packet_type.name} received.')
        if self.reunion_mode == ReunionMode.FAILED:
            if packet_type == PacketType.ADVERTISE:
                self.__handle_advertise_packet(packet)
            return
        if packet_type == PacketType.MESSAGE:
            self.__handle_message_packet(packet)
        elif packet_type == PacketType.ADVERTISE:
            self.__handle_advertise_packet(packet)
        elif packet_type == PacketType.JOIN:
            self.__handle_join_packet(packet)
        elif packet_type == PacketType.REGISTER:
            self.__handle_register_packet(packet)
        elif packet_type == PacketType.REUNION:
            self.__handle_reunion_packet(packet)

    @staticmethod
    def __validate_received_packet(packet: Packet) -> bool:
        if packet.get_length() != len(packet.get_body()):
            return False
        # TODO: More conditions
        return True

    def __check_registered(self, source_address: Address) -> bool:
        """
        If the Peer is the root of the network we need to find that is a node registered or not.

        :param source_address: Unknown IP/Port address.
        :type source_address: Address

        :return:
        """
        source_ip, source_port = source_address
        source_node = SemiNode(source_ip, source_port)
        return source_node in self.registered

    def __handle_advertise_packet(self, packet: Packet):
        """
        For advertising peers in the network, It is peer discovery message.

        Request:
            We should act as the root of the network and reply with a neighbour address in a new Advertise Response packet.

        Response:
            When an Advertise Response packet type arrived we should update our parent peer and send a Join packet to the
            new parent.

        Code design suggestion:
            1. Start the Reunion daemon thread when the first Advertise Response packet received.
            2. When an Advertise Response message arrived, make a new Join packet immediately for the advertised address.

        Warnings:
            1. Don't forget to ignore Advertise Request packets when you are a non-root peer.
            2. The addresses which still haven't registered to the network can not request any peer discovery message.
            3. Maybe it's not the first time that the source of the packet sends Advertise Request message. This will happen
               in rare situations like Reunion Failure. Pay attention, don't advertise the address to the packet sender
               sub-tree.
            4. When an Advertise Response packet arrived update our Peer parent for sending Reunion Packets.

        :param packet: Arrived register packet

        :type packet Packet

        :return:
        """
        advertise_type = self.__identify_advertise_type(packet)
        if self.is_root and advertise_type == AdvertiseType.REQ:
            self.__handle_advertise_request(packet)
        elif (not self.is_root) and advertise_type == AdvertiseType.RES:
            self.__handle_advertise_response(packet)

    def __identify_advertise_type(self, packet: Packet) -> AdvertiseType:
        advertise_type = packet.get_body()[:3]
        return AdvertiseType(advertise_type)

    def __handle_advertise_request(self, packet: Packet) -> None:
        sender_address = packet.get_source_server_address()
        sender_semi_node = SemiNode(sender_address[0], sender_address[1])
        if sender_semi_node not in self.registered:
            log(f'Advertise Request from unregistered source({sender_address}).')
            return
        advertised_address = self.__get_neighbour(sender_address)
        log(f'Advertising Node({advertised_address}) to Node({sender_address}).')
        advertise_response_packet = PacketFactory.new_advertise_packet(AdvertiseType.RES, self.address,
                                                                       advertised_address)
        self.stream.add_message_to_out_buff(sender_address, advertise_response_packet, want_register=True)
        # Add to network_graph
        self.network_graph.add_node(sender_semi_node.get_ip(), sender_semi_node.get_port(), advertised_address)

    def __handle_advertise_response(self, packet: Packet) -> None:
        self.last_hello_time = time.time()
        self.last_hello_back_time = time.time()
        parent_address = packet.get_advertised_address()
        log(f'Trying to join Node({parent_address})...')
        self.parent_address = parent_address
        join_packet = PacketFactory.new_join_packet(self.address)
        self.stream.add_node(parent_address)  # Add a non_register Node to stream to the parent
        log(f'Join Request added to out buf on Node({parent_address}).')
        self.stream.add_message_to_out_buff(parent_address, join_packet)
        self.reunion_mode = ReunionMode.ACCEPTANCE
        if not self.reunion_daemon.is_alive():
            self.reunion_daemon.start()

    def __handle_register_packet(self, packet: Packet):
        """
        For registration a new node to the network at first we should make a Node with stream.add_node for'sender' and
        save it.

        Code design suggestion:
            1.For checking whether an address is registered since now or not you can use SemiNode object except Node.

        Warnings:
            1. Don't forget to ignore Register Request packets when you are a non-root peer.

        :param packet: Arrived register packet
        :type packet Packet
        :return:
        """
        register_type = self.__identify_register_type(packet)
        if self.is_root and register_type == RegisterType.REQ:
            new_node = SemiNode(packet.get_source_server_ip(), packet.get_source_server_port())
            if new_node in self.registered:
                return
            self.registered.append(new_node)
            sender_address = packet.get_source_server_address()
            self.stream.add_node(sender_address, set_register_connection=True)
            register_response_packet = PacketFactory.new_register_packet(RegisterType.RES, self.address)
            self.stream.add_message_to_out_buff(sender_address, register_response_packet, want_register=True)
        elif register_type == RegisterType.RES:
            log('Register request ACKed by root. You are now registered.')

    def __identify_register_type(self, packet: Packet) -> RegisterType:
        register_type = packet.get_body()[:3]
        return RegisterType(register_type)

    def __check_neighbour(self, address: Address) -> bool:
        """
        It checks is the address in our neighbours array or not.

        :param address: Unknown address

        :type address: Address

        :return: Whether is address in our neighbours or not.
        :rtype: bool
        """
        is_from_children = False
        for child_address in self.children_addresses:
            is_from_children = is_from_children or (child_address == address)
        is_from_parent = (address == self.parent_address)
        return is_from_parent or is_from_children

    def __handle_message_packet(self, packet: Packet):
        """
        Only broadcast message to the other nodes.

        Warnings:
            1. Do not forget to ignore messages from unknown sources.
            2. Make sure that you are not sending a message to a register_connection.

        :param packet: Arrived message packet

        :type packet Packet

        :return:
        """
        log(f'New message arrived: {packet.get_body()}')
        sender_address = packet.get_source_server_address()
        updated_packet = PacketFactory.new_message_packet(packet.get_body(), self.address)
        if self.__check_neighbour(sender_address):  # From known source
            for neighbor_address in [*self.children_addresses, self.parent_address]:
                if neighbor_address is not None and neighbor_address != sender_address:
                    self.stream.add_message_to_out_buff(neighbor_address, updated_packet)

    def __handle_reunion_packet(self, packet: Packet):
        """
        In this function we should handle Reunion packet was just arrived.

        Reunion Hello:
            If you are root Peer you should answer with a new Reunion Hello Back packet.
            At first extract all addresses in the packet body and append them in descending order to the new packet.
            You should send the new packet to the first address in the arrived packet.
            If you are a non-root Peer append your IP/Port address to the end of the packet and send it to your parent.

        Reunion Hello Back:
            Check that you are the end node or not; If not only remove your IP/Port address and send the packet to the next
            address, otherwise you received your response from the root and everything is fine.

        Warnings:
            1. Every time adding or removing an address from packet don't forget to update Entity Number field.
            2. If you are the root, update last Reunion Hello arrival packet from the sender node and turn it on.
            3. If you are the end node, update your Reunion mode from pending to acceptance.


        :param packet: Arrived reunion packet
        :return:
        """
        reunion_type = self.__identify_reunion_type(packet)
        if self.is_root and reunion_type == ReunionType.REQ:
            self.__update_last_reunion(packet)
            self.__respond_to_reunion(packet)
        else:
            if reunion_type == ReunionType.REQ:
                self.__pass_reunion_hello(packet)
            else:
                self.__handle_reunion_hello_back(packet)

    def __update_last_reunion(self, packet: Packet):
        sender_address = packet.get_addresses()[0]
        next_node = packet.get_addresses()[-1]
        self.network_graph.keep_alive(sender_address)
        log(f'New Hello from Node({sender_address}).')
        log(f'HelloBack added to out buf of Node({next_node})')

    def __respond_to_reunion(self, packet: Packet):
        reversed_addresses = packet.get_addresses_in_reverse()
        response_packet = PacketFactory.new_reunion_packet(ReunionType.RES, self.address, reversed_addresses)
        next_node_address = reversed_addresses[0]
        self.stream.add_message_to_out_buff(next_node_address, response_packet)

    def __identify_reunion_type(self, packet: Packet) -> ReunionType:
        reunion_type = packet.get_body()[:3]
        return ReunionType(reunion_type)

    def __pass_reunion_hello(self, packet: Packet):
        new_addresses = self.__format_reunion_hello_addresses_on_pass(packet)
        request_packet = PacketFactory.new_reunion_packet(ReunionType.REQ, self.address, new_addresses)
        self.stream.add_message_to_out_buff(self.parent_address, request_packet)

    def __format_reunion_hello_addresses_on_pass(self, packet: Packet) -> List[Address]:
        addresses = packet.get_addresses()
        addresses.append(self.address)
        return addresses

    def __handle_reunion_hello_back(self, packet: Packet):
        if packet.get_addresses()[-1] == self.address:
            # It's our hello back!
            self.last_hello_back_time = time.time()
            log('We received our HelloBack.')
        else:
            self.__pass_reunion_hello_back(packet)

    def __pass_reunion_hello_back(self, packet: Packet):
        new_addresses = packet.get_addresses()[1:]
        next_node_address = new_addresses[0]
        log(f'HelloBack packet passed down to Node({next_node_address}).')
        passed_packet = PacketFactory.new_reunion_packet(ReunionType.RES, self.address, new_addresses)
        self.stream.add_message_to_out_buff(next_node_address, passed_packet)

    def __handle_join_packet(self, packet: Packet):
        """
        When a Join packet received we should add a new node to our nodes array.
        In reality, there is a security level that forbids joining every node to our network.

        :param packet: Arrived register packet.


        :type packet Packet

        :return:
        """
        new_member_address = packet.get_source_server_address()
        log(f'New JOIN packet from Node({new_member_address}).')
        self.stream.add_node(new_member_address)
        self.children_addresses.append(new_member_address)

    def __get_neighbour(self, sender: Address) -> Address:
        """
        Finds the best neighbour for the 'sender' from the network_nodes array.
        This function only will call when you are a root peer.

        Code design suggestion:
            1. Use your NetworkGraph find_live_node to find the best neighbour.

        :param sender: Sender of the packet
        :return: The specified neighbour for the sender; The format is like ('192.168.001.001', 5335).
        """
        if self.is_root:
            return self.network_graph.find_live_node(sender)


class ReunionThread(threading.Thread):
    def __init__(self, handler: Callable) -> None:
        threading.Thread.__init__(self)
        self.handler = handler

    def run(self):
        log('Starting reunion daemon...')
        self.handler()
