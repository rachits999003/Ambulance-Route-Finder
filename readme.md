# 🚑 Ambulance Route Finder

A Python-based GUI application that calculates the shortest route for an ambulance using **Dijkstra's algorithm**. Ideal for emergency systems and simulations, this tool finds the quickest path between two points in a city road network.

---

## 🧠 Features

- Graph-based road mapping using `networkx`
- Fast and accurate shortest path calculation (Dijkstra's algorithm)
- User-friendly GUI built with `tkinter`
- Customizable road network
- (Optional) Graph visualization using `matplotlib`

---

## 📦 Requirements

Make sure Python 3.7+ is installed. Then install the required libraries:

```bash
pip install networkx matplotlib
```

🖥️ Usage
Enter the start location (e.g., A).

Enter the destination location (e.g., E).

Click "Find Best Route".

The optimal path and total distance will be displayed.

Optionally, view a visualized graph of the path.

🗺️ Sample Road Graph
```
A --4--> B --2--> C
 \        |
  \       v
   >--5--> C
```
🛠️ Future Improvements
Real-time GPS integration

Traffic-based dynamic weights

Map overlay using OpenStreetMap or Google Maps

Voice input for hands-free operation

🧠 Algorithm
This project uses Dijkstra’s algorithm, a greedy method to compute the shortest path from a source node to all other nodes in a weighted graph with non-negative edges.

💡 Inspiration
Designed to simulate emergency route optimization for smart cities and ambulance dispatch systems.

📜 License
This project is open-source and free to use under the MIT License.
