"""Lesson 1 — "What is a Drug?" animation (16 s, 1280×720, 30 fps).

blender -b -P animate_lesson01.py              -> renders/lesson01.mp4 + lesson01_animation.blend
blender -b -P animate_lesson01.py -- --preview -> renders/preview_###.png (one still per act)

Act 1 (0–6 s)   Natural vs synthetic vs biologic — dolly out from two small molecules to reveal
                an IgG antibody at true relative scale.
Act 2 (6–11 s)  Stereochemistry — (S)- and (R)-ibuprofen as mirror images; chiral centre glows.
Act 3 (11–16 s) The dose makes the poison — acetaminophen → (CYP2E1, overdose) → NAPQI.
"""
import os, sys, math
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import importlib, molkit as mk, build_molecules as bm
importlib.reload(mk); importlib.reload(bm)

FPS = 30
A1, A2, A3, END = 1, 181, 331, 480         # act start frames
MINT = (0.43, 0.9, 0.72)
RED = (1.0, 0.25, 0.2)
ACT2 = Vector((1000, 0, 0))
ACT3 = Vector((2000, 0, 0))


def spin(ob, f0, f1, turns=1.0, axis=2):
    rot = list(ob.rotation_euler)
    mk.key(ob, "rotation_euler", f0, tuple(rot), interp="LINEAR")
    rot[axis] += turns * 2 * math.pi
    mk.key(ob, "rotation_euler", f1, tuple(rot), interp="LINEAR")


def pop(ob, f_in, f_out=None, dur=10, s=1.0):
    """Scale-in at f_in, optional scale-out at f_out (scale 0 = invisible)."""
    mk.key(ob, "scale", f_in, (0, 0, 0))
    mk.key(ob, "scale", f_in + dur, (s, s, s))
    if f_out is not None:
        mk.key(ob, "scale", f_out - dur, (s, s, s))
        mk.key(ob, "scale", f_out, (0, 0, 0))


def hud(cam, body, font, f_in, f_out, y=0.165, size=0.026, color=(1, 1, 1), coll=None):
    """Text locked to the camera (in front of the lens), so it stays put while the camera moves."""
    t = mk.text(body, coll, size=size, color=color, font=font, strength=2.5, name="hud_" + body[:10])
    t.parent = cam
    t.rotation_euler = (0, 0, 0)
    t.location = (0, y, -1.0)          # 1 unit in front of a 50 mm lens: frame is 0.72 × 0.405
    pop(t, f_in, f_out, dur=8)
    return t


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    mk.setup_world_and_render(scene, res=(1280, 720), fps=FPS, samples=32)
    scene.frame_start, scene.frame_end = A1, END
    font = mk.load_font(bm.FONT)

    mols = mk.collection("Molecules")
    labels = mk.collection("Labels")
    obs = bm.build_all(mols)

    cam_d = bpy.data.cameras.new("Camera"); cam_d.lens = 50
    cam_d.clip_start, cam_d.clip_end = 0.5, 5000
    cam = bpy.data.objects.new("Camera", cam_d)
    scene.collection.objects.link(cam); scene.camera = cam
    aim = bpy.data.objects.new("CamTarget", None)
    scene.collection.objects.link(aim)
    tr = cam.constraints.new("TRACK_TO"); tr.target = aim
    tr.track_axis, tr.up_axis = "TRACK_NEGATIVE_Z", "UP_Y"

    def shot(f, cam_loc, aim_loc):
        mk.key(cam, "location", f, Vector(cam_loc))
        mk.key(aim, "location", f, Vector(aim_loc))

    # ------------------------------------------------------------ ACT 1: origins & scale
    rig1 = mk.collection("Lights_act1")
    mk.three_point_lights(rig1, Vector(), scale=60, name="a1")
    m, a, ab = obs["morphine"], obs["atorvastatin"], obs["antibody"]
    m.location, a.location = (-9, 0, 0), (11, 0, 0)
    ab.location = (0, 170, 10)
    ab.rotation_euler = (math.radians(90), 0, 0)
    for o in (m, a):
        o.rotation_euler = (math.radians(20), 0, 0)
        spin(o, A1, A2 - 1, turns=1.0)
    spin(ab, A1, A2 - 1, turns=0.15, axis=1)
    pop(ab, A1 + 80, dur=45)                         # antibody grows in as the camera pulls back
    obs["insulin"].hide_render = True
    for ch in obs["insulin"].children:
        ch.hide_render = True

    lm = mk.text("Morphine", labels, (-9, -1, -7.5), size=1.4, font=font)
    lm2 = mk.text("natural · 285 Da", labels, (-9, -1, -9.3), size=0.9, color=MINT, font=font)
    la = mk.text("Atorvastatin", labels, (11, -1, -7.5), size=1.4, font=font)
    la2 = mk.text("synthetic · 559 Da", labels, (11, -1, -9.3), size=0.9, color=MINT, font=font)
    lab = mk.text("IgG antibody", labels, (95, 160, 40), size=20, font=font, align="LEFT")
    lab2 = mk.text("biologic · ~150,000 Da", labels, (95, 160, 18), size=12, color=MINT, font=font, align="LEFT")
    for t in (lm, lm2, la, la2):
        pop(t, A1 + 6, A1 + 95)
    for t in (lab, lab2):
        pop(t, A1 + 115, A2 - 2)

    shot(A1, (1, -46, 4), (1, 0, -1))
    shot(A1 + 60, (1, -52, 5), (1, 0, -1))           # gentle push while labels read
    shot(A1 + 150, (0, -420, 90), (0, 90, 20))       # pull back to reveal the antibody
    shot(A2 - 1, (0, -440, 95), (0, 90, 20))

    # ------------------------------------------------------------ ACT 2: mirror images
    rig2 = mk.collection("Lights_act2")
    s, r = obs["s_ibuprofen"], obs["r_ibuprofen"]
    s.location, r.location = ACT2 + Vector((-8, 0, 0)), ACT2 + Vector((8, 0, 0))
    s.rotation_euler = r.rotation_euler = (math.radians(70), 0, 0)
    # mirror-symmetric spin: S turns +, R turns − about Z keeps them reflections across x = 0
    mk.key(s, "rotation_euler", A2, (math.radians(70), 0, 0), interp="LINEAR")
    mk.key(s, "rotation_euler", A3 - 1, (math.radians(70), 0, math.pi), interp="LINEAR")
    mk.key(r, "rotation_euler", A2, (math.radians(70), 0, 0), interp="LINEAR")
    mk.key(r, "rotation_euler", A3 - 1, (math.radians(70), 0, -math.pi), interp="LINEAR")

    bpy.ops.mesh.primitive_plane_add(size=1, location=ACT2)
    mirror = bpy.context.active_object
    mirror.name = "MirrorPlane"
    mirror.rotation_euler = (0, math.radians(90), 0)
    mirror.scale = (16, 13, 1)
    mirror.data.materials.append(mk.material("mirror_glass", mk.ACCENT, rough=0.05,
                                             emission=mk.ACCENT, strength=0.6, alpha=0.18))
    for c in mirror.users_collection:
        c.objects.unlink(mirror)
    mols.objects.link(mirror)

    for body, x in (("(S)-ibuprofen", -8), ("(R)-ibuprofen", 8)):
        t = mk.text(body, labels, ACT2 + Vector((x, -1, -7)), size=1.3, font=font)
        pop(t, A2 + 10, A3 - 2)
    t = mk.text("active COX inhibitor", labels, ACT2 + Vector((-8, -1, -8.7)), size=0.85, color=MINT, font=font)
    pop(t, A2 + 25, A3 - 2)
    t = mk.text("inactive → inverts to (S) in vivo", labels, ACT2 + Vector((8, -1, -8.7)), size=0.85,
                color=(0.75, 0.75, 0.8), font=font)
    pop(t, A2 + 40, A3 - 2)

    shot(A2, ACT2 + Vector((-6, -40, 10)), ACT2 + Vector((0, 0, -1.5)))
    shot(A3 - 1, ACT2 + Vector((6, -38, 6)), ACT2 + Vector((0, 0, -1.5)))

    # ------------------------------------------------------------ ACT 3: dose makes the poison
    rig3 = mk.collection("Lights_act3")
    apap, nq = obs["acetaminophen"], obs["napqi"]
    for o in (apap, nq):
        o.location = ACT3
        o.rotation_euler = (math.radians(75), 0, 0)
    mk.key(apap, "rotation_euler", A3, (math.radians(75), 0, 0), interp="LINEAR")
    mk.key(apap, "rotation_euler", A3 + 70, (math.radians(75), 0, math.radians(120)), interp="LINEAR")
    mk.key(nq, "rotation_euler", A3 + 70, (math.radians(75), 0, math.radians(120)), interp="LINEAR")
    mk.key(nq, "rotation_euler", END, (math.radians(75), 0, math.radians(260)), interp="LINEAR")
    mk.key(apap, "scale", A3, (1, 1, 1)); mk.key(apap, "scale", A3 + 62, (1, 1, 1))
    mk.key(apap, "scale", A3 + 72, (0, 0, 0))
    mk.key(nq, "scale", A3, (0, 0, 0)); mk.key(nq, "scale", A3 + 70, (0, 0, 0))
    mk.key(nq, "scale", A3 + 82, (1.08, 1.08, 1.08)); mk.key(nq, "scale", A3 + 90, (1, 1, 1))

    # toxic glow: red halo light pulses in as NAPQI forms
    hl = bpy.data.lights.new("toxic_glow", "POINT"); hl.color = RED; hl.shadow_soft_size = 3
    ho = bpy.data.objects.new("toxic_glow", hl); ho.location = ACT3 + Vector((0, -6, 2))
    rig3.objects.link(ho)
    for f, e in ((A3, 0), (A3 + 70, 0), (A3 + 85, 4000), (A3 + 110, 1600), (A3 + 130, 3200), (END, 2000)):
        hl.energy = e; hl.keyframe_insert("energy", frame=f)

    t1 = mk.text("Acetaminophen", labels, ACT3 + Vector((0, -1, -5.4)), size=1.3, font=font)
    t1b = mk.text("therapeutic dose → safe conjugation", labels, ACT3 + Vector((0, -1, -6.9)), size=0.8,
                  color=MINT, font=font)
    pop(t1, A3 + 6, A3 + 62); pop(t1b, A3 + 14, A3 + 62)
    t2 = mk.text("overdose → CYP2E1", labels, ACT3 + Vector((0, -1, 5.4)), size=1.0, color=(1, 0.7, 0.4), font=font)
    pop(t2, A3 + 45, A3 + 100)
    t3 = mk.text("NAPQI", labels, ACT3 + Vector((0, -1, -5.4)), size=1.4, color=(1, 0.55, 0.5), font=font)
    t3b = mk.text("reactive electrophile → liver cell death", labels, ACT3 + Vector((0, -1, -6.9)), size=0.8,
                  color=(1, 0.55, 0.5), font=font)
    pop(t3, A3 + 78, END + 20); pop(t3b, A3 + 88, END + 20)

    shot(A3, ACT3 + Vector((0, -40, 3)), ACT3 + Vector((0, 0, -0.8)))
    shot(END, ACT3 + Vector((0, -35, 1.5)), ACT3 + Vector((0, 0, -0.8)))

    # ------------------------------------------------------------ act titles (camera HUD)
    huds = mk.collection("HUD")
    hud(cam, "1 · Where drugs come from", font, A1 + 2, A2 - 4, coll=huds)
    hud(cam, "2 · Same atoms, mirror shapes", font, A2 + 2, A3 - 4, coll=huds)
    hud(cam, "3 · The dose makes the poison", font, A3 + 2, END + 30, coll=huds)
    hud(cam, "true relative scale", font, A1 + 110, A2 - 4, y=-0.17, size=0.018, color=MINT, coll=huds)

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "lesson01_animation.blend"))

    out = os.path.join(HERE, "renders")
    os.makedirs(out, exist_ok=True)
    if "--preview" in sys.argv:
        scene.render.image_settings.file_format = "PNG"
        for f in (30, 175, 270, 455):
            scene.frame_set(f)
            scene.render.filepath = os.path.join(out, f"preview_{f:03d}.png")
            bpy.ops.render.render(write_still=True)
        print("DONE preview")
        return

    im = scene.render.image_settings
    if hasattr(im, "media_type"):
        im.media_type = "VIDEO"
    im.file_format = "FFMPEG"
    ff = scene.render.ffmpeg
    ff.format, ff.codec = "MPEG4", "H264"
    ff.constant_rate_factor = "HIGH"
    ff.ffmpeg_preset = "GOOD"
    ff.audio_codec = "NONE"
    scene.render.filepath = os.path.join(out, "lesson01.mp4")
    bpy.ops.render.render(animation=True)
    print("DONE animation")


if __name__ == "__main__":
    main()
