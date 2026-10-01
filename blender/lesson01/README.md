# Lesson 1 — "What is a Drug?" · Blender molecules & animation

Real coordinates only: small molecules are PubChem 3D conformers, proteins are PDB crystal structures
(`data/`). 1 Blender unit = 1 Å. Requires Blender 5.2.

| Run | Output |
| --- | --- |
| `blender -b -P build_molecules.py` | `lesson01_molecules.blend`, `glb/*.glb`, `renders/design_sheet.png` |
| `blender -b -P animate_lesson01.py -- --preview` | one PNG per act in `renders/` |
| `blender -b -P animate_lesson01.py` | `renders/lesson01.mp4` (16 s, 1280×720, ~3 min on RTX 5060 Ti) |

## Molecules → lesson concept
| Model | Source | Teaches |
| --- | --- | --- |
| Morphine | PubChem CID 5288826 | Natural drug (alkaloid) |
| Atorvastatin | CID 60823 | Synthetic, SAR-optimised, fluorinated |
| Insulin | PDB 3I40 (Cα trace + disulfides) | Biologic (design sheet) |
| IgG antibody | PDB 1IGT (Cα trace + disulfides) | Biologic at true scale (animation) |
| (S)/(R)-Ibuprofen | CID 39912, mirrored for (R) | Enantiomers; stereocentre glows gold |
| Acetaminophen → NAPQI | CID 1983, 39763 | "The dose makes the poison" |

`molkit.py` is reusable for later lessons: `read_sdf` / `read_pdb_ca` → `ball_and_stick` / `protein_trace`.
