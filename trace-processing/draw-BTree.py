import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# Read CSV file
df = pd.read_csv('btree-tiny.csv')

# Create a directed graph
G = nx.DiGraph()

# Add nodes and edges to the graph
for index, row in df.iterrows():
    node_id = row['node_address']
    parent_id = row['parent_address']
    G.add_node(node_id)
    if not pd.isnull(parent_id):
        G.add_edge(parent_id, node_id)

# Draw the tree
pos = nx.spring_layout(G)  # You can choose a different layout if needed
nx.draw(G, pos, with_labels=True, font_weight='bold', node_size=700, node_color='skyblue', font_size=8, arrows=True)

# Save the plot to a file (e.g., PNG, PDF, etc.)
plt.savefig('BTree_plot.png')

# Show the plot
plt.show()
