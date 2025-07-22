import json
import numpy as np
import matplotlib.pyplot as plt

# 1) Load your bigraph JSON
with open("RoomBigraph17.json", "r") as f:
    data = json.load(f)
room = data["Rooms"][0]["room1"]

# 2) Gather (x,z) by category — replace "location"→"corner" if your JSON uses that
pts = {}
for cat in ["walls", "doors", "windows"]: #//TODO#add windows later 
    pts[cat] = [(it["location"]["x"], it["location"]["z"])
                for it in room[cat]]
for cat, items in room.get("furniture", {}).items():
    pts[cat] = [(it["location"]["x"], it["location"]["z"])
                for it in items]

# 3) Compute the axis-aligned bounding box of wall points
wall_pts = np.array(pts["walls"])
xmin, xmax = wall_pts[:,0].min(), wall_pts[:,0].max()
zmin, zmax = wall_pts[:,1].min(), wall_pts[:,1].max()

# 4) Define the rectangle corners (close the loop back to start)
rect_x = [xmin, xmin, xmax, xmax, xmin]
rect_z = [zmin, zmax, zmax, zmin, zmin]

# 5) Plot
plt.figure(figsize=(8,8))

# 5a) Draw room outline
plt.plot(rect_x, rect_z, 'k-', lw=2, label="Room boundary")

# 5b) Scatter + annotate every point
for cat, coords in pts.items():
    if not coords: continue
    xs, zs = zip(*coords)
    plt.scatter(xs, zs, label=cat, s=40)
    for x, z in coords:
        plt.text(x, z, f"({x:.2f}, {z:.2f})",
                 fontsize=7, ha='right', va='bottom')

# 6) Tidy up
plt.gca().set_aspect('equal', 'box')
plt.xlabel("x (m)")
plt.ylabel("z (m)")
plt.title("Plan‐view: room outline + points w/ coords")
plt.legend(loc="upper right")
plt.show()
