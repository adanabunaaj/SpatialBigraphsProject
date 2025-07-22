#not very accurate but try it with a more accurate scan 
import json 
import networkx as nx
from networkx.drawing.nx_pydot import graphviz_layout
import matplotlib.pyplot as plt
import numpy as np 

#Helping Functions: 

#Add node with attributes
def add_node(graph, node_id, label, **attrs):
    graph.add_node(node_id, label=label, **attrs)

#Assign unique IDs to avoid collision
def unique_id(prefix, i):
    return f"{prefix}_{i}"

def to_vec(point):
    """
    Convert a dict with 'x', 'y', 'z' keys into a NumPy 3-vector.
    """
    # Extract each coordinate
    x = point["x"]
    y = point["y"]
    z = point["z"]

    # Pack into a NumPy array and return
    return np.array([x, y, z]) 

#Load JSON file
with open("Jsons/kitchenroom.json", "r") as f:
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
                #add edge
                G.add_edge(room_name, node_id)
        
        #Add IoT devices as second-level nodes: 
        iot_devs = room_data.get("iot_devices", [])
        for dev in iot_devs:
            dev_pod = to_vec(dev["position"])
            dev_id = dev['id']
            closest_obj = None
            closest_dist = float('inf')

            #flatten all ovjects into one list
            all_objects = []
            for group_items in collections.values():
                all_objects.extend(group_items)

            #find closest distance to an object -- this is wrong imo cause if it is on a wall it might be closer to the chair in front of it and not to the wall corner. 
            for obj in all_objects:
                obj_pos = to_vec(obj.get('location', obj.get('position')))
                dist = np.linalg.norm(dev_pod - obj_pos)

                if dist < closest_dist:
                    closest_dist = dist
                    closest_obj = obj

            #Add device nodes to the tree
            add_node(G, dev_id, label=dev.get('name', 'IoT Device'), position=dev["position"])
            parent_id = closest_obj.get("id", "<fallback_id>")
            G.add_edge(parent_id, dev_id)


#Visualize the Spatial Bigraph

#Define simple tree layout function fro visualization
def hierarchy_pos(G, root, width=1.0, vert_gap=0.2, vert_loc=0, xcenter=0.5,
                  pos=None, parent=None):
    """
    If G is a DiGraph that is a tree, return a dict of positions
    keyed by node, in a top-down hierarchy layout.
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

# Find all root nodes (rooms have in-degree 0)
roots = [n for n, d in G.in_degree() if d == 0]

# Build pos dict for one or multiple roots
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












