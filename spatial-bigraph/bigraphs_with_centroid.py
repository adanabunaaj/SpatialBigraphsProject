import json 
import networkx as nx
from networkx.drawing.nx_pydot import graphviz_layout
import matplotlib.pyplot as plt
import numpy as np 

# ─────── Helper Functions ────────────────────────────────────────────────────

#Add node with attributes
def add_node(graph, node_id, label, **attrs):
    graph.add_node(node_id, label=label, **attrs)

#Assign unique IDs to avoid collision
def unique_id(prefix, i):
    return f"{prefix}_{i}"

def to_vec(point):
    """
    Convert a dict with 'x', 'y', 'z' keys into a NumPy 3-vector [x, y, z].]
    """
    # Extract each coordinate
    x = point["x"]
    y = point["y"]
    z = point["z"]

    # Pack into a NumPy array and return
    return np.array([x, y, z]) 

# ─────── Main Script ─────────────────────────────────────────────────────────

#Load JSON file
path_to_file = "Jsons/room1_kitchen_with_iot.json" # Adjust the path as needed
with open(path_to_file, "r") as f:
    data = json.load(f)

rooms = data["Rooms"] 


#Build the Spatial Bigraph using NetworkX
G = nx.DiGraph() #Directed Graph

for room_dict in rooms: 
    for room_name, room_data in room_dict.items():
        #Add rooms as root nodes
        add_node(G, room_name, label=room_name)

        #Add first-level nodes (walls, doors, windows, furniture, etc..):
        collections =  {}
        for group in ('walls', 'doors', 'windows'):
            collections[group] = room_data.get(group, [])

        for category, objs in room_data.get('objects', {}).items():
            collections[category] = objs

        for group_name , items in collections.items():
            for i, item in enumerate(items):

                node_id = item.get('id', f"{group_name}_{i}")
                if group_name in ('walls', 'doors', 'windows'):
                    label = group_name[:-1].capitalize()

                else:
                   label = item.get('category', group_name)
            
                pos = item.get('location') or item.get('position')

                #add node: 
                add_node(G, node_id, label, position=pos)
                #add edge to root
                G.add_edge(room_name, node_id)
        
        #Add IoT devices as second-level nodes: 
        iot_devs = room_data.get("iot_devices", [])
        for dev in iot_devs:
            dev_pos = to_vec(dev["position"])
            dev_id = dev['id']
            closest_obj = None
            closest_dist = float('inf')

            #flatten all ovjects into one list
            all_objects = []
            for group_items in collections.values():
                all_objects.extend(group_items)

            #find closest distance to an object -- this is wrong imo cause if it is on a wall it might be closer to the chair in front of it and not to the wall corner. 
            for obj in all_objects:
                loc = obj.get('location') or obj.get('position')

                if group_name in ("walls", "doors", "windows"):
                    # JSON gives a corner for these, so we compute centroid
                    dims = obj.get("dimensions", {})
                    w = dims.get("width",  0.0)  # extent in x
                    l = dims.get("length", 0.0)  # extent in z
                    h = dims.get("height", 0.0)  # extent in y

                    # Centroid = corner + half‐extents
                    cx = loc["x"] + 0.5 * w
                    cy = loc["y"] + 0.5 * h
                    cz = loc["z"] + 0.5 * l
                    obj_centroid = np.array([cx, cy, cz])

                else:
                    # For all other objects, JSON loc *is* the centroid
                    obj_centroid = to_vec(loc)

                dist = np.linalg.norm(dev_pos - obj_centroid) #Euclidean distance from device to object centroid
                if dist < closest_dist:
                    closest_dist = dist
                    closest_obj = obj

            #Add device nodes to the tree
            add_node(G, dev_id, label=dev.get('name', 'IoT Device'), position=dev["position"])
            parent_id = closest_obj.get("id", "<fallback_id>")
            G.add_edge(parent_id, dev_id)


# ─────── Visualize the Bigraph ────────────────────────────────────────────────

def hierarchy_pos(G, root, width=1.0, vert_gap=0.2, vert_loc=0, xcenter=0.5,
                  pos=None, parent=None):
    """
    Compute positions for a tree layout (top-down).
    """
    if pos is None:
        pos = {root: (xcenter, vert_loc)}
    else:
        pos[root] = (xcenter, vert_loc)

    children = list(G.successors(root))
    if not children:
        return pos
    
    dx = width / len(children)
    nextx = xcenter - width/2 - dx/2
    for child in children:
        nextx += dx
        pos = hierarchy_pos(
            G, child,
            width=dx, vert_gap=vert_gap, vert_loc=vert_loc-vert_gap,
            xcenter=nextx, pos=pos, parent=root
        )
    return pos

# Find roots (rooms have no incoming edges)
roots = [n for n, d in G.in_degree() if d == 0]

# Build a pos dict for each node
if len(roots) == 1:
    pos = hierarchy_pos(G, roots[0])
else:
    pos = {}
    chunk = 1.0 / len(roots)
    for i, r in enumerate(roots):
        subpos = hierarchy_pos(G, r, width=chunk, xcenter=(i + 0.5) * chunk)
        pos.update(subpos)

# Draw the directed tree
labels = nx.get_node_attributes(G, 'label')
nx.draw(
    G, pos,
    with_labels=True,
    labels=labels,
    node_size=500,
    node_color="lightblue",
    arrows=True,
    arrowstyle='-|>',
    arrowsize=12
)
plt.tight_layout()
plt.show()