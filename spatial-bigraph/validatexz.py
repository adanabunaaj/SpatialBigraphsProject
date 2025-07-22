import json
import matplotlib.pyplot as plt

# 1) Load your bigraph JSON
with open("RoomBigraph8.json") as f:
    data = json.load(f)

room = data["Rooms"][0]["room1"]

# 2) Gather all (x,z) pairs, color-coded by category
categories = ["walls", "doors", "windows"] + list(room["furniture"].keys())
points = {cat: [] for cat in categories}

for cat in ["walls", "doors", "windows"]:
    for item in room[cat]:
        x = item["location"]["x"]
        z = item["location"]["z"]
        points[cat].append((x, z))

for cat, items in room["furniture"].items():
    for item in items:
        x = item["location"]["x"]
        z = item["location"]["z"]
        points[cat].append((x, z))

# 3) Plot
plt.figure()
for cat, pts in points.items():
    xs, zs = zip(*pts) if pts else ([],[])
    plt.scatter(xs, zs, label=cat, s=30)

plt.gca().set_aspect("equal", "box")
plt.xlabel("x (m)")
plt.ylabel("z (m)")
plt.title("Top-down view of scanned room")
plt.legend(loc="best")
plt.show()
