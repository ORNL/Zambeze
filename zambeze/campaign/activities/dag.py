import networkx as nx


class DAG(nx.DiGraph):
    def __init__(self, **attr):
        super().__init__(**attr)

    def validate_dag(self):
        if nx.is_directed_acyclic_graph(self):
            is_valid_dag = True
        else:
            is_valid_dag = False
        return is_valid_dag
