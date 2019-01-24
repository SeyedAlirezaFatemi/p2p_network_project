import time
from typing import List, Optional

from src.tools.logger import log
from src.tools.parsers import parse_ip
from src.tools.type_repo import Address


class GraphNode:
    def __init__(self, address: Address):
        self.address = address
        self.parent: GraphNode = None
        self.children: List[GraphNode] = []
        self.level: int = None
        self.is_alive = False
        self.last_hello = None

    def set_parent(self, parent: 'GraphNode') -> None:
        self.parent = parent
        self.keep_alive()

    def keep_alive(self):
        self.is_alive = True
        self.last_hello = time.time()

    def set_address(self, new_address: Address) -> None:
        self.address = new_address

    def set_level(self, level: int) -> None:
        self.level = level

    def __reset(self) -> None:
        self.parent = None
        self.children = []
        self.is_alive = False

    def add_child(self, child: 'GraphNode') -> None:
        if len(self.children) < 2:
            self.children.append(child)
        else:
            # Something went wrong
            log('The Network is not working properly.')

    def hello(self):
        self.last_hello = time.time()

    def __eq__(self, other) -> bool:
        return self.address == other.address

    def __str__(self) -> str:
        return self.address.__str__()


def check_is_parent(child: GraphNode, parent: GraphNode) -> bool:
    while True:
        child = child.parent
        if child is None:
            return False
        elif child == parent:
            return True


class NetworkGraph:
    def __init__(self, root: GraphNode):
        self.root = root
        root.keep_alive()
        root.alive = True
        self.nodes = [root]

    def find_live_node(self, sender: Address) -> Optional[Address]:
        """
        Here we should find a neighbour for the sender.
        Best neighbour is the node who is nearest the root and has not more than one child.

        Code design suggestion:
            1. Do a BFS algorithm to find the target.

        Warnings:
            1. Check whether there is sender node in our NetworkGraph or not; if exist do not return sender node or
               any other nodes in it's sub-tree.

        :param sender: The node address we want to find best neighbour for it.
        :type sender: tuple

        :return: Best neighbour for sender.
        :rtype: GraphNode
        """
        graph: List[GraphNode] = []
        visited = {}
        # Create a queue for BFS
        # Mark the source node as visited and enqueue it
        queue: List[GraphNode] = [self.root]
        visited[self.root.address] = True
        while queue:
            # Dequeue a vertex from queue and print it
            node = queue.pop(0)
            graph.append(node)
            # Get all adjacent vertices of the dequeued vertex node
            # If a adjacent has not been visited, then mark it visited and enqueue it
            for child in node.children:
                if child.address not in visited or not visited[child.address]:
                    queue.append(child)
                    visited[child.address] = True
        sender_node = self.find_node(sender)  # For the warning
        for node in graph[::-1]:
            if node.level == 8 or len(node.children) == 2 or (not node.is_alive) or (
                    sender_node and check_is_parent(node, sender_node)) or sender == node.address:
                continue
            return node.address
        log('Network is full.')

    def find_node(self, node_address: Address) -> Optional[GraphNode]:
        for node in self.nodes:
            if node_address == node.address:
                return node

    def turn_on_node(self, node_address: Address) -> None:
        self.find_node(node_address).is_alive = True

    def turn_off_node(self, node_address: Address) -> None:
        self.find_node(node_address).is_alive = False

    def remove_node(self, node_address: Address) -> None:
        log(f'Node({node_address}) was REMOVED.')
        node = self.find_node(node_address)
        self.turn_off_subtree(node)
        node.parent.children.remove(node)
        self.nodes.remove(node)

    def turn_off_subtree(self, node: GraphNode):
        parents = [node]
        while True and len(parents) != 0:
            parent = parents[0]
            if parent:
                for child in parent.children:
                    child.is_alive = False
                    parents.append(child)
                    log(f'Node({child}) was turned OFF.')
                parents.remove(parent)

    def add_node(self, ip: str, port: int, father_address: Address) -> None:
        """
        Add a new node with node_address if it does not exist in our NetworkGraph and set its father.

        Warnings:
            1. Don't forget to set the new node as one of the father_address children.
            2. Before using this function make sure that there is a node which has father_address.

        :param ip: IP address of the new node.
        :param port: Port of the new node.
        :param father_address: Father address of the new node

        :type ip: str
        :type port: int
        :type father_address: tuple


        :return:
        """
        father_node = self.find_node(father_address)
        new_node_address=(parse_ip(ip), port)
        old_graph_node = self.find_node(new_node_address)
        if old_graph_node:
            old_graph_node.keep_alive()
            old_graph_node.set_parent(father_node)
            if father_node == self.root:
                old_graph_node.set_level(1)
            else:
                old_graph_node.set_level(father_node.level + 1)
            father_node.add_child(old_graph_node)
            return
        new_node = GraphNode(new_node_address)
        new_node.set_parent(father_node)
        if father_node == self.root:
            new_node.set_level(1)
        else:
            new_node.set_level(father_node.level + 1)
        father_node.add_child(new_node)
        self.nodes.append(new_node)

    def keep_alive(self, address: Address) -> None:
        graph_node = self.find_node(address)
        graph_node.keep_alive()
