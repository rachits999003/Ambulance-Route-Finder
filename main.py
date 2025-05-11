import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os
import numpy as np
import folium
from folium import plugins
import osmnx as ox
import networkx as nx
import webbrowser
from shapely.geometry import Point
import geopandas as gpd
from functools import partial

class AmbulanceRouteFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("🚑 Shegaon Ambulance Route Finder")
        self.root.geometry("500x600")
        self.root.configure(bg="#f0f0f0")
        
        # Center coordinates for Shegaon
        self.shegaon_coords = (20.7937, 76.6994)  # More accurate coordinates
        self.graph = None
        self.current_route = None
        self.map_file = "shegaon_map.html"
        
        # Create a style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('Arial', 11))
        style.configure('TButton', font=('Arial', 11, 'bold'))
        
        self.create_widgets()
        self.load_map_data()
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(header_frame, text="Shegaon Ambulance Route Finder", 
                  font=('Arial', 16, 'bold')).pack()
        ttk.Label(header_frame, text="Find the fastest route for emergency services", 
                 font=('Arial', 10)).pack()
        
        # Map loading status
        self.status_var = tk.StringVar(value="Loading map data...")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground="#FF5722")
        self.status_label.pack(pady=(0, 10))
        
        # Progress bar for map loading
        self.progress = ttk.Progressbar(main_frame, orient=tk.HORIZONTAL, length=300, mode='indeterminate')
        self.progress.pack(pady=(0, 15))
        self.progress.start(10)
        
        # Location selection frame
        select_frame = ttk.LabelFrame(main_frame, text="Select Locations", padding=10)
        select_frame.pack(fill=tk.X, pady=5)
        
        # Define important locations in Shegaon
        self.locations = [
            ("Dr. Hedgewar Hospital", (20.7930, 76.6985)),
            ("Shree Gajanan Maharaj Mandir", (20.7937, 76.6994)),
            ("Bus Stand", (20.7940, 76.7010)),
            ("Shegaon Railway Station", (20.7970, 76.7000)),
            ("Main Bazaar", (20.7935, 76.7002)),
            ("Subhash Nagar", (20.7915, 76.6980)),
            ("Civil Hospital", (20.7945, 76.6970)),
            ("Shivaji Nagar", (20.7925, 76.7015)),
            ("Akot Road", (20.7960, 76.7020)),
            ("Gandhi Chowk", (20.7933, 76.6990))
        ]
        
        # Start location
        ttk.Label(select_frame, text="Emergency Start Point:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.start_var = tk.StringVar()
        self.start_combo = ttk.Combobox(select_frame, textvariable=self.start_var, 
                                      values=[loc[0] for loc in self.locations], state='readonly', width=25)
        self.start_combo.grid(row=0, column=1, padx=5, pady=5)
        self.start_combo.current(0)
        
        # Destination
        ttk.Label(select_frame, text="Emergency Destination:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.dest_var = tk.StringVar()
        self.dest_combo = ttk.Combobox(select_frame, textvariable=self.dest_var, 
                                     values=[loc[0] for loc in self.locations], state='readonly', width=25)
        self.dest_combo.grid(row=1, column=1, padx=5, pady=5)
        self.dest_combo.current(1)
        
        # Action buttons
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=15)
        
        # Find route button
        self.route_btn = ttk.Button(btn_frame, text="Find Fastest Route", command=self.find_route, state=tk.DISABLED)
        self.route_btn.pack(side=tk.LEFT, padx=5)
        
        # Simulate button
        self.sim_btn = ttk.Button(btn_frame, text="Simulate Ambulance", command=self.simulate_ambulance, state=tk.DISABLED)
        self.sim_btn.pack(side=tk.LEFT, padx=5)
        
        # View map button
        self.map_btn = ttk.Button(btn_frame, text="View Full Map", command=self.view_map, state=tk.DISABLED)
        self.map_btn.pack(side=tk.LEFT, padx=5)
        
        # Results frame
        result_frame = ttk.LabelFrame(main_frame, text="Route Information", padding=10)
        result_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Route info
        self.info_text = tk.Text(result_frame, height=8, width=50, wrap=tk.WORD, 
                               font=('Courier New', 10), bg='#f8f8f8')
        self.info_text.pack(fill=tk.BOTH, expand=True)
        self.info_text.insert(tk.END, "Map data loading... Please wait.")
        self.info_text.config(state=tk.DISABLED)
        
        # Ambulance status
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=10)
        
        self.ambulance_status = tk.StringVar(value="Ready to dispatch")
        status_label = ttk.Label(status_frame, textvariable=self.ambulance_status, 
                              font=('Arial', 12, 'bold'), foreground="#4CAF50")
        status_label.pack()
    
    def load_map_data(self):
        """Load OSM data in a separate thread to avoid freezing the UI"""
        self.loading_thread = threading.Thread(target=self._load_graph_data)
        self.loading_thread.daemon = True
        self.loading_thread.start()
    
    def _load_graph_data(self):
        """Background task to load the graph data"""
        try:
            # Define the bounding box for Shegaon with a larger area to ensure coverage
            north, south, east, west = 20.8037, 20.7837, 76.7094, 76.6894
            
            # Get the driving network - FIX HERE: Use a dictionary for the bbox
            # bbox = {'north': north, 'south': south, 'east': east, 'west': west}
            bbox = [north, south, east, west]
            self.graph = ox.graph_from_bbox(bbox, network_type='drive')


            # Project the graph to UTM
            self.graph_proj = ox.project_graph(self.graph)
            
            # Create the initial map and save it
            self._create_base_map()
            
            # Update UI from the main thread
            self.root.after(0, self._map_loaded)
        except Exception as e:
            error_msg = f"Error loading map data: {str(e)}"
            self.root.after(0, lambda msg=error_msg: self._show_error(msg))
    
    def _map_loaded(self):
        """Called when map is successfully loaded"""
        self.progress.stop()
        self.progress.pack_forget()
        self.status_var.set("Map data loaded successfully!")
        self.status_label.config(foreground="#4CAF50")
        
        # Enable buttons
        self.route_btn.config(state=tk.NORMAL)
        self.map_btn.config(state=tk.NORMAL)
        
        # Update info text
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, "Map loaded successfully. Select start and destination points to find a route.")
        self.info_text.config(state=tk.DISABLED)
    
    def _show_error(self, message):
        """Show error message on UI"""
        self.progress.stop()
        self.status_var.set("Error loading map")
        self.status_label.config(foreground="red")
        messagebox.showerror("Error", message)
    
    def _create_base_map(self):
        """Create and save the base map with location markers"""
        m = folium.Map(location=self.shegaon_coords, zoom_start=15, 
                     tiles="cartodbpositron")
        
        # Add all location markers
        for name, coords in self.locations:
            popup_text = f"<b>{name}</b>"
            folium.Marker(
                location=[coords[0], coords[1]],
                popup=popup_text,
                tooltip=name,
                icon=folium.Icon(icon="map-marker", prefix="fa", color="blue")
            ).add_to(m)
        
        # Save the map
        m.save(self.map_file)
    
    def find_route(self):
        """Find the fastest route between selected points"""
        start_name = self.start_var.get()
        dest_name = self.dest_var.get()
        
        if start_name == dest_name:
            messagebox.showwarning("Warning", "Start and destination cannot be the same.")
            return
            
        # Get coordinates for selected locations
        start_coords = next((loc[1] for loc in self.locations if loc[0] == start_name), None)
        dest_coords = next((loc[1] for loc in self.locations if loc[0] == dest_name), None)
        
        if not start_coords or not dest_coords:
            messagebox.showerror("Error", "Could not get coordinates for selected locations.")
            return
            
        try:
            # Find nearest network nodes to our points
            start_node = ox.distance.nearest_nodes(self.graph, X=start_coords[1], Y=start_coords[0])
            end_node = ox.distance.nearest_nodes(self.graph, X=dest_coords[1], Y=dest_coords[0])
            
            # Calculate shortest path using Dijkstra's algorithm
            route = nx.shortest_path(self.graph, start_node, end_node, weight='length')
            self.current_route = route
            
            # Get route length
            length_m = sum(ox.utils_graph.get_route_edge_attributes(self.graph, route, 'length'))
            length_km = length_m / 1000  # Convert to kilometers
            
            # Get route nodes coordinates
            route_coords = [(self.graph.nodes[node]['y'], self.graph.nodes[node]['x']) for node in route]
            
            # Calculate estimated travel time (assuming ambulance speed of 40 km/h average in town)
            ambulance_speed_kmh = 40
            travel_time_hours = length_km / ambulance_speed_kmh
            travel_time_mins = travel_time_hours * 60
            
            # Update info text
            self.info_text.config(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, f"Route from {start_name} to {dest_name}:\n\n")
            self.info_text.insert(tk.END, f"Distance: {length_km:.2f} km\n")
            self.info_text.insert(tk.END, f"Estimated travel time: {travel_time_mins:.1f} minutes\n")
            self.info_text.insert(tk.END, f"Number of turns: {len(route) - 2}\n\n")
            self.info_text.insert(tk.END, "Route created successfully. Click 'Simulate Ambulance' to visualize.")
            self.info_text.config(state=tk.DISABLED)
            
            # Create and display the route map
            self._create_route_map(route_coords, start_name, dest_name)
            
            # Enable simulation button
            self.sim_btn.config(state=tk.NORMAL)
            
            # Update ambulance status
            self.ambulance_status.set("Route calculated, ready for dispatch 🚑")
            
        except nx.NetworkXNoPath:
            messagebox.showerror("Error", "No route found between these locations.")
        except Exception as e:
            messagebox.showerror("Error", f"Error finding route: {str(e)}")
    
    def _create_route_map(self, route_coords, start_name, dest_name):
        """Create a map with the calculated route"""
        m = folium.Map(location=self.shegaon_coords, zoom_start=15, tiles="cartodbpositron")
        
        # Add all location markers
        for name, coords in self.locations:
            is_start = name == start_name
            is_dest = name == dest_name
            
            if is_start:
                icon_color = "green"
                icon_type = "ambulance"
            elif is_dest:
                icon_color = "red"
                icon_type = "plus"
            else:
                icon_color = "blue"
                icon_type = "map-marker"
                
            popup_text = f"<b>{name}</b>"
            if is_start:
                popup_text += " (START)"
            elif is_dest:
                popup_text += " (DESTINATION)"
                
            folium.Marker(
                location=[coords[0], coords[1]],
                popup=popup_text,
                tooltip=name,
                icon=folium.Icon(icon=icon_type, prefix="fa", color=icon_color)
            ).add_to(m)
        
        # Add the route as a line
        folium.PolyLine(
            route_coords,
            color="#FF5722",
            weight=5,
            opacity=0.8,
            tooltip="Emergency Route"
        ).add_to(m)
        
        # Save the map with route
        m.save(self.map_file)
        
        # Automatically open the map
        webbrowser.open('file://' + os.path.realpath(self.map_file))
    
    def simulate_ambulance(self):
        """Simulate ambulance movement along the route"""
        if not self.current_route:
            messagebox.showwarning("Warning", "Calculate a route first.")
            return
            
        # Update ambulance status
        self.ambulance_status.set("🚑 Ambulance dispatched!")
        
        # Disable buttons during simulation
        self.route_btn.config(state=tk.DISABLED)
        self.sim_btn.config(state=tk.DISABLED)
        
        # Start simulation in a separate thread
        sim_thread = threading.Thread(target=self._run_simulation)
        sim_thread.daemon = True
        sim_thread.start()
    
    def _run_simulation(self):
        """Run the ambulance movement simulation"""
        try:
            # Get route coordinates
            route_coords = [(self.graph.nodes[node]['y'], self.graph.nodes[node]['x']) for node in self.current_route]
            
            # Create a map for the simulation
            m = folium.Map(location=self.shegaon_coords, zoom_start=15, tiles="cartodbpositron")
            
            # Add the route line
            folium.PolyLine(
                route_coords,
                color="#FF5722",
                weight=5,
                opacity=0.8
            ).add_to(m)
            
            # Add destination marker
            dest_name = self.dest_var.get()
            dest_coords = next((loc[1] for loc in self.locations if loc[0] == dest_name), None)
            
            folium.Marker(
                location=dest_coords,
                popup=f"<b>{dest_name}</b> (DESTINATION)",
                tooltip=dest_name,
                icon=folium.Icon(icon="plus", prefix="fa", color="red")
            ).add_to(m)
            
            # Create a feature group for the ambulance marker
            ambulance_group = folium.FeatureGroup(name="Ambulance")
            m.add_child(ambulance_group)
            
            # Create an icon for the ambulance
            ambulance_icon = folium.features.CustomIcon(
                "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
                icon_size=(25, 41)
            )
            
            # Simulate movement
            steps = min(10, len(route_coords))  # Use at most 10 steps to avoid too slow simulation
            step_indices = np.linspace(0, len(route_coords) - 1, steps).astype(int)
            
            for i, idx in enumerate(step_indices):
                # Update status message
                progress = int((i + 1) / steps * 100)
                status_msg = f"🚑 Ambulance en route: {progress}% complete"
                
                # Update UI from the main thread - use partial to avoid scope issues
                self.root.after(0, partial(self.ambulance_status.set, status_msg))
                
                # Add the ambulance marker at the current position
                ambulance_group.add_child(
                    folium.Marker(
                        location=route_coords[idx],
                        tooltip="Ambulance",
                        icon=ambulance_icon
                    )
                )
                
                # Save and refresh the map
                m.save(self.map_file)
                
                # Make sure to not sleep after the last step
                if i < len(step_indices) - 1:
                    time.sleep(1)
                    
                # Clear the ambulance marker for the next step
                if i < len(step_indices) - 1:  # Don't clear on the last step
                    for child in list(ambulance_group._children.values()):
                        ambulance_group._children.pop(child._name)
            
            # Final status update
            self.root.after(0, partial(self.ambulance_status.set, "🎯 Ambulance arrived at destination!"))
            
            # Re-enable buttons
            self.root.after(0, partial(self.route_btn.config, state=tk.NORMAL))
            self.root.after(0, partial(self.sim_btn.config, state=tk.NORMAL))
            
        except Exception as e:
            error_msg = f"Simulation error: {str(e)}"
            self.root.after(0, lambda msg=error_msg: messagebox.showerror("Error", msg))
            self.root.after(0, partial(self.route_btn.config, state=tk.NORMAL))
            self.root.after(0, partial(self.sim_btn.config, state=tk.NORMAL))
    
    def view_map(self):
        """Open the current map in web browser"""
        # Ensure the map file exists
        if not os.path.exists(self.map_file):
            self._create_base_map()
        
        # Open in browser
        webbrowser.open('file://' + os.path.realpath(self.map_file))

if __name__ == "__main__":
    root = tk.Tk()
    app = AmbulanceRouteFinder(root)
    root.mainloop()