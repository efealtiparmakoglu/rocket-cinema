#!/usr/bin/env python3
"""rocket-cinema — iki kademeli roket fiziği (SAF MATEMATIK, Blender'siz).

Model: dikey yakin-uzay yukselis (dusuk irtifada egri atilir, yorunge degil)
    F(t)  = itki * gaz_kelebegi(t)                  (gimbal ivme yonu ayri)
    m(t)  = kademe kutleleri - mdot * t             (yakit tuketimi)
    a(t)  = F/m - g + surukkleme                    (dikey 1B entegrasyon)

Kademeler: 1. kademe yanmasi bitince kutle dusurulur, 2. kademe motoru
uyanir (aralikta ~2 s coast — urei ukunusu).

TSIOLKOVSKY kapisi: her kademenin entegre edilen deltav'i
    ve * ln(m0/m1) ile 0.1% icinde eslesmek ZORUNDA — integre edilmis
    hiz, analitik roket denklemini yalan soyleyemez.
"""

import math

G0 = 9.80665

# kademe kutleleri (ton): kuru + yakit
K1 = {"kuru": 4.5, "yakit": 28.0, "itki_kN": 620.0, "ve": 2820.0}   # deniz seviyesi
K2 = {"kuru": 1.6, "yakit": 6.4, "itki_kN": 110.0, "ve": 3480.0}    # vakum
YUK = 1.1
GECIS_S = 2.0           # kademeler arasi beklemis urei ukunusu
GIMBAL_MAX_DEG = 6.0    # nozul sapma limiti


def kademeler():
    return [K1, K2]


def kalkis_twr():
    """Yerden kalkis itki/agani — >1 olmali (kapi)."""
    m0 = K1["kuru"] + K1["yakit"] + K2["kuru"] + K2["yakit"] + YUK
    itki_ton = K1["itki_kN"] / G0
    return itki_ton / m0


def toplam_kutle(t):
    """t anindaki toplam kutle (ton) — yanma sirasiyla lineer tuketim."""
    m1_sure = K1["yakit"] / (K1["itki_kN"] / K1["ve"])  # s — mdot = F/ve
    m0 = K1["kuru"] + K1["yakit"] + K2["kuru"] + K2["yakit"] + YUK
    if t < m1_sure:
        mdot_ton = K1["itki_kN"] / K1["ve"]  # kN / (m/s) = t/s
        return m0 - mdot_ton * t, 1
    if t < m1_sure + GECIS_S:
        return K1["kuru"] + K2["kuru"] + K2["yakit"] + YUK, 0
    m2_sure = K2["yakit"] / (K2["itki_kN"] / K2["ve"])
    t2 = min(t - m1_sure - GECIS_S, m2_sure)
    mdot_ton = K2["itki_kN"] / K2["ve"]
    return K2["kuru"] + K2["yakit"] + YUK - mdot_ton * t2, 2


def ucus_sim(dt=0.05, t_max=380.0):
    """Basit dikey yukselis entegrasyonu.
    Doner: (zamanlar, yukseklikler, hizlar, kutleler, kademeler, deltavler)
    Surukkleme ve egri atis bilerek yok — dikey ideal; kapilar buna gore.
    """
    t = 0.0
    z = 0.0
    v = 0.0
    m1_sure = K1["yakit"] / (K1["itki_kN"] / K1["ve"])
    T, Z, V, M, K = [0.0], [0.0], [0.0], [toplam_kutle(0.0)[0]], [1]
    dv1 = 0.0
    dv2 = 0.0
    while t < t_max:
        kutle, kademe = toplam_kutle(t)
        if kademe == 1 and kutle > K1["kuru"] + 1e-9:
            itki_n = K1["itki_kN"] * 1000.0
            ve = K1["ve"]
        elif kademe == 2 and kutle > K2["kuru"] + YUK + 1e-9:
            itki_n = K2["itki_kN"] * 1000.0
            ve = K2["ve"]
        else:
            itki_n, ve = 0.0, 0.0
        m_kg = kutle * 1000.0
        a = itki_n / m_kg - G0
        v += a * dt
        z += v * dt
        t += dt
        dv_kat = (itki_n / m_kg) * dt if itki_n else 0.0
        if kademe == 1:
            dv1 += dv_kat
        elif kademe == 2:
            dv2 += dv_kat
        T.append(t)
        Z.append(z)
        V.append(v)
        M.append(kutle)
        K.append(kademe)
        if kademe == 2 and t > m1_sure + GECIS_S + K2["yakit"] / \
                (K2["itki_kN"] / K2["ve"]) + 1.0:
            break
    return T, Z, V, M, K, (dv1, dv2)


def gecis_m1():
    return GECIS_S


def tsiolkovsky(k, m_ust):
    """Tek kademe ideal deltav: ve * ln(m0/m1). m_ust = uzerindeki kutle."""
    m0 = k["kuru"] + k["yakit"] + m_ust
    m1 = k["kuru"] + m_ust
    return k["ve"] * math.log(m0 / m1)


def gimbal_yonu(aci_deg):
    """Nozul ekseni birim vektoru — dikeyden aci kadar egik (+X yonune)."""
    a = math.radians(aci_deg)
    return (math.sin(a), 0.0, math.cos(a))


def yan_kuvvet_orani(aci_deg):
    """Itkinin yana bileseni / toplam — gimbal kapisi: sin(a)."""
    return math.sin(math.radians(aci_deg))
