#!/usr/bin/env python3
"""rocket-cinema dogrulama kapilari (Blender'siz: python3 tests/verify.py)"""

import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import roket_fizik as rf  # noqa: E402


def main():
    ok, fail = 0, 0

    def kapil(ad, kosul, detay=""):
        nonlocal ok, fail
        if kosul:
            ok += 1
            print(f"  [ok] {ad} {detay}")
        else:
            fail += 1
            print(f"  [FAIL] {ad} {detay}")

    # 1) kalkis TWR > 1 (yerden kalkabilmek icin zorunlu)
    twr = rf.kalkis_twr()
    kapil("kalkis itki/agani > 1", twr > 1.0, f"(TWR = {twr:.2f})")

    # 2) TSIOLKOVSKY kapisi k1: entegre deltav = ve * ln(m0/m1), %0.2 icinde
    ust = rf.K2["kuru"] + rf.K2["yakit"] + rf.YUK
    ideal1 = rf.tsiolkovsky(rf.K1, ust)
    T, Z, V, M, K, (dv1, dv2) = rf.ucus_sim(dt=0.01)
    kapil("kademe-1 deltav = Tsiolkovsky", abs(dv1 - ideal1) / ideal1 < 0.002,
          f"({dv1:.1f} ~ {ideal1:.1f} m/s, sapma %{abs(dv1 - ideal1) / ideal1 * 100:.3f})")

    # 3) TSIOLKOVSKY kapisi k2
    ideal2 = rf.tsiolkovsky(rf.K2, rf.YUK)
    kapil("kademe-2 deltav = Tsiolkovsky", abs(dv2 - ideal2) / ideal2 < 0.002,
          f"({dv2:.1f} ~ {ideal2:.1f} m/s, sapma %{abs(dv2 - ideal2) / ideal2 * 100:.3f})")

    # 4) kademe gecisi: kutle tam kuru-1 kadar dusuyor, hiz kesintisiz
    m1_sure = rf.K1["yakit"] / (rf.K1["itki_kN"] / rf.K1["ve"])
    m_once, k_once = rf.toplam_kutle(m1_sure - 0.01)
    m_sonra, k_sonra = rf.toplam_kutle(m1_sure + rf.GECIS_S + 0.01)
    dusen = m_once - m_sonra
    kapil("kademe ayrilmasi kutle dususu = kuru-1",
          abs(dusen - rf.K1["kuru"]) < 0.05, f"(dusen {dusen:.2f} t)")
    v_once = V[min(range(len(T)), key=lambda i: abs(T[i] - (m1_sure - 0.01)))]
    v_sonra = V[min(range(len(T)), key=lambda i: abs(T[i] - (m1_sure + rf.GECIS_S + 0.01)))]
    kapil("urei ukunusu hiz kaybini gosterir (g - t)", v_once > v_sonra,
          f"({v_once:.0f} -> {v_sonra:.0f} m/s)")

    # 5) gimbal: birim vektor + yan bilesen sin(a)
    d = rf.gimbal_yonu(6.0)
    kapil("gimbal yonu birim", abs(math.hypot(d[0], d[1], d[2]) - 1.0) < 1e-12)
    kapil("yan kuvvet orani = sin(aci)",
          abs(rf.yan_kuvvet_orani(6.0) - math.sin(math.radians(6.0))) < 1e-12)

    # 6) yorunge ucu: sim yuksekligi pozitif bitiyor (uzaya ulasti)
    kapil("sim sonunda yukseklik > 100 km", Z[-1] > 100_000,
          f"(z_son = {Z[-1] / 1000:.0f} km)")

    # 7) determinizm: ayni cagri iki kez — birebir ayni sonuc
    a1 = rf.ucus_sim()
    a2 = rf.ucus_sim()
    kapil("determinizm", a1 == a2)

    print(f"\n{'TUM KAPILAR GECTI' if fail == 0 else 'KAPILARDA FAIL VAR'}"
          f" ({ok} ok, {fail} fail)")
    sys.exit(0 if fail == 0 else 1)


if __name__ == "__main__":
    main()
