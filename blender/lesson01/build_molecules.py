"""Lesson 1 — molecule library.

blender -b -P build_molecules.py
  -> lesson01_molecules.blend   (every model, laid out as a design sheet)
  -> glb/<name>.glb             (one per molecule, for a web viewer)
  -> renders/design_sheet.png   (labelled lineup still)
"""
import os, sys, math
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib, molkit as mk
importlib.reload(mk)

DATA = os.path.join(HERE, "data")
FONT = r"C:\Windows\Fonts\seguisb.ttf"

# name, file, label, sub-label  (MW from PubChem; antibody/insulin approximate)
SMALL = [
    ("morphine",      "morphine.sdf",      "Morphine",        "Natural · alkaloid · 285 Da"),
    ("atorvastatin",  "atorvastatin.sdf",  "Atorvastatin",    "Synthetic · fluorinated · 559 Da"),
    ("acetaminophen", "acetaminophen.sdf", "Acetaminophen",   "Safe dose · 151 Da"),
    ("napqi",         "napqi.sdf",         "NAPQI",           "Toxic metabolite · 149 Da"),
    ("s_ibuprofen",   "dexibuprofen.sdf",  "(S)-Ibuprofen",   "Active COX inhibitor"),
    ("r_ibuprofen",   "dexibuprofen.sdf",  "(R)-Ibuprofen",   "Mirror image · inactive"),
]
PROTEIN_COLORS = [(0.064, 0.48, 0.30), (0.02, 0.25, 0.60), (0.40, 0.75, 0.55), (0.10, 0.45, 0.80)]


def stereocentre(atoms, bonds):
    """sp3 carbon with one H, bonded to a carboxyl carbon — ibuprofen's chiral centre."""
    nb = {i: [] for i in range(len(atoms))}
    for i, j, _ in bonds:
        nb[i].append(j); nb[j].append(i)
    for i, (s, _) in enumerate(atoms):
        if s != "C" or len(nb[i]) != 4:
            continue
        hs = [k for k in nb[i] if atoms[k][0] == "H"]
        carboxyl = [k for k in nb[i] if atoms[k][0] == "C" and sum(atoms[m][0] == "O" for m in nb[k]) == 2]
        if len(hs) == 1 and carboxyl:
            return i
    return None


def build_all(coll):
    """Create every model in `coll`; return {name: object}."""
    obs = {}
    for name, fn, *_ in SMALL:
        atoms, bonds = mk.read_sdf(os.path.join(DATA, fn), mirror=(name == "r_ibuprofen"))
        hl = stereocentre(atoms, bonds) if "ibuprofen" in name else None
        obs[name] = mk.ball_and_stick(name, atoms, bonds, coll, highlight=hl)

    chains, ss = mk.read_pdb_ca(os.path.join(DATA, "insulin_3I40.pdb"))
    obs["insulin"] = mk.protein_trace("insulin", chains, coll, PROTEIN_COLORS, radius=0.9, disulfides=ss)

    chains, ss = mk.read_pdb_ca(os.path.join(DATA, "antibody_1IGT.pdb"))
    obs["antibody"] = mk.protein_trace("antibody", chains, coll, PROTEIN_COLORS, radius=1.6, disulfides=ss)
    return obs


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    mk.setup_world_and_render(scene, res=(1920, 1080), samples=64)
    font = mk.load_font(FONT)

    lib = mk.collection("Lesson01_Molecules")
    obs = build_all(lib)

    # --- export each model as GLB (origin-centred, Å units) before laying out the sheet
    glb_dir = os.path.join(HERE, "glb"); os.makedirs(glb_dir, exist_ok=True)
    for name, ob in obs.items():
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        for ch in ob.children:
            ch.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.export_scene.gltf(filepath=os.path.join(glb_dir, name + ".glb"),
                                  use_selection=True, export_apply=True, export_yup=True)

    # --- design sheet: 2 rows of small molecules + insulin, with labels
    labels = mk.collection("Labels")
    layout = [("morphine", 0.5, 0), ("atorvastatin", 1.5, 0), ("insulin", 2.5, 0),
              ("s_ibuprofen", 0, 1), ("r_ibuprofen", 1, 1), ("acetaminophen", 2, 1), ("napqi", 3, 1)]
    meta = {n: (l, s) for n, _, l, s in SMALL}
    meta["insulin"] = ("Insulin", "Biologic · 51 residues · 5.8 kDa")
    meta["antibody"] = ("IgG antibody", "Biologic · ~150 kDa")
    sx, sy = 24.0, 27.0
    for name, col, row in layout:
        ob = obs[name]
        s = 8.5 / mk.radius_of(ob)                   # fit each model to its cell (sheet is NOT to scale)
        ob.scale = (s, s, s)
        x = (col - 1.5) * sx
        z = (0.5 - row) * sy
        ob.location = (x, 0, z)
        ob.rotation_euler = (math.radians(15), 0, math.radians(25))
        lab, sub = meta[name]
        mk.text(lab, labels, (x, -2, z - 10.2), size=1.7, font=font, name="lab_" + name)
        mk.text(sub, labels, (x, -2, z - 12.4), size=1.05, color=(0.43, 0.9, 0.72), strength=1.5,
                font=font, name="sub_" + name)
    mk.text("BioMed Explorer · Lesson 1 · What is a drug?", labels, (0, -2, 0.5 * sy + 13), size=2.2,
            font=font, name="sheet_title")
    mk.text("Each model fitted to its cell — not to scale", labels, (0, -2, 0.5 * sy + 10), size=1.0,
            color=(0.6, 0.6, 0.65), strength=1, font=font, name="sheet_note")
    obs["antibody"].hide_render = obs["antibody"].hide_viewport = True   # too big for the sheet; used in the animation
    for ch in obs["antibody"].children:
        ch.hide_render = ch.hide_viewport = True

    rig = mk.collection("Lights")
    mk.three_point_lights(rig, Vector(), scale=60)

    cam_d = bpy.data.cameras.new("Camera"); cam_d.lens = 50
    cam = bpy.data.objects.new("Camera", cam_d)
    cam.location = (0, -165, -1)
    cam.rotation_euler = (math.pi / 2, 0, 0)
    scene.collection.objects.link(cam)
    scene.camera = cam

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "lesson01_molecules.blend"))

    os.makedirs(os.path.join(HERE, "renders"), exist_ok=True)
    scene.render.filepath = os.path.join(HERE, "renders", "design_sheet.png")
    scene.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True)
    print("DONE design sheet")


if __name__ == "__main__":
    main()
