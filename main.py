import tkinter as tk
from tkinter import messagebox
import networkx as nx
import matplotlib.pyplot as plt
import threading
import time


# ----------- Create the graph ----------- #
G = nx.Graph()

# Example graph edges with weights (customize this!)
edges = [
    ("A", "B", 4),
    ("A", "C", 5),
    ("B", "C", 2),
    ("B", "D", 7),
    ("C", "D", 6),
    ("C", "E", 3),
    ("D", "E", 1)
]

G.add_weighted_edges_from(edges)

# ----------- Thread for Simulating Movement ----------- #
def simulate_ambulance_movement(path):
    for location in path:
        result_label.config(text=f"Ambulance at: {location} 🚑")

        root.update()  # Refresh the GUI
        time.sleep(1.5)  # Wait 1.5 sec before moving to next location
    result_label.config(text=f"Ambulance reached destination: {path[-1]} 🎯")

# ----------- Dijkstra Function ----------- #
def find_best_route():
    start = start_entry.get().strip().upper()
    dest = dest_entry.get().strip().upper()

    if start not in G.nodes or dest not in G.nodes:
        messagebox.showerror("Invalid Input", "Start or destination not found in the map.")
        return

    try:
        path = nx.dijkstra_path(G, start, dest)
        distance = nx.dijkstra_path_length(G, start, dest)
        result = f"Best Route: {' → '.join(path)}\nTotal Distance: {distance}"
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

tk.Label(root, text="Start Location:").pack(pady=(10, 0))
start_entry = tk.Entry(root, width=30)
start_entry.pack(pady=5)

tk.Label(root, text="Destination Location:").pack()
dest_entry = tk.Entry(root, width=30)
dest_entry.pack(pady=5)

tk.Button(root, text="Find Best Route", command=find_best_route, bg="#4CAF50", fg="white").pack(pady=10)
tk.Button(root, text="Show Map", command=show_map, bg="#2196F3", fg="white").pack()

result_label = tk.Label(root, text="", wraplength=400, justify="center", fg="darkblue", font=("Arial", 10))
result_label.pack(pady=15)

root.mainloop()
