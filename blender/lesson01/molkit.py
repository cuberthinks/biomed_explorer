"""molkit — build ball-and-stick molecules and protein traces in Blender from SDF/PDB files.

Units: 1 Blender unit = 1 Angstrom. Each molecule becomes ONE mesh object (atoms + bonds,
material per element) centred on its centroid, so it can be spun, scaled and exported as GLB.
"""
import math
import bpy
import bmesh
from mathutils import Vector, Matrix

# Site palette (index.html): slate-950 background, emerald accent.
BG = (0.0006, 0.0021, 0.0090)          # #020617 in linear
ACCENT = (0.064, 0.48, 0.30)           # #10b981 in linear

# Element style: (base colour linear RGB, ball radius in Å)
ELEMENTS = {
    "C":  ((0.150, 0.165, 0.190), 0.36),
    "H":  ((0.800, 0.820, 0.840), 0.22),
    "O":  ((0.700, 0.030, 0.030), 0.36),
    "N":  ((0.030, 0.150, 0.800), 0.36),
    "F":  ((0.300, 0.800, 0.150), 0.32),
    "S":  ((0.900, 0.650, 0.020), 0.48),
    "Cl": ((0.100, 0.700, 0.080), 0.45),
    "P":  ((0.900, 0.300, 0.020), 0.48),
}
BOND_R = 0.11


# ---------------------------------------------------------------- parsing
def read_sdf(path, mirror=False):
    """Return atoms [(symbol, Vector)] and bonds [(i, j, order)] from a V2000 SDF/MOL file."""
    lines = open(path, encoding="utf-8").read().splitlines()
    na, nb = int(lines[3][0:3]), int(lines[3][3:6])
    atoms = []
    for l in lines[4:4 + na]:
        x, y, z, sym = float(l[0:10]), float(l[10:20]), float(l[20:30]), l[31:34].strip()
        atoms.append((sym, Vector((-x if mirror else x, y, z))))
    bonds = []
    for l in lines[4 + na:4 + na + nb]:
        bonds.append((int(l[0:3]) - 1, int(l[3:6]) - 1, int(l[6:9])))
    return atoms, bonds


def read_pdb_ca(path, model=1):
    """Return {chain: [Vector CA...]} and disulfide CA pairs [(Vector, Vector)] from a PDB file."""
    chains, sg, ca_of = {}, [], {}
    cur_model = 1
    for l in open(path, encoding="utf-8"):
        if l.startswith("MODEL"):
            cur_model = int(l.split()[1])
        if cur_model != model or not l.startswith("ATOM"):
            continue
        name, res, chain, resi = l[12:16].strip(), l[17:20], l[21], l[22:27]
        p = Vector((float(l[30:38]), float(l[38:46]), float(l[46:54])))
        if name == "CA":
            chains.setdefault(chain, []).append(p)
            ca_of[(chain, resi)] = p
        elif name == "SG" and res == "CYS":
            sg.append(((chain, resi), p))
    ss = []
    for i in range(len(sg)):
        for j in range(i + 1, len(sg)):
            if (sg[i][1] - sg[j][1]).length < 2.3:
                ss.append((ca_of[sg[i][0]], ca_of[sg[j][0]]))
    return chains, ss


# ---------------------------------------------------------------- materials
def material(name, color, rough=0.32, emission=None, strength=0.0, alpha=1.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = 0.35
    b.inputs["Coat Roughness"].default_value = 0.08
    if emission:
        b.inputs["Emission Color"].default_value = (*emission, 1)
        b.inputs["Emission Strength"].default_value = strength
    if alpha < 1:
        b.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "BLENDED"
    return m


def element_material(sym):
    col = ELEMENTS.get(sym, ((0.6, 0.2, 0.6), 0.4))[0]
    return material(f"el_{sym}", col)


# ---------------------------------------------------------------- geometry helpers
def _tag(bm, verts, mat_index):
    for f in {f for v in verts for f in v.link_faces}:
        f.material_index = mat_index
        f.smooth = True


def _cylinder(bm, a, b, r, mat_index, segs=16):
    d = b - a
    if d.length < 1e-6:
        return
    M = Matrix.Translation((a + b) / 2) @ d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=r, radius2=r,
                                depth=d.length, matrix=M)
    _tag(bm, res["verts"], mat_index)


def _sphere(bm, p, r, mat_index):
    res = bmesh.ops.create_uvsphere(bm, u_segments=32, v_segments=16, radius=r,
                                    matrix=Matrix.Translation(p))
    _tag(bm, res["verts"], mat_index)


def _new_object(name, mesh, collection):
    ob = bpy.data.objects.new(name, mesh)
    collection.objects.link(ob)
    return ob


# ---------------------------------------------------------------- builders
def ball_and_stick(name, atoms, bonds, collection, hydrogens=True, highlight=None):
    """One mesh: spheres per atom, two-colour half-bond cylinders, offset sticks for double/triple bonds.

    highlight: optional atom index rendered with an emissive accent material (e.g. a stereocentre).
    """
    keep = [i for i, (s, _) in enumerate(atoms) if hydrogens or s != "H"]
    centroid = sum((atoms[i][1] for i in keep), Vector()) / len(keep)
    pos = {i: atoms[i][1] - centroid for i in keep}

    mats, slot = [], {}
    def mi(key, factory):
        if key not in slot:
            slot[key] = len(mats)
            mats.append(factory())
        return slot[key]

    nbrs = {i: [] for i in keep}
    for i, j, _ in bonds:
        if i in pos and j in pos:
            nbrs[i].append(j); nbrs[j].append(i)

    bm = bmesh.new()
    for i in keep:
        sym = atoms[i][0]
        if i == highlight:
            idx = mi("hl", lambda: material("hl_stereo", (0.9, 0.7, 0.1), emission=(1.0, 0.75, 0.15), strength=4))
        else:
            idx = mi(sym, lambda s=sym: element_material(s))
        _sphere(bm, pos[i], ELEMENTS.get(sym, (None, 0.4))[1], idx)

    for i, j, order in bonds:
        if i not in pos or j not in pos:
            continue
        a, b = pos[i], pos[j]
        d = (b - a).normalized()
        # perpendicular in the plane of a neighbouring atom, for multi-bond offsets
        ref = next((pos[k] for k in nbrs[i] + nbrs[j] if k not in (i, j)), a + Vector((0, 0, 1)))
        perp = d.cross((ref - a).cross(d))
        perp = perp.normalized() if perp.length > 1e-6 else d.orthogonal().normalized()
        if order == 1:
            offsets, r = [Vector()], BOND_R
        elif order == 2:
            offsets, r = [perp * 0.13, -perp * 0.13], BOND_R * 0.7
        else:
            offsets, r = [Vector(), perp * 0.2, -perp * 0.2], BOND_R * 0.6
        mid = (a + b) / 2
        for o in offsets:
            _cylinder(bm, a + o, mid + o, r, mi(atoms[i][0], lambda s=atoms[i][0]: element_material(s)))
            _cylinder(bm, mid + o, b + o, r, mi(atoms[j][0], lambda s=atoms[j][0]: element_material(s)))

    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    for m in mats:
        me.materials.append(m)
    return _new_object(name, me, collection)


def protein_trace(name, chains, collection, colors, radius=1.0, disulfides=()):
    """Smooth Cα tube per chain (one curve object, material per chain) + yellow disulfide sticks."""
    allp = [p for c in chains.values() for p in c]
    centroid = sum(allp, Vector()) / len(allp)

    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = radius
    cu.bevel_resolution = 4
    cu.resolution_u = 6
    for k, (chain, pts) in enumerate(chains.items()):
        cu.materials.append(material(f"{name}_chain_{chain}", colors[k % len(colors)], rough=0.4))
        sp = cu.splines.new("BEZIER")
        sp.bezier_points.add(len(pts) - 1)
        for bp, p in zip(sp.bezier_points, pts):
            bp.co = p - centroid
            bp.handle_left_type = bp.handle_right_type = "AUTO"
        sp.material_index = k
        sp.use_smooth = True
    ob = _new_object(name, cu, collection)

    if disulfides:
        bm = bmesh.new()
        for a, b in disulfides:
            _cylinder(bm, a - centroid, b - centroid, radius * 0.45, 0)
        me = bpy.data.meshes.new(name + "_SS")
        bm.to_mesh(me); bm.free()
        me.materials.append(material("disulfide", ELEMENTS["S"][0], emission=(1, 0.7, 0.1), strength=1.5))
        ss = _new_object(name + "_SS", me, collection)
        ss.parent = ob
    return ob


def radius_of(ob):
    """Bounding radius around the object origin (for framing)."""
    return max((Vector(c).length for c in ob.bound_box), default=1.0)


# ---------------------------------------------------------------- scene helpers
def collection(name, parent=None):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in (parent or bpy.context.scene.collection).children:
        (parent or bpy.context.scene.collection).children.link(c)
    return c


def text(body, collection, loc=(0, 0, 0), size=1.0, color=(1, 1, 1), strength=2.0, font=None,
         align="CENTER", name=None):
    cu = bpy.data.curves.new(name or ("txt_" + body[:16]), "FONT")
    cu.body = body
    cu.size = size
    cu.align_x = align
    cu.align_y = "CENTER"
    if font:
        cu.font = font
    m = bpy.data.materials.new("txtmat_" + (name or body[:12]))
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (*color, 1)
    e.inputs["Strength"].default_value = strength
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(e.outputs[0], o.inputs[0])
    cu.materials.append(m)
    ob = bpy.data.objects.new(cu.name, cu)
    ob.location = loc
    ob.rotation_euler = (math.pi / 2, 0, 0)   # stand up, readable from -Y
    collection.objects.link(ob)
    return ob


def load_font(path):
    try:
        return bpy.data.fonts.load(path, check_existing=True)
    except Exception:
        return None


def setup_world_and_render(scene, res=(1280, 720), fps=30, samples=48):
    world = scene.world or bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bgn = world.node_tree.nodes["Background"]
    bgn.inputs["Color"].default_value = (*BG, 1)
    bgn.inputs["Strength"].default_value = 1.0

    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = samples
    for attr, val in (("use_raytracing", True), ("use_shadows", True)):
        if hasattr(scene.eevee, attr):
            setattr(scene.eevee, attr, val)
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.fps = fps
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.render.film_transparent = False


def three_point_lights(collection, target=Vector(), scale=40.0, name="rig"):
    """Key/fill/rim sun lights (distance-independent, so they work at any Å scale)."""
    out = []
    for nm, off, energy, col in (
        ("key", Vector((-0.8, -1.0, 0.9)), 4.0, (1.0, 0.97, 0.92)),
        ("fill", Vector((1.0, -0.6, 0.2)), 1.4, (0.75, 0.88, 1.0)),
        ("rim", Vector((0.2, 1.0, 0.8)), 3.5, (0.45, 1.0, 0.8)),
    ):
        ld = bpy.data.lights.new(f"{name}_{nm}", "SUN")
        ld.energy = energy
        ld.color = col
        ld.angle = 0.2
        lo = bpy.data.objects.new(f"{name}_{nm}", ld)
        lo.location = target + off * scale
        lo.rotation_euler = off.to_track_quat("Z", "Y").to_euler()
        collection.objects.link(lo)
        out.append(lo)
    return out


def key(ob, path, frame, value=None, interp=None):
    if value is not None:
        setattr(ob, path, value)
    ob.keyframe_insert(path, frame=frame)
    if interp:
        ad = ob.animation_data
        act = ad.action if ad else None
        if act:
            for fc in _fcurves(act):
                if fc.data_path == path:
                    for kp in fc.keyframe_points:
                        kp.interpolation = interp


def _fcurves(action):
    # Blender 5.x layered actions; fall back to legacy action.fcurves
    if hasattr(action, "layers") and action.layers:
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    yield from bag.fcurves
    elif hasattr(action, "fcurves"):
        yield from action.fcurves
