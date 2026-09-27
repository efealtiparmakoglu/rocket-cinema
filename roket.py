#!/usr/bin/env python3
"""rocket-cinema — iki kademeli roket (Blender icinde).

Yerlesim: +Z yukari, origin = motor nozul ucu duzlemi (z=0).
    kademe-1 : z 1.4 .. 23.4  (govde)      motor: z 0..1.4 (gimbal pivot z=1.4)
    ara kat  : z 23.4 .. 25.4 (siyah)
    kademe-2 : z 25.4 .. 33.4
    zarf     : z 33.4 .. 40.6 (koni) + yuk

Fonksiyonel kisim: gimbal_pozu(refs, aci_deg) — nozul pivot etrafinda egilir,
alev konisi yone uyar, isik nozuldan gelir. ayrilma_pozu(refs, mesafe)
kademe-1 + ara kati asagi indirir (gercek ayirma düzleminden).
"""

import math

import bpy
from mathutils import Vector

MAT = {}


def mat_yap(ad, renk, rough=0.5, metalik=0.0, emissive=None):
    if ad in MAT:
        return MAT[ad]
    m = bpy.data.materials.new(ad)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (renk[0], renk[1], renk[2], 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metalik
    if emissive is not None:
        nt.nodes.remove(b)
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (renk[0], renk[1], renk[2], 1)
        em.inputs["Strength"].default_value = emissive
        outn = nt.nodes.get("Material Output")
        nt.links.new(em.outputs["Emission"], outn.inputs["Surface"])
    MAT[ad] = m
    return m


def kutu(ad, merkez, boyut, mat):
    bpy.ops.mesh.primitive_cube_add(size=1, location=merkez)
    o = bpy.context.active_object
    o.name = ad
    o.scale = boyut
    o.data.materials.append(mat)
    return o


def silindir(ad, merkez, r1, r2, derinlik, mat, vert=32):
    """Koni/silindir: r1 alt, r2 ust yaricap."""
    bpy.ops.mesh.primitive_cone_add(radius1=r1, radius2=r2, depth=derinlik,
                                    location=merkez, vertices=vert)
    o = bpy.context.active_object
    o.name = ad
    o.data.materials.append(mat)
    return o


def kur():
    """Roketi kurar; poz referanslarini dondurur."""
    MAT.clear()
    beyaz = mat_yap("GovdeBeyaz", (0.82, 0.82, 0.83), rough=0.35)
    siyah = mat_yap("AraKatSiyah", (0.012, 0.012, 0.014), rough=0.4)
    gri = mat_yap("MotorGri", (0.28, 0.28, 0.30), rough=0.35, metalik=0.85)
    bakir = mat_yap("Nozul", (0.45, 0.26, 0.14), rough=0.3, metalik=0.9)
    turuncu = mat_yap("Serit", (0.55, 0.12, 0.03), rough=0.5)

    kok = bpy.data.objects.new("Roket", None)
    bpy.context.collection.objects.link(kok)
    once = set(bpy.data.objects)
    refs = {"kok": kok, "gimbal": None, "alev": None, "isik": None,
            "kademe1": [], "kademe2": []}

    # ---------------- kademe-1 (etek z 2.2..4.4, govde 4.4..26.4)
    silindir("K1_Etek", (0, 0, 3.3), 2.0, 2.0, 2.2, gri)
    silindir("K1_Govde", (0, 0, 15.4), 1.85, 1.85, 22.0, beyaz)
    silindir("K1_Serit", (0, 0, 24.5), 1.86, 1.86, 0.5, turuncu)
    silindir("K1_UcKapak", (0, 0, 26.3), 1.85, 1.85, 0.2, gri)

    # ---------------- ara kat (siyah) 26.4..28.4
    silindir("AraKat", (0, 0, 27.4), 1.85, 1.85, 2.0, siyah)

    # ---------------- kademe-2  28.4..36.4
    silindir("K2_Govde", (0, 0, 32.4), 1.85, 1.85, 8.0, beyaz)

    # ---------------- zarf + yuk  36.4..43.6 + uc koni
    silindir("Zarf", (0, 0, 40.0), 1.85, 1.85, 7.2, beyaz)
    silindir("ZarfUc", (0, 0, 44.3), 1.85, 0.0, 1.4, beyaz)

    # ---------------- gimbal motor: pivot z=2.2, can agzi z 0.7..2.1
    pivot = bpy.data.objects.new("GimbalPivot", None)
    pivot.location = (0, 0, 2.2)
    bpy.context.collection.objects.link(pivot)
    nozul = silindir("Nozul", (0, 0, -0.8), 0.92, 0.30, 1.4, bakir)
    nozul.parent = pivot
    bogaz = silindir("NozulBogaz", (0, 0, 0.4), 0.35, 0.35, 1.2, gri)
    bogaz.parent = pivot
    kutu("TurboGodugu", (0.42, 0, 0.6), (0.5, 0.35, 0.35), gri).parent = pivot

    # ---------------- alev konisi (nozuldan asagiya, zemin uzerinde biter)
    alev_m = mat_yap("Alev", (1.0, 0.55, 0.15), emissive=2.6)
    ic_m = mat_yap("AlevIc", (1.0, 0.85, 0.4), emissive=2.6)
    alev = silindir("AlevKoni", (0, 0, -1.6), 0.30, 0.85, 2.2, alev_m)
    alev.parent = pivot
    ic = silindir("AlevIc", (0, 0, -1.1), 0.20, 0.50, 1.4, ic_m)
    ic.parent = pivot
    isik_data = bpy.data.lights.new("AlevIsik", "POINT")
    isik_data.energy = 1500
    isik_data.color = (1.0, 0.5, 0.15)
    isik_data.shadow_soft_size = 0.8
    isik = bpy.data.objects.new("AlevIsik", isik_data)
    isik.location = (0, 0, -0.6)
    bpy.context.collection.objects.link(isik)
    isik.parent = pivot
    refs["gimbal"] = pivot
    refs["alev"] = (alev, ic)
    refs["isik"] = isik

    # ---------------- yer tutucu: lansman klepeleri 4 nokta
    for i, (dx, dy) in enumerate(((1.4, 1.4), (1.4, -1.4), (-1.4, 1.4), (-1.4, -1.4))):
        ayak = kutu(f"Tutucu{i}", (dx, dy, 0.35), (0.5, 0.5, 0.7), gri)

    # parent: kademe-1 + ara kat hepsi koke; gimbal pivot da koke
    for o in set(bpy.data.objects) - once:
        if o is not kok and o.parent is None:
            o.parent = kok

    # kademe ayirma referanslari: kademe-1 + ara kat listesi
    refs["kademe1"] = [bpy.data.objects[n] for n in
                       ("K1_Govde", "K1_Serit", "K1_Etik", "K1_UcKapak", "AraKat")
                       if n in bpy.data.objects]
    refs["kademe2"] = [bpy.data.objects[n] for n in
                       ("K2_Govde", "Zarf", "ZarfUc") if n in bpy.data.objects]
    return refs


def gimbal_pozu(refs, aci_deg):
    """Nozulu dikeyden aci kadar eg (+X yonune); alev ve isik takip eder."""
    refs["gimbal"].rotation_euler = (0, math.radians(aci_deg), 0)


def ayrilma_pozu(refs, mesafe):
    """Kademe-1 + ara kati asagi ayirir (ayrilma sonrasi goruntuler)."""
    for o in refs["kademe1"]:
        o.location.z -= mesafe


def motor_pozu(refs, t, aci_genlik=5.0):
    """GIF icin: sinuzoidal gimbal + alev titremesi."""
    aci = aci_genlik * math.sin(t * 2.2)
    gimbal_pozu(refs, aci)
    titrek = 1.0 + 0.12 * math.sin(t * 31.0) + 0.06 * math.sin(t * 57.0)
    alev, ic = refs["alev"]
    alev.scale = (titrek, titrek, 1.0 + 0.15 * math.sin(t * 40.0))
    ic.scale = (titrek, titrek, 1.0 + 0.2 * math.sin(t * 47.0))
    refs["isik"].data.energy = 4000 * titrek
