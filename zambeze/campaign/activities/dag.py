
import dill
import networkx as nx


class DAG(nx.DiGraph):
    def __init__(self, **attr):
        super().__init__(**attr)

    def validate_dag(self):
        return nx.is_directed_acyclic_graph(self)

    def serialize_dag(self):
        # Serialize the DAG to a file using dill
        return dill.dumps(self)

    @staticmethod
    def deserialize_dag(byte_data):
        # Deserialize a DAG object from a file using dill
        return dill.loads(byte_data)

    def serialize_node(self, node):
        # Serialize an individual node to a dill byte string
        if node in self:
            node_data = self.nodes[node]
            return dill.dumps((node, node_data))
        else:
            raise ValueError("Node does not exist in the DAG.")

    @staticmethod
    def deserialize_node(byte_data):
        # Deserialize a node from a dill byte string and add it to the DAG
        node = dill.loads(byte_data)
        return node

    def update_node_relationships(self):
        # Update each node to include its predecessors and successors
        for node in self.nodes():
            self.nodes[node]["predecessors"] = list(self.predecessors(node))
            self.nodes[node]["successors"] = list(self.successors(node))

    def get_node_ids(self):
        # Return a list of all node IDs in the DAG
        return list(self.nodes())