import json 
import networkx as nx
from networkx.drawing.nx_pydot import graphviz_layout
import matplotlib.pyplot as plt
import numpy as np 

#Helping Functions: 

def point_to_plane_dist(point, plane_point, plane_normal):
    """Unsigned distance from pt to infinite plaen"""
    return abs(np.dot(plane_normal, point - plane_point))

def point_to_aabb_dist(point, aabb_min, aabb_max):
    """" Distance from point to axis-aligned bounding box"""""
    dx = max(aabb_min[0] - point[0], 0, point[0] - aabb_max[0])
    dy = max(aabb_min[1] - point[1], 0, point[1] - aabb_max[1])
    dz = max(aabb_min[2] - point[2], 0, point[2] - aabb_max[2])
    return np.linalg.norm([dx, dy, dz])

def build_surfaces(objects, walls_ids, door_ids, window_ids):
    """
    Convert each object into a tuple: 
    ("plane",   obj_dict, point_on_plane, normal)
    ("box",     obj_dict, aabb_min,       aabb_max)
    We identify planes by id membership in walls/doors/windows.
    """
    surfaces = []
    for obj in objects: 
        pos = to_vec(obj.get('location', obj.get("position")))
        dims = obj.get("dimensions", {})

        #Walls/doors/windows --> infinite planes
        if obj["id"] in walls_ids + door_ids + window_ids:
            #assume the zero-length dimension axis is the normal
            #e.g. walls have length==0 --> normal along local z
            #you may need to adjust axis mapping
            if dims.get("length",1) == 0:
                normal = np.array([0, 0, 1])
            elif dims.get("width",1) == 0:
                normal = np.array([1, 0, 0])
            else:  # height==0
                normal = np.array([0, 1, 0])
            surfaces.append(("plane", obj, pos, normal))
        else: 
            # AABB: center ± half-dims
            half = np.array([
                dims.get("length",0)/2,
                dims.get("height",0)/2,
                dims.get("width",0)/2
            ])
            aabb_min = pos - half
            aabb_max = pos + half
            surfaces.append(("box", obj, aabb_min, aabb_max))
    return surfaces


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
with open("Jsons/floor.json", "r") as f:
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

        #faltten all objects once: 
        all_objects = []
        for items in collections.values():
            all_objects.extend(items)
        
        #Collect wall/door/window IDs
        walls_ids   = [o["id"] for o in collections.get("walls",[])]
        door_ids    = [o["id"] for o in collections.get("doors",[])]
        window_ids  = [o["id"] for o in collections.get("windows",[])]

        # build surface list
        surfaces = build_surfaces(all_objects, walls_ids, door_ids, window_ids)

        
        #Add IoT devices as second-level nodes: 
        iot_devs = room_data.get("iot_devices", [])
        for dev in iot_devs:
            dev_pos = to_vec(dev["position"])
            dev_id = dev['id']
            closest_obj = None
            closest_dist = float('inf')

            
            #find closest distance to an object -- this is wrong imo cause if it is on a wall it might be closer to the chair in front of it and not to the wall corner. 
            for kind, obj, *params in surfaces:
                if kind == "plane":
                    dist = point_to_plane_dist(dev_pos, params[0], params[1])
                else:
                    dist = point_to_aabb_dist(dev_pos, params[0], params[1])

                if dist < closest_dist:
                    closest_dist, closest_obj = dist, obj

            #Add device nodes to the tree
            # Optionally: ignore if best_dist > some_threshold
            parent_id = closest_obj.get("id", "<unknown>")
            add_node(G, dev['id'], label=dev.get('name','IoT Device'), position=dev["position"])
            G.add_edge(parent_id, dev['id'])


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












