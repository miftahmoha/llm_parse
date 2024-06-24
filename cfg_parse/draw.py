import matplotlib.pyplot as plt
import networkx as nx

from cfg_parse.base import Symbol, SymbolGraph, SymbolType
from cfg_parse.cfg_build.helpers import get_symbols_from_generated_symbol_graph


def draw_symbol_graph(symbol_graph: SymbolGraph):
    G = nx.DiGraph()

    symbol_graph_copy = symbol_graph.copy()

    symbols = get_symbols_from_generated_symbol_graph(symbol_graph_copy)

    # Adding initials and finals as `Symbols` for visual purposes.
    symbol_special_initials, symbol_special_finals = Symbol(
        "INITIALS", SymbolType.SPECIAL
    ), Symbol("FINALS", SymbolType.SPECIAL)
    symbols["INITIALS"], symbols["FINALS"] = (
        symbol_special_initials,
        symbol_special_finals,
    )

    # Adding the connections.
    (
        symbol_graph_copy.nodes[symbol_special_initials],
        symbol_graph_copy.nodes[symbol_special_finals],
    ) = (symbol_graph_copy.initials, symbol_graph_copy.finals)

    labels = {}

    for symbol in symbols.values():
        G.add_node(symbol)
        labels[symbol] = symbol.content

    for symbol, connections in symbol_graph_copy.nodes.items():
        for connection in connections:
            G.add_edge(symbol, connection)

    # Setting the figure size.
    plt.figure(figsize=(5, 5))

    pos = nx.nx_agraph.graphviz_layout(G, prog="dot")

    # Using graphviz to layout the nodes.
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
