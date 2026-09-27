#!/usr/bin/env python3
# Blender icinde: blender --background --python rocket_render.py -- --scene scenes/studyo.json [--gif 36]
"""rocket-cinema — stüdyo render + gimbal animasyonu."""

import argparse
import json
import math
import os
import shutil
import subprocess
import sys

import bpy
from mathutils import Vector

BURASI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BURASI)

import roket  # noqa: E402


def kamera_kur(konum, hedef, lens=50):
    cam = bpy.data.cameras.new("Cam")
    cam.lens = lens
    co = bpy.data.objects.new("kamera", cam)
    bpy.context.collection.objects.link(co)
    co.location = konum
    yon = Vector(hedef) - Vector(konum)
    co.rotation_euler = yon.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = co
    return co


def isik_kur(ad, guc, konum, hedef, boy=6.0):
    ld = bpy.data.lights.new(ad, "AREA")
    ld.energy = guc
    ld.size = boy
    lo = bpy.data.objects.new(ad, ld)
    bpy.context.collection.objects.link(lo)
    lo.location = konum
    lo.rotation_euler = (Vector(hedef) - Vector(konum)
                         ).to_track_quat("-Z", "Y").to_euler()


def sahne_kur(cfg):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        prefs.get_devices()
        for dv in prefs.devices:
            dv.use = True
        sc.cycles.device = "GPU"
    except Exception as e:
        print("  [uyari] GPU:", e)
    sc.cycles.samples = cfg["render"].get("samples", 128)
    sc.cycles.use_denoising = True
    sc.render.resolution_x = cfg["render"].get("width", 1600)
    sc.render.resolution_y = cfg["render"].get("height", 900)
    sc.view_settings.view_transform = "Filmic"
    sc.view_settings.exposure = cfg["render"].get("exposure", 0.0)
    look = cfg["render"].get("look")
    if look:
        try:
            sc.view_settings.look = look
        except Exception:
            pass
    dunya = bpy.data.worlds.new("Studio")
    sc.world = dunya
    dunya.use_nodes = True
    nt = dunya.node_tree
    nt.nodes.clear()
    bg = nt.nodes.new("ShaderNodeBackground")
    renk = cfg.get("fon", {"color": [0.010, 0.011, 0.014]})
    bg.inputs["Color"].default_value = (*renk["color"], 1)
    bg.inputs["Strength"].default_value = renk.get("strength", 1.0)
    outn = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(bg.outputs["Background"], outn.inputs["Surface"])

    m = bpy.data.materials.new("Zemin")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    z = cfg.get("zemin", {})
    b.inputs["Base Color"].default_value = (*z.get("color", (0.075, 0.075, 0.08)), 1)
    b.inputs["Roughness"].default_value = z.get("roughness", 0.45)
    bpy.ops.mesh.primitive_plane_add(size=80)
    zo = bpy.context.active_object
    zo.name = "Zemin"
    zo.data.materials.append(m)
    return sc


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--scene", required=True)
    ap.add_argument("--gif", type=int, default=0)
    ap.add_argument("--fps", type=int, default=12)
    a = ap.parse_args(args)

    cfg = json.load(open(a.scene, encoding="utf-8"))
    if os.environ.get("HIZLI") == "1":
        cfg["render"] = {**cfg.get("render", {}), "width": 800, "height": 450,
                         "samples": 32}
        cfg["output"] = "/tmp/onizleme_roket_" + os.path.basename(a.scene).replace(".json", ".png")
        print("  [HIZLI] onizleme ->", cfg["output"])

    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = sahne_kur(cfg)

    isik = cfg.get("isik", {})
    isik_kur("Ana", isik.get("ana", 3200), isik.get("ana_konum", (-12, -11, 24)),
             (0, 0, 20))
    isik_kur("Dolgu", isik.get("dolgu", 700), isik.get("dolgu_konum", (12, -8, 10)),
             (0, 0, 15), boy=9.0)
    isik_kur("Rim", isik.get("rim", 4200), isik.get("rim_konum", (6, 14, 30)),
             (0, 0, 24), boy=4.0)

    refs = roket.kur()
    roket.gimbal_pozu(refs, cfg.get("gimbal", 0.0))
    if cfg.get("havada", 0.0) > 0:
        refs["kok"].location.z += cfg["havada"]
    if cfg.get("ayrilma", 0.0) > 0:
        roket.ayrilma_pozu(refs, cfg["ayrilma"])
        refs["isik"].data.energy = 0

    cam_cfg = cfg["camera"]
    cam_obj = kamera_kur(cam_cfg["position"], cam_cfg["look_at"],
                         cam_cfg.get("lens", 50))

    if a.gif:
        cfg["render"] = {**cfg.get("render", {}), "width": 1280, "height": 720,
                         "samples": 48}
        out = os.path.splitext(cfg["output"])[0] + ".gif"
    else:
        out = cfg["output"]
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)

    if not a.gif:
        sc.render.filepath = out
        bpy.ops.render.render(write_still=True)
        print(f"== BİTTİ -> {out}")
        return

    tmp = out + ".frames"
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    for f in range(a.gif):
        t = f / a.fps
        roket.motor_pozu(refs, t, cfg.get("gimbal_genlik", 5.0))
        sc.render.filepath = f"{tmp}/f{f:05d}.png"
        bpy.ops.render.render(write_still=True)
        print(f"  kare {f + 1}/{a.gif}")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(a.fps),
                    "-i", f"{tmp}/f%05d.png",
                    "-vf", "palettegen=max_colors=256:stats_mode=diff",
                    f"{tmp}/pal.png"], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(a.fps),
                    "-i", f"{tmp}/f%05d.png", "-i", f"{tmp}/pal.png",
                    "-lavfi", "paletteuse=dither=bayer:bayer_scale=3:diff_mode=rectangle",
                    "-loop", "0", out], check=True)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"== BİTTİ -> {out}")


if __name__ == "__main__":
    main()
