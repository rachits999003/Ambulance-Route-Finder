import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import networkx as nx
import matplotlib.pyplot as plt
import threading
import time
import osmnx as ox

# ----------- Get Shegaon Map ----------- #
def get_shegown_map():
    # Get the graph for Shegaon, Maharashtra, India
    place_name = "Shegaon, Maharashtra, India"
    graph = ox.graph_from_place(place_name, network_type='all')
    return graph

# ----------- Create the graph ----------- #
G = get_shegown_map()
print(nx.info(G))

# ----------- Thread for Simulating Movement ----------- #
def simulate_ambulance_movement(path):
    for location in path:
        result_label.config(text=f"Ambulance at: {location} 🚑")

        root.after(1500, root.update)  # Refresh the GUI
        time.sleep(1.5)  # Wait 1.5 sec before moving to next location
    result_label.config(text=f"Ambulance reached destination: {path[-1]} 🎯")

# ----------- Dijkstra Function ----------- #
def find_best_route():
    start = start_var.get()
    dest = dest_var.get()

    # Convert location names to nearest nodes in the graph
    start_node = ox.distance.nearest_nodes(G, X=start[1], Y=start[0])
    dest_node = ox.distance.nearest_nodes(G, X=dest[1], Y=dest[0])

    if start_node not in G.nodes or dest_node not in G.nodes:
        messagebox.showerror("Invalid Input", "Start or destination not found in the map.")
        return

    try:
        path = nx.dijkstra_path(G, start_node, dest_node)
        distance = nx.dijkstra_path_length(G, start_node, dest_node)
        result = f"Best Route: {' → '.join(map(str, path))}\nTotal Distance: {distance}"
        result_label.config(text=result)

        # Run ambulance movement in separate thread so GUI doesn't freeze
        threading.Thread(target=simulate_ambulance_movement, args=(path,), daemon=True).start()

    except nx.NetworkXNoPath:
        result_label.config(text="No path found between the selected locations.")

# ----------- Optional Graph Visualization ----------- #
def show_map():
    pos = nx.spring_layout(G)
    edge_labels = nx.get_edge_attributes(G, 'weight')

    plt.figure(figsize=(6, 4))
    nx.draw(G, pos, with_labels=True, node_color='lightblue', edge_color='gray', node_size=1500, font_size=10)
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
    plt.title("City Road Map")
    plt.show()

# ----------- GUI ----------- #
root = tk.Tk()
root.title("🚑 Ambulance Route Finder")
root.geometry("420x300")
root.resizable(False, False)

# Define start and destination locations as tuples of (latitude, longitude)
nodes = [
    ("Dr. Hedgewar Hospital", (20.5316, 76.5779)),
    ("Shree Gajanan Maharaj Mandir", (20.5333, 76.5795)),
    ("Bus Stand", (20.5311, 76.5785)),
    ("Shegaon Railway Station", (20.5375, 76.5802)),
    ("Main Bazaar", (20.5361, 76.5787)),
    ("Subhash Nagar", (20.5324, 76.5776)),
    ("Civil Hospital", (20.5336, 76.5788)),
    ("Shivaji Nagar", (20.5350, 76.5773))
]

# Initialize variables for selected start and destination
start_var = tk.StringVar()
dest_var = tk.StringVar()

# Populate the combo boxes
start_menu = ttk.Combobox(root, textvariable=start_var, values=[node[0] for node in nodes], state='readonly')
start_menu.pack(pady=5)

dest_menu = ttk.Combobox(root, textvariable=dest_var, values=[node[0] for node in nodes], state='readonly')
dest_menu.pack(pady=5)

tk.Button(root, text="Find Best Route", command=find_best_route, bg="#4CAF50", fg="white").pack(pady=10)
tk.Button(root, text="Show Map", command=show_map, bg="#2196F3", fg="white").pack()

result_label = tk.Label(root, text="", wraplength=400, justify="center", fg="darkblue", font=("Arial", 10))
result_label.pack(pady=15)

root.mainloop()
