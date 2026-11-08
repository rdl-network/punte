# -*- coding: utf-8 -*-
"""test_viu — clientul de test al punții rezidente (rulează în Python-ul obișnuit, pe același calculator cu cadwork).

  python test_viu.py ping
  python test_viu.py mod                          (modul de permisiune curent)
  python test_viu.py mod citire|intreaba|liber    (schimbă modul; spre mai liber = dialog Da/Nu în cadwork)
  python test_viu.py lista
  python test_viu.py selectie                     (fișele elementelor selectate de om în fereastra cadwork)
  python test_viu.py amprenta                     (amprenta modelului → amprenta_test.json lângă script)
  python test_viu.py diff                         (ce s-a schimbat față de amprenta_test.json)
  python test_viu.py selectie-cod                 (cod «citire» care folosește lista SELECTIE: volumul pieselor selectate)
  python test_viu.py ruleaza                      (desenează o grindă de test „Punte viu T1” și o listează; după mod)
  python test_viu.py citeste                      (cod declarat «citire»: numără elementele; rulează fără întrebare)
  python test_viu.py smecher                      (cod declarat «citire» care încearcă să creeze o grindă: garda îl refuză)
  python test_viu.py curata                       (șterge, cu undo, toate grinzile de test „Punte viu T1”; după mod)
  python test_viu.py anuleaza                     (șterge, cu undo, ce a creat ultimul job; după mod)
  python test_viu.py stop
"""
import os
import sys
import json
import time
import socket

PORTURI = (53900, 53901, 53902)

COD_TEST = r'''
import cadwork
eid = ec.create_rectangular_beam_vectors(100.0, 200.0, 1500.0, cadwork.point_3d(0.0, -2000.0, 0.0),
                                        cadwork.point_3d(1.0, 0.0, 0.0), cadwork.point_3d(0.0, 0.0, 1.0))
ac.set_name([eid], "Punte viu T1")
print("grinda de test creata, id", eid, "volum m3", round(gc.get_volume(eid) / 1e9, 4))
raspuns["id"] = eid
raspuns["elemente_in_model"] = len(ec.get_all_identifiable_element_ids())
'''

COD_SELECTIE = r'''
vol = sum(gc.get_volume(eid) for eid in SELECTIE) / 1e9
nume = [ac.get_name(eid) for eid in SELECTIE]
print("selectate:", len(SELECTIE), nume, "volum m3", round(vol, 4))
raspuns["selectate"] = len(SELECTIE)
raspuns["volum_m3"] = round(vol, 4)
'''

COD_CURATA = r'''
de_sters = [eid for eid in ec.get_all_identifiable_element_ids() if ac.get_name(eid) == "Punte viu T1"]
if de_sters:
    ec.delete_elements_with_undo(de_sters)
print("sterse grinzile de test:", de_sters)
raspuns["sterse_test"] = de_sters
'''

COD_CITIRE = r'''
from collections import Counter
ids = ec.get_all_identifiable_element_ids()
c = Counter()
for eid in ids:
    et = ac.get_element_type(eid)
    c["ecarisat" if et.is_rectangular_beam() else "altele"] += 1
print("elemente:", len(ids), dict(c))
raspuns["elemente"] = len(ids)
raspuns["pe_tip"] = dict(c)
'''

COD_SMECHER = r'''
import cadwork
# declarat «citire», dar incearca sa creeze: garda trebuie sa-l refuze inainte de rulare
eid = ec.create_rectangular_beam_vectors(100.0, 100.0, 1000.0, cadwork.point_3d(0.0, -3000.0, 0.0),
                                        cadwork.point_3d(1.0, 0.0, 0.0), cadwork.point_3d(0.0, 0.0, 1.0))
raspuns["id"] = eid
'''


DIALOG = os.path.join(os.path.expanduser("~"), "cadwork-punte", "dialog.txt")


def cere(cerere, timeout=600):
    ultima = None
    if os.path.exists(DIALOG) and time.time() - os.path.getmtime(DIALOG) < 2 * 3600:
        with open(DIALOG, encoding="utf-8") as f:
            d = json.load(f)
        de = int(time.time() - os.path.getmtime(DIALOG))
        if cerere.get("op") == "ping":
            return {"ok": True, "ocupat": True, "dialog": d.get("intrebare"), "dialog_de_s": de}
        return {"ok": False, "refuzat": True, "ocupat": True, "dialog": d.get("intrebare"), "dialog_de_s": de,
                "eroare": f"puntea e ocupata: dialogul «{d.get('intrebare')}» e deschis in cadwork de {de} s; raspunde acolo intai"}
    for p in PORTURI:
        try:
            s = socket.create_connection(("127.0.0.1", p), timeout=5)
        except OSError as e:
            ultima = e
            continue
        with s:
            try:
                s.settimeout(timeout)
                s.sendall((json.dumps(cerere, ensure_ascii=False) + "\n").encode("utf-8"))
                linie = s.makefile("rb").readline()
            except socket.timeout:
                return {"ok": False, "timeout": True, "eroare": f"puntea e pe portul {p}, dar nu a raspuns in {timeout} s (dialog deschis in cadwork?)"}
            return json.loads(linie.decode("utf-8"))
    return {"ok": False, "eroare": f"puntea nu raspunde pe niciun port {PORTURI}: {ultima}"}


def main():
    op = sys.argv[1] if len(sys.argv) > 1 else "ping"
    if op == "ruleaza":
        cerere = {"op": "ruleaza", "cod": COD_TEST, "descriere": "grinda de test prin puntea vie"}
    elif op == "diff":
        with open("amprenta_test.json", encoding="utf-8") as f:
            cerere = {"op": "diff", "amprenta": json.load(f).get("amprenta") or {}}
    elif op == "selectie-cod":
        cerere = {"op": "ruleaza", "cod": COD_SELECTIE, "descriere": "volumul pieselor selectate (doar citire)", "citire": True}
    elif op == "curata":
        cerere = {"op": "ruleaza", "cod": COD_CURATA, "descriere": "sterg grinzile de test Punte viu T1"}
    elif op == "citeste":
        cerere = {"op": "ruleaza", "cod": COD_CITIRE, "descriere": "numar elementele (doar citire)", "citire": True}
    elif op == "smecher":
        cerere = {"op": "ruleaza", "cod": COD_SMECHER, "descriere": "test garda: creare declarata citire", "citire": True}
    elif op == "mod" and len(sys.argv) > 2:
        cerere = {"op": "seteaza_mod", "mod": sys.argv[2], "motiv": " ".join(sys.argv[3:]) or "test din test_viu"}
    else:
        cerere = {"op": op}
    r = cere(cerere, timeout=15 if op in ("stop", "ping", "mod", "lista", "selectie", "amprenta", "diff") and cerere.get("op") != "seteaza_mod" else 600)
    if op == "amprenta" and r.get("ok"):
        with open("amprenta_test.json", "w", encoding="utf-8") as f:
            json.dump(r, f, ensure_ascii=False)
        print(f"amprenta salvata: model {r.get('model')}, {r.get('elemente')} elemente, {r.get('cand')} -> amprenta_test.json")
    elif op == "selectie" and r.get("ok"):
        piese = r["piese"]
        print(f"model {r.get('model')}: {len(piese)} selectate din {r.get('elemente')}, mod {r.get('mod')}, ids {r.get('ids')}")
        for pz in piese:
            print(f"  {pz['nume']:<16} {pz['categorie']:<10} {pz['material']:<10} {pz['latime_mm']:>4} x {pz['inaltime_mm']:<4} L {pz['lungime_mm']:>5}  {pz['volum_m3']:.4f} m3")
    elif op == "lista" and r.get("ok"):
        piese = r["piese"]
        print(f"model {r.get('model')}: {len(piese)} elemente, mod {r.get('mod')}")
        for pz in piese:
            print(f"  {pz['nume']:<16} {pz['categorie']:<10} {pz['material']:<10} {pz['latime_mm']:>4} x {pz['inaltime_mm']:<4} L {pz['lungime_mm']:>5}  {pz['volum_m3']:.4f} m3")
    else:
        print(json.dumps(r, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
