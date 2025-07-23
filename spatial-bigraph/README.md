# SpatialBigraphsProject

A toolkit for constructing, visualizing, and analyzing **spatial bigraphs** from RoomPlan JSON exports.

## 📁 Project File Structure

spatial-bigraph/
├── Figures/ # Generated plots (manually saved here)
├── Jsons/ # RoomPlan‑app JSON files
├── imagineRoomBoundary.py 
├── ImagineRoom.py 
├── bigraphs_with_centroids.py 
├── bigraphs_withplanes.py 
└── README.md 


## 🐍 Python Scripts

- **`imagineRoomBoundary.py`**  
  Reads a RoomPlan JSON, extracts wall/floor boundary points, and plots the room outline.

- **`ImagineRoom.py`**  
  Loads the full JSON (walls, furniture, windows, etc.) and renders a complete 2D floorplan.

- **`bigraphs_with_centroids.py`**  
  Computes centroids of each room‑feature (e.g. furniture, walls) and constructs a graph where edges encode spatial containment.

- **`bigraphs_withplanes.py`**  
  Splits the room into planar regions (planes), then builds a bigraph whose nodes are those regions and edges indicate containment.

## ⚙️ Setup & Usage

1. **(Optional) Create a virtual environment**  
   ```bash
   python3 -m venv venv
   source venv/bin/activate

2. Install dependencies
    If you have a requirements.txt, run:
    pip install -r requirements.txt

    Otherwise make sure you have at least:
    pip install numpy matplotlib networkx shapely

3. Prepare your JSON
    Copy your RoomPlan exports into the Jsons/ folder.

4. Run a script
    python imagineRoomBoundary.py 
    Replace file_to_json with your file name.

    Figures will pop up interactively; to save them, click Save or edit the script to call plt.savefig("Figures/…").


