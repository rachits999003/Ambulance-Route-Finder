import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import os
import webbrowser
import folium
import random
import math
from functools import partial

class AmbulanceRouteFinder:
    def __init__(self, root):
        self.root = root
        self.root.title("🚑 Shegaon Ambulance Route Finder")
        self.root.geometry("500x600")
        self.root.configure(bg="#f0f0f0")
        
        # Center coordinates for Shegaon
        self.shegaon_coords = (20.7937, 76.6994)
        self.current_route = None
        self.map_file = "shegaon_map.html"
        
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
        
        # Virtual road network (simplified)
        self.road_network = self._create_dummy_road_network()
        
        # Create a style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('Arial', 11))
        style.configure('TButton', font=('Arial', 11, 'bold'))
        
        self.create_widgets()
        
        # Load dummy map data (much faster)
        self.load_dummy_map_data()
    
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
    
    def _create_dummy_road_network(self):
        """Create a simplified dummy road network based on known locations"""
        road_network = {}
        
        # For each location, create connections to 3-5 nearest locations
        for name1, coords1 in self.locations:
            # Find distances to all other locations
            distances = []
            for name2, coords2 in self.locations:
                if name1 != name2:
                    # Calculate distance between locations
                    dist = self._haversine_distance(coords1, coords2)
                    distances.append((name2, dist))
            
            # Sort by distance
            distances.sort(key=lambda x: x[1])
            
            # Connect to 3-5 nearest locations
            num_connections = random.randint(3, min(5, len(distances)))
            road_network[name1] = [(name2, dist) for name2, dist in distances[:num_connections]]
            
        return road_network
    
    def _haversine_distance(self, coord1, coord2):
        """Calculate the distance between two coordinates in km"""
        # Radius of the Earth in km
        R = 6371.0
        
        # Convert coordinates to radians
        lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
        lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
        
        # Differences
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        # Haversine formula
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        # Distance in km
        distance = R * c
        
        return distance
    
    def load_dummy_map_data(self):
        """Simulate loading map data with a short delay"""
        self.loading_thread = threading.Thread(target=self._simulate_loading)
        self.loading_thread.daemon = True
        self.loading_thread.start()
    
    def _simulate_loading(self):
        """Simulate loading process with a short delay"""
        try:
            # Create the road network (already done in init)
            self._create_base_map()
            
            # Artificial delay to simulate loading (much shorter)
            time.sleep(1.0)
            
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
        
        # Add roads (simplified)
        added_roads = set()  # Keep track of roads we've already added
        
        for name1, connections in self.road_network.items():
            coords1 = next((loc[1] for loc in self.locations if loc[0] == name1), None)
            
            for name2, _ in connections:
                # Create a unique road identifier
                road_id = tuple(sorted([name1, name2]))
                
                # Skip if we've already added this road
                if road_id in added_roads:
                    continue
                    
                coords2 = next((loc[1] for loc in self.locations if loc[0] == name2), None)
                
                # Add the road line
                if coords1 and coords2:
                    folium.PolyLine(
                        [coords1, coords2],
                        color="gray",
                        weight=2,
                        opacity=0.7
                    ).add_to(m)
                    
                    # Mark as added
                    added_roads.add(road_id)
        
        # Save the map
        m.save(self.map_file)
    
    def _dijkstra(self, start, end):
        """
        Find shortest path using Dijkstra's algorithm.
        This is a simplified version for our dummy network.
        """
        # Initialize distances with infinity for all nodes except start
        distances = {loc[0]: float('infinity') for loc in self.locations}
        distances[start] = 0
        
        # Track previous nodes for path reconstruction
        previous = {loc[0]: None for loc in self.locations}
        
        # Unvisited nodes
        unvisited = set(loc[0] for loc in self.locations)
        
        while unvisited:
            # Find unvisited node with minimum distance
            current = min(unvisited, key=lambda x: distances[x])
            
            # If we reached the end or no path exists
            if current == end or distances[current] == float('infinity'):
                break
                
            # Remove current from unvisited
            unvisited.remove(current)
            
            # Check all neighbors of current
            if current in self.road_network:
                for neighbor, distance in self.road_network[current]:
                    # Calculate potential new distance
                    new_distance = distances[current] + distance
                    
                    # Update if shorter path found
                    if new_distance < distances[neighbor]:
                        distances[neighbor] = new_distance
                        previous[neighbor] = current
        
        # Reconstruct path
        path = []
        current = end
        
        while current:
            path.append(current)
            current = previous[current]
            
        # Reverse to get path from start to end
        path.reverse()
        
        # Check if path exists
        if path[0] != start:
            return None, float('infinity')
            
        return path, distances[end]
    
    def find_route(self):
        """Find the fastest route between selected points"""
        start_name = self.start_var.get()
        dest_name = self.dest_var.get()
        
        if start_name == dest_name:
            messagebox.showwarning("Warning", "Start and destination cannot be the same.")
            return
        
        try:
            # Find route using our simplified Dijkstra
            route, distance = self._dijkstra(start_name, dest_name)
            
            if not route:
                messagebox.showerror("Error", "No route found between these locations.")
                return
                
            self.current_route = route
            
            # Get route coordinates
            route_coords = [next((loc[1] for loc in self.locations if loc[0] == name), None) for name in route]
            
            # Calculate estimated travel time (assuming ambulance speed of 40 km/h average in town)
            ambulance_speed_kmh = 40
            travel_time_hours = distance / ambulance_speed_kmh
            travel_time_mins = travel_time_hours * 60
            
            # Update info text
            self.info_text.config(state=tk.NORMAL)
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, f"Route from {start_name} to {dest_name}:\n\n")
            self.info_text.insert(tk.END, f"Path: {' → '.join(route)}\n\n")
            self.info_text.insert(tk.END, f"Distance: {distance:.2f} km\n")
            self.info_text.insert(tk.END, f"Estimated travel time: {travel_time_mins:.1f} minutes\n")
            self.info_text.insert(tk.END, f"Number of stops: {len(route) - 2}\n\n")
            self.info_text.insert(tk.END, "Route created successfully. Click 'Simulate Ambulance' to visualize.")
            self.info_text.config(state=tk.DISABLED)
            
            # Create and display the route map
            self._create_route_map(route_coords, start_name, dest_name)
            
            # Enable simulation button
            self.sim_btn.config(state=tk.NORMAL)
            
            # Update ambulance status
            self.ambulance_status.set("Route calculated, ready for dispatch 🚑")
            
        except Exception as e:
            messagebox.showerror("Error", f"Error finding route: {str(e)}")
    
    def _create_route_map(self, route_coords, start_name, dest_name):
        """Create a map with the calculated route"""
        m = folium.Map(location=self.shegaon_coords, zoom_start=15, tiles="cartodbpositron")
        
        # Add all location markers
        for name, coords in self.locations:
            is_start = name == start_name
            is_dest = name == dest_name
            is_route = name in self.current_route and not (is_start or is_dest)
            
            if is_start:
                icon_color = "green"
                icon_type = "ambulance"
            elif is_dest:
                icon_color = "red"
                icon_type = "plus"
            elif is_route:
                icon_color = "orange"
                icon_type = "map-pin"
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
            route_coords = [next((loc[1] for loc in self.locations if loc[0] == name), None) for name in self.current_route]
            
            # Create a map for the simulation
            m = folium.Map(location=self.shegaon_coords, zoom_start=15, tiles="cartodbpositron")
            
            # Add route points
            for name in self.current_route[1:-1]:  # Skip start and end
                coords = next((loc[1] for loc in self.locations if loc[0] == name), None)
                folium.Marker(
                    location=coords,
                    popup=f"<b>{name}</b>",
                    tooltip=name,
                    icon=folium.Icon(icon="map-pin", prefix="fa", color="orange")
                ).add_to(m)
            
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
            
            # Simulate movement
            for i, location_name in enumerate(self.current_route):
                # Get coordinates for current location
                coords = next((loc[1] for loc in self.locations if loc[0] == location_name), None)
                
                # Update status message
                progress = int((i + 1) / len(self.current_route) * 100)
                status_msg = f"🚑 Ambulance en route: {progress}% complete - {location_name}"
                
                # Update UI from the main thread - use partial to avoid scope issues
                self.root.after(0, partial(self.ambulance_status.set, status_msg))
                
                # Add the ambulance marker at the current position
                ambulance_group.add_child(
                    folium.Marker(
                        location=coords,
                        tooltip="Ambulance",
                        icon=folium.Icon(icon="ambulance", prefix="fa", color="green")
                    )
                )
                
                # Save and refresh the map
                m.save(self.map_file)
                
                # Make sure to not sleep after the last step
                if i < len(self.current_route) - 1:
                    time.sleep(1)
                    
                # Clear the ambulance marker for the next step
                if i < len(self.current_route) - 1:  # Don't clear on the last step
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
