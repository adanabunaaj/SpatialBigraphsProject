import json 
import networkx as nx
from networkx.drawing.nx_pydot import graphviz_layout
import matplotlib.pyplot as plt
import numpy as np 

# ─── Geometry Helpers ────────────────────────────────────────────────────────

def to_vec(point):
    """
    Convert a dict with keys 'x','y','z' into a NumPy array [x,y,z].
    """
    return np.array([point["x"], point["y"], point["z"]])

def point_to_plane_dist(point, plane_point, plane_normal):
    """
    Compute the unsigned perpendicular distance from `point` to the infinite plane
    defined by `plane_point` (any point on the plane) and `plane_normal`.
    """
    return abs(np.dot(plane_normal, point - plane_point))


def point_to_aabb_dist(point, aabb_min, aabb_max):
    """
    Compute the shortest distance from `point` to an axis-aligned bounding box
    defined by `aabb_min` and `aabb_max`.
    """
    dx = max(aabb_min[0] - point[0], 0, point[0] - aabb_max[0])
    dy = max(aabb_min[1] - point[1], 0, point[1] - aabb_max[1])
    dz = max(aabb_min[2] - point[2], 0, point[2] - aabb_max[2])
    return np.linalg.norm([dx, dy, dz])

def build_surfaces(objects, walls_ids, door_ids, window_ids):
    """
    For each object, produce either:
      - ("plane", obj, plane_point, normal)  for walls/doors/windows
      - ("box",   obj, aabb_min, aabb_max)   for everything else

    *Walls/doors/windows* JSON give you a *corner* location + dimensions:
      we compute the face-centroid = corner + ½(extents) to use as plane_point.

    *Other objects* JSON `location` is already their centroid – so we
    build an AABB centered there.
    """
    
    surfaces = []
    for obj in objects: 
        dims = obj.get("dimensions", {})
        
        # Does this object live in walls/doors/windows?
        is_plane = obj["id"] in (walls_ids + door_ids + window_ids)
        loc_raw  = obj.get("location") or obj.get("position")

        if is_plane:
            # 1) Compute face centroid from the corner + half extents
            w = dims.get("width",  0.0)  # x‐extent
            l = dims.get("length", 0.0)  # z‐extent
            h = dims.get("height", 0.0)  # y‐extent

            cx = loc_raw["x"] + 0.5 * w
            cy = loc_raw["y"] + 0.5 * h
            cz = loc_raw["z"] + 0.5 * l
            plane_point = np.array([cx, cy, cz])

            # 2) Choose a normal based on which dimension was zero
            #    (length==0 → normal along z; width==0 → normal along x; else y)
            if abs(dims.get("length", 1)) < 1e-6:
                normal = np.array([0, 0, 1])
            elif abs(dims.get("width", 1)) < 1e-6:
                normal = np.array([1, 0, 0])
            else:
                normal = np.array([0, 1, 0])

            surfaces.append(("plane", obj, plane_point, normal))

        else:
            # Build an AABB around the centroid (JSON loc is already centroid)
            center = to_vec(loc_raw)
            half = np.array([
                dims.get("length", 0.0) / 2,
                dims.get("height", 0.0) / 2,
                dims.get("width",  0.0) / 2
            ])
            aabb_min = center - half
            aabb_max = center + half
            surfaces.append(("box", obj, aabb_min, aabb_max))


            surfaces.append(("plane", obj, plane_point, normal))

    return surfaces

# ─── Graph Building Helpers ─────────────────────────────────────────────────

#Add node with attributes
def add_node(graph, node_id, label, **attrs):
    graph.add_node(node_id, label=label, **attrs)

#Assign unique IDs to avoid collision
def unique_id(prefix, i):
    return f"{prefix}_{i}"


# ─── Main: Build the Spatial Bigraph ─────────────────────────────────────────

#Load JSON file
path_to_file = "Jsons/floor.json" # Adjust the path as needed
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
                #add edge
                G.add_edge(room_name, node_id)

        #faltten all objects once: 
        all_objects = []  # list of (obj_dict, group_name)
        #Collect wall/door/window IDs
        walls_ids   = [o["id"] for o in collections.get("walls",[])]
        door_ids    = [o["id"] for o in collections.get("doors",[])]
        window_ids  = [o["id"] for o in collections.get("windows",[])]

        for grp, items in collections.items():
            all_objects.extend([(o, grp) for o in items])

        # build surface list
        surfaces = build_surfaces([o for o, _ in all_objects], walls_ids, door_ids, window_ids)
        
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
                    plane_pt, normal = params
                    dist = point_to_plane_dist(dev_pos, plane_pt, normal)
                else:  # "box"
                    aabb_min, aabb_max = params
                    dist = point_to_aabb_dist(dev_pos, aabb_min, aabb_max)

                if dist < closest_dist:
                    closest_dist, closest_obj = dist, obj

            # Create the IoT node & attach to its nearest object
            add_node(
                G, dev_id,
                label    = dev.get("name", "IoT Device"),
                position = dev["position"]
            )
            parent_id = closest_obj.get("id", "<unknown>")
            G.add_edge(parent_id, dev_id)


# ─── Visualization: Hierarchical Layout ──────────────────────────────────────

#Define simple tree layout function fro visualization
def hierarchy_pos(G, root, width=1.0, vert_gap=0.2, vert_loc=0, xcenter=0.5,
                  pos=None, parent=None):
    """
    Compute a top-down tree layout for a DiGraph that is a tree.
    Returns a dict {node: (x,y), …}.
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