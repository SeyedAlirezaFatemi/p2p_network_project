# import time
from typing import List

from src.tools.type_repo import Address


class GraphNode:
    def __init__(self, address: Address):
        """
        :param address: (ip, port)
        :type address: tuple
        """
        self.address = address
        self.parent = None
        self.children = []

    def set_parent(self, parent):
        self.parent = parent

    def set_address(self, new_address: Address):
        self.address = new_address

    def __reset(self):
        self.parent = None
        self.children = []

    def add_child(self, child):
        self.children.append(child)

    def __eq__(self, other):
        return self.address == other.address

    def __str__(self):
        return self.address.__str__()


class NetworkGraph:
    def __init__(self, root: GraphNode):
        self.root = root
        root.alive = True
        self.nodes = [root]

    def find_live_node(self, sender: Address) -> GraphNode:
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
        # TODO: Not done yet

    def find_node(self, node_address: Address) -> GraphNode:
        for node in self.nodes:
            if node_address == node.address:
                return node

    def turn_on_node(self, node_address: Address):
        pass

    def turn_off_node(self, node_address: Address):
        pass

    def remove_node(self, node_address: Address):
        self.nodes.remove(self.find_node(node_address))

    def add_node(self, ip: str, port: int, father_address: Address):
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
        pass
