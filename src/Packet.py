"""

    This is the format of packets in our network:
    


                                                **  NEW Packet Format  **
     __________________________________________________________________________________________________________________
    |           Version(2 Bytes)         |         Type(2 Bytes)         |           Length(Long int/4 Bytes)          |
    |------------------------------------------------------------------------------------------------------------------|
    |                                            Source Server IP(8 Bytes)                                             |
    |------------------------------------------------------------------------------------------------------------------|
    |                                           Source Server Port(4 Bytes)                                            |
    |------------------------------------------------------------------------------------------------------------------|
    |                                                    ..........                                                    |
    |                                                       BODY                                                       |
    |                                                    ..........                                                    |
    |__________________________________________________________________________________________________________________|

    Version:
        For now version is 1
    
    Type:
        1: Register
        2: Advertise
        3: Join
        4: Message
        5: Reunion
                e.g: type = '2' => Advertise packet.
    Length:
        This field shows the character numbers for Body of the packet.

    Server IP/Port:
        We need this field for response packet in non-blocking mode.



    ***** For example: ******

    version = 1                 b'\x00\x01'
    type = 4                    b'\x00\x04'
    length = 12                 b'\x00\x00\x00\x0c'
    ip = '192.168.001.001'      b'\x00\xc0\x00\xa8\x00\x01\x00\x01'
    port = '65000'              b'\x00\x00\xfd\xe8'
    Body = 'Hello World!'       b'Hello World!'

    Bytes = b'\x00\x01\x00\x04\x00\x00\x00\x0c\x00\xc0\x00\xa8\x00\x01\x00\x01\x00\x00\xfd\xe8Hello World!'




    Packet descriptions:
    
        Register:
            Request:
        
                                 ** Body Format **
                 ________________________________________________
                |                  REQ (3 Chars)                 |
                |------------------------------------------------|
                |                  IP (15 Chars)                 |
                |------------------------------------------------|
                |                 Port (5 Chars)                 |
                |________________________________________________|
                
                For sending IP/Port of the current node to the root to ask if it can register to network or not.

            Response:
        
                                 ** Body Format **
                 _________________________________________________
                |                  RES (3 Chars)                  |
                |-------------------------------------------------|
                |                  ACK (3 Chars)                  |
                |_________________________________________________|
                
                For now only should just send an 'ACK' from the root to inform a node that it
                has been registered in the root if the 'Register Request' was successful.
                
        Advertise:
            Request:
            
                                ** Body Format **
                 ________________________________________________
                |                  REQ (3 Chars)                 |
                |________________________________________________|
                
                Nodes for finding the IP/Port of their neighbour peer must send this packet to the root.

            Response:

                                ** Packet Format **
                 ________________________________________________
                |                RES(3 Chars)                    |
                |------------------------------------------------|
                |              Server IP (15 Chars)              |
                |------------------------------------------------|
                |             Server Port (5 Chars)              |
                |________________________________________________|
                
                Root will response Advertise Request packet with sending IP/Port of the requester peer in this packet.
                
        Join:

                                ** Body Format **
                 ________________________________________________
                |                 JOIN (4 Chars)                 |
                |________________________________________________|
            
            New node after getting Advertise Response from root must send this packet to the specified peer
            to tell him that they should connect together; When receiving this packet we should update our
            Client Dictionary in the Stream object.


            
        Message:
                                ** Body Format **
                 ________________________________________________
                |             Message (#Length Chars)            |
                |________________________________________________|

            The message that want to broadcast to hole network. Right now this type only includes a plain text.
        
        Reunion:
            Hello:
        
                                ** Body Format **
                 ________________________________________________
                |                  REQ (3 Chars)                 |
                |------------------------------------------------|
                |           Number of Entries (2 Chars)          |
                |------------------------------------------------|
                |                 IP0 (15 Chars)                 |
                |------------------------------------------------|
                |                Port0 (5 Chars)                 |
                |------------------------------------------------|
                |                 IP1 (15 Chars)                 |
                |------------------------------------------------|
                |                Port1 (5 Chars)                 |
                |------------------------------------------------|
                |                     ...                        |
                |------------------------------------------------|
                |                 IPN (15 Chars)                 |
                |------------------------------------------------|
                |                PortN (5 Chars)                 |
                |________________________________________________|
                
                In every interval (for now 20 seconds) peers must send this message to the root.
                Every other peer that received this packet should append their (IP, port) to
                the packet and update Length.

            Hello Back:
        
                                    ** Body Format **
                 ________________________________________________
                |                  REQ (3 Chars)                 |
                |------------------------------------------------|
                |           Number of Entries (2 Chars)          |
                |------------------------------------------------|
                |                 IPN (15 Chars)                 |
                |------------------------------------------------|
                |                PortN (5 Chars)                 |
                |------------------------------------------------|
                |                     ...                        |
                |------------------------------------------------|
                |                 IP1 (15 Chars)                 |
                |------------------------------------------------|
                |                Port1 (5 Chars)                 |
                |------------------------------------------------|
                |                 IP0 (15 Chars)                 |
                |------------------------------------------------|
                |                Port0 (5 Chars)                 |
                |________________________________________________|

                Root in an answer to the Reunion Hello message will send this packet to the target node.
                In this packet, all the nodes (IP, port) exist in order by path traversal to target.
            
    
"""
import socket
import struct
from typing import List

from src.tools.parsers import parse_ip, parse_port
from src.tools.type_repo import Address

VERSION = 1
REGISTER = 1
ADVERTISE = 2
JOIN = 3
MESSAGE = 4
REUNION = 5


class Packet:
    def __init__(self, version: int, packet_type: int, length: int, source_ip: str, source_port: int,
                 body: str):
        """
        The decoded buffer should convert to a new packet.
        """
        self.version = version
        self.packet_type = packet_type
        self.length = length
        self.source_ip = source_ip
        self.source_port = source_port
        self.body = body

    def get_header(self) -> str:
        """

        :return: Packet header
        :rtype: str
        """
        return f'Version:{self.version},Type:{self.packet_type},Length:{self.length}'

    def get_version(self) -> int:
        """

        :return: Packet Version
        :rtype: int
        """
        return self.version

    def get_type(self) -> int:
        """

        :return: Packet type
        :rtype: int
        """
        return self.packet_type

    def get_length(self) -> int:
        """

        :return: Packet length
        :rtype: int
        """
        return self.length

    def get_body(self) -> str:
        """

        :return: Packet body
        :rtype: str
        """
        return self.body

    def get_buf(self) -> bytearray:
        """
        In this function, we will make our final buffer that represents the Packet with the Struct class methods.

        :return The parsed packet to the network format.
        :rtype: bytearray
        """
        ip = [int(part) for part in self.source_ip.split('.')]
        return bytearray(
            struct.pack(f'!HHLHHHHL{len(self.body)}s', self.version, self.packet_type, self.length, ip[0], ip[1], ip[2],
                        ip[3], self.source_port, bytes(self.body, 'utf-8')))

    def get_source_server_ip(self) -> str:
        """

        :return: Server IP address for the sender of the packet.
        :rtype: str
        """
        return self.source_ip

    def get_source_server_port(self) -> int:
        """

        :return: Server Port address for the sender of the packet.
        :rtype: int
        """
        return self.source_port

    def get_source_server_address(self) -> Address:
        """

        :return: Server address; The format is like ('192.168.001.001', 05335).
        :rtype: tuple
        """
        return self.source_ip, self.source_port


class PacketFactory:
    """
    This class is only for making Packet objects.
    """

    @staticmethod
    def parse_buffer(buffer: bytearray) -> Packet:
        """
        In this function we will make a new Packet from input buffer with struct class methods.

        :param buffer: The buffer that should be parse to a validate packet format

        :return new packet
        :rtype: Packet

        """
        header = buffer[:20]
        body = buffer[20:]
        version, packet_type, length = struct.unpack('!HHI', header[:8])
        # Choose odd bytes of the 8 bytes of ip because ip is 4 bytes
        source_ip = socket.inet_ntoa(header[8:16][1::2])
        source_port = struct.unpack('!I', header[16:20])[0]
        body_chars = struct.unpack(f'{len(body)}s', body)[0].decode('utf-8')
        return Packet(version, packet_type, length, source_ip, source_port, body_chars)

    @staticmethod
    def new_reunion_packet(reunion_type: str, source_address: Address, nodes_array: List[Address]) -> Packet:
        """
        :param reunion_type: Reunion Hello (REQ) or Reunion Hello Back (RES)
        :param source_address: IP/Port address of the packet sender.
        :param nodes_array: [(ip0, port0), (ip1, port1), ...] It is the path to the 'destination'.

        :type reunion_type: str
        :type source_address: tuple
        :type nodes_array: list

        :return New reunion packet.
        :rtype Packet
        """
        n_entries = len(nodes_array)
        body = reunion_type + str(n_entries)
        for node in nodes_array:
            body += (parse_ip(node[0]) + parse_port(node[1]))
        length = len(body)
        return Packet(VERSION, REUNION, length, source_address[0], source_address[1], body)

    @staticmethod
    def new_advertise_packet(packet_type: str, source_server_address: Address, neighbour: Address = None) -> Packet:
        """
        :param packet_type: Type of Advertise packet
        :param source_server_address Server address of the packet sender.
        :param neighbour: The neighbour for advertise response packet; The format is like ('192.168.001.001', '05335').

        :type packet_type: str
        :type source_server_address: tuple
        :type neighbour: tuple

        :return New advertise packet.
        :rtype Packet

        """
        pass

    @staticmethod
    def new_join_packet(source_server_address: Address) -> Packet:
        """
        :param source_server_address: Server address of the packet sender.

        :type source_server_address: tuple

        :return New join packet.
        :rtype Packet

        """
        pass

    @staticmethod
    def new_register_packet(register_type: str, source_server_address: Address,
                            address: Address = None) -> Packet:
        """
        :param register_type: Type of Register packet
        :param source_server_address: Server address of the packet sender.
        :param address: If 'type' is 'request' we need an address; The format is like ('192.168.001.001', '05335').

        :type register_type: str
        :type source_server_address: tuple
        :type address: tuple

        :return New Register packet.
        :rtype Packet

        """
        body = 'REQ' + parse_ip(address[0]) + parse_port(address[1]) \
            if register_type == 'request' else 'RES' + 'ACK'
        length = len(body)
        return Packet(VERSION, REGISTER, length, source_server_address[0], source_server_address[1], body)

    @staticmethod
    def new_message_packet(message: str, source_server_address: Address) -> Packet:
        """
        Packet for sending a broadcast message to the whole network.

        :param message: Our message
        :param source_server_address: Server address of the packet sender.

        :type message: str
        :type source_server_address: tuple

        :return: New Message packet.
        :rtype: Packet
        """
        length = len(message)
        return Packet(VERSION, MESSAGE, length, source_server_address[0], source_server_address[1], message)
