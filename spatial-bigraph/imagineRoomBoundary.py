import json
import numpy as np
import matplotlib.pyplot as plt

# 1) Load your JSON file and get room data 
path_to_file = 'Jsons/bathroomwithiot1.json' # Adjust the path as neede
with open(path_to_file) as f:
    data = json.load(f)

room_name = "Bathroom" # Adjust the room name as needed
room = data["Rooms"][0][room_name]

# 2) Gather (x,z) by category 
points = {} #dict to hold lists of (x,z) tuples for each caregory --> {category: [(x1,z1), (x2,z2), ...]}
for category in ["walls", "doors", "windows"]: 
    points[category] = [(item["location"]["x"], item["location"]["z"]) for item in room[category]]
for category, items in room.get("furniture", {}).items():
    points[category] = [(item["location"]["x"], item["location"]["z"]) for item in items]

# 3) Compute the room boundary
wall_pts = np.array(points["walls"])
xmin, xmax = wall_pts[:,0].min(), wall_pts[:,0].max()
zmin, zmax = wall_pts[:,1].min(), wall_pts[:,1].max()

# 4) Define the rectangle corners of the room (close the loop back to start)
rect_x = [xmin, xmin, xmax, xmax, xmin]
rect_z = [zmin, zmax, zmax, zmin, zmin]

# 5) Plot
plt.figure(figsize=(8,8))

# 5a) Draw room outline
plt.plot(rect_x, rect_z, 'k-', lw=2, label="Room boundary")

# 5b) Scatter + annotate every point
for cat, coords in points.items():
    if not coords: continue
    xs, zs = zip(*coords)
    plt.scatter(xs, zs, label=cat, s=40)
    for x, z in coords:
        plt.text(x, z, f"({x:.2f}, {z:.2f})",
                 fontsize=7, ha='right', va='bottom')

# 6) Display
plt.gca().set_aspect('equal', 'box')
plt.xlabel("x (m)")
plt.ylabel("z (m)")
plt.title("Plan‐view: room outline + points w/ coords")
plt.legend(loc="upper right")
plt.show()
