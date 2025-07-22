import json
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from itertools import cycle

def plot_room(file_path):
    # 1) Load JSON & find the room
    with open(file_path, 'r') as f:
        data = json.load(f)
    room_name, room = next(iter(data['Rooms'][0].items()))
    
    # 2) Extract wall points to get the bounding box
    wall_pts = np.array([
        (w['location']['x'], w['location']['z'])
        for w in room.get('walls', [])
    ])
    xmin, xmax = wall_pts[:,0].min(), wall_pts[:,0].max()
    zmin, zmax = wall_pts[:,1].min(), wall_pts[:,1].max()
    
    # 3) Build door/window segments flush on the boundary
    door_segs = []
    tol = 1e-3
    for kind in ('doors','windows'):
        for itm in room.get(kind, []):
            x = itm['location']['x']
            z = itm['location']['z']
            W = itm['dimensions'].get('width', 0)
            L = itm['dimensions'].get('length', 0)

            # which wall?
            if abs(z - zmax) < tol:
                x1, x2 = x, x + W
                z1 = z2 = zmax
            elif abs(z - zmin) < tol:
                x1, x2 = x, x + W
                z1 = z2 = zmin
            elif abs(x - xmin) < tol:
                x1 = x2 = xmin
                z1, z2 = z, z - W
            elif abs(x - xmax) < tol:
                x1 = x2 = xmax
                z1, z2 = z, z - W
            else:
                if W > 0:
                    x1, x2 = x, x + W
                    z1 = z2 = z
                else:
                    x1 = x2 = x
                    z1, z2 = z, z + L
            door_segs.append((x1, z1, x2, z2, kind))
    
    # 4) Gather all objects → rectangles by category
    rects = []
    categories = set()
    for category, items in room.get('objects', {}).items():
        for it in items:
            x = it['location']['x']
            z = it['location']['z']
            L = it['dimensions']['length']
            W = it['dimensions']['width']
            cat = it.get('category', category)
            rects.append((x, z, L, W, cat))
            categories.add(cat)
    
    # 5) IoT devices from room['iot_devices']
    iots = []
    for dev in room.get('iot_devices', []):
        if dev.get('room') == room_name:
            x = dev['position']['x']
            z = dev['position']['z']
            name = dev.get('name','IoT')
            iots.append((x, z, name))
    
    # 6) Color cycles
    base = plt.rcParams['axes.prop_cycle'].by_key()['color']
    cc = cycle(base)
    cat_color = {c: next(cc) for c in sorted(categories)}
    dw_color  = next(cc)
    iot_color = {nm: next(cc) for *_, nm in iots}
    
    # 7) Plotting
    fig, ax = plt.subplots(figsize=(8,8))
    
    # 7a) Room boundary
    rect_x = [xmin, xmin, xmax, xmax, xmin]
    rect_z = [zmin, zmax, zmax, zmin, zmin]
    ax.plot(rect_x, rect_z, 'k-', lw=2, label='wall')
    
    # 7b) Doors/windows on boundary
    for x1, z1, x2, z2, kind in door_segs:
        ax.plot([x1,x2],[z1,z2], lw=2, color=dw_color,
                label=kind if kind not in ax.get_legend_handles_labels()[1] else "")
    
    # 7c) Object rectangles
    for x, z, L, W, cat in rects:
        blx, blz = x - L/2, z - W/2
        rect = Rectangle((blx,blz), L, W,
                         edgecolor=cat_color[cat], facecolor='none', lw=1.5,
                         label=cat if cat not in ax.get_legend_handles_labels()[1] else "")
        ax.add_patch(rect)
        ax.text(x, z, cat, fontsize=7, ha='center', va='center', color=cat_color[cat])
    
    # 7d) IoT points
    for x, z, name in iots:
        c = iot_color[name]
        ax.scatter(x, z, marker='x', s=80, color=c,
                   label=name if name not in ax.get_legend_handles_labels()[1] else "")
        ax.text(x, z, name, fontsize=7, ha='left', va='bottom', color=c)
    
    # 8) Finalize
    ax.set_aspect('equal', 'box')
    ax.set_xlabel('x (m)')
    ax.set_ylabel('z (m)')
    ax.set_title(f"Room '{room_name}' — boundary + flush doors/windows")
    ax.legend(loc='upper right', fontsize=8)
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    plot_room('bathroomwithiot1.json')
