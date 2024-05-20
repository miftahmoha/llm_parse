# from cfg_parser import connect_symbol_graph, construct_symbol_subgraph
from cfg_parser.base import OrderedSet, Symbol
from cfg_parser.functions import get_symbols_from_generated_symbol_graph

import networkx as nx
import matplotlib.pyplot as plt


def draw_symbol_graph(symbol_graph: dict[Symbol, OrderedSet[Symbol]]):
    G = nx.DiGraph()
    symbols = get_symbols_from_generated_symbol_graph(symbol_graph)
    labels = {}

    for symbol in symbols.values():
        G.add_node(symbol)
        labels[symbol] = symbol.content

    for symbol, connections in symbol_graph.items():
        for connection in connections:
            G.add_edge(symbol, connection)

    # Set the figure size
    plt.figure(figsize=(5, 5))

    pos = nx.nx_agraph.graphviz_layout(G, prog="dot")

    # Use graphviz to layout the nodes
    nx.draw(
        G,
        pos,
        with_labels=True,
        labels=labels,
        node_color="lightblue",
        edge_color="gray",
    )

    plt.show()


# if __name__ == "__main__":

#     symbol_graph_left = construct_symbol_subgraph(
#         """ factor "+" | factor "-" """.split()
#     )
#     symbol_graph_right = construct_symbol_subgraph(
#         """ Regex([0-9]*.[0-9]*) | "-" factor |  "(" expression ")" """.split()
#     )
#     generated_symbol_graph_output = connect_symbol_graph(
#         symbol_graph_left, symbol_graph_right
#     )

#     draw_symbol_graph(generated_symbol_graph_output)
