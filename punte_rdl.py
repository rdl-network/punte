# -*- coding: utf-8 -*-
"""punte_rdl — „puntea cu buton” între Claude și cadwork 3D, v0 (Revista din Lemn / Hub-ul Lemnului, 5 nov 2026).

Cum merge, în trei pași:
  1. Claude (prin serverul MCP `server_punte_rdl.py`, din Claude Desktop sau Claude Code) scrie comanda ca fișier Python:
        %USERPROFILE%\\cadwork-punte\\job.py
  2. Omul apasă butonul `punte_rdl` din cadwork 3D (Window → User Plugins). Pluginul rulează jobul în cadwork,
     cu modulele cwapi3d la îndemână (cadwork, ec, ac, gc, mc, uc), prinde tot ce a scris jobul (print + `raspuns`)
     și scrie:
        %USERPROFILE%\\cadwork-punte\\rezultat.json  (pentru Claude)
        %USERPROFILE%\\cadwork-punte\\rezultat.txt   (pentru om)
     Elementele create de job intră în undo (Ctrl+Z) și sunt ținute minte în `ultimul_job.json`, ca Claude să le poată
     anula la cerere. Jobul rulat se mută în `istoric\\` (jurnalul punții); job.py dispare, ca un al doilea click să nu-l
     ruleze a doua oară.
  3. Claude citește rezultatul.

De ce „cu buton” și nu server în cadwork: apăsarea e aprobarea omului; nu ține fire sau socketuri în cadwork
(apelurile cwapi3d merg doar pe firul principal); cadwork își anunță propriul MCP (beta.cadwork.ai) — ce facem noi
e stratul de meserie de deasupra, nu infrastructura.

Instalare: folderul `userprofil_2026\\3d\\API.x64\\punte_rdl\\punte_rdl.py`.
"""
import os
import io
import sys
import json
import time
import shutil
import datetime
import traceback

import cadwork
import element_controller as ec
import attribute_controller as ac
import geometry_controller as gc
import material_controller as mc
import utility_controller as uc

PUNTE = os.path.join(os.path.expanduser("~"), "cadwork-punte")
JOB = os.path.join(PUNTE, "job.py")
REZ_JSON = os.path.join(PUNTE, "rezultat.json")
REZ_TXT = os.path.join(PUNTE, "rezultat.txt")
ULTIMUL = os.path.join(PUNTE, "ultimul_job.json")
ISTORIC = os.path.join(PUNTE, "istoric")


def acum():
    return datetime.datetime.now()


def descrierea(cod):
    """Prima linie `# punte: ...` din job, dacă există."""
    for linie in cod.splitlines()[:5]:
        if linie.strip().lower().startswith("# punte:"):
            return linie.split(":", 1)[1].strip()
    return "(fara descriere)"


def json_safe(obj):
    try:
        json.dumps(obj)
        return obj
    except Exception:
        return str(obj)


def scrie_rezultat(rez):
    with open(REZ_JSON, "w", encoding="utf-8") as f:
        json.dump(rez, f, ensure_ascii=False, indent=2, default=str)
    linii = [
        f"Puntea RDL — rezultatul jobului „{rez.get('descriere')}”, {rez.get('cand')}",
        f"Stare: {rez.get('stare')}   model: {rez.get('model')}   durata: {rez.get('durata_s')} s",
        f"Elemente create: {len(rez.get('create', []))}   sterse: {len(rez.get('sterse', []))}",
        "",
        "Ce a scris jobul:",
        rez.get("iesire") or "(nimic)",
    ]
    if rez.get("raspuns"):
        linii += ["", "raspuns:", json.dumps(rez["raspuns"], ensure_ascii=False, indent=2, default=str)]
    if rez.get("eroare"):
        linii += ["", "EROARE:", rez["eroare"]]
    with open(REZ_TXT, "w", encoding="utf-8") as f:
        f.write("\n".join(linii) + "\n")
    return linii


def ruleaza_job(cod):
    """Rulează codul jobului pe firul principal al cadwork, cu stdout prins."""
    ns = {
        "__name__": "__punte__",
        "cadwork": cadwork, "ec": ec, "ac": ac, "gc": gc, "mc": mc, "uc": uc,
        "element_controller": ec, "attribute_controller": ac, "geometry_controller": gc,
        "material_controller": mc, "utility_controller": uc,
        "raspuns": {},
        "PUNTE": PUNTE,
    }
    inainte = set(ec.get_all_identifiable_element_ids())
    buf = io.StringIO()
    stdout_vechi = sys.stdout
    sys.stdout = buf
    eroare = ""
    t0 = time.perf_counter()
    try:
        exec(compile(cod, JOB, "exec"), ns)
    except Exception:
        eroare = traceback.format_exc()
    finally:
        sys.stdout = stdout_vechi
    durata = round(time.perf_counter() - t0, 3)
    dupa = set(ec.get_all_identifiable_element_ids())
    create = sorted(dupa - inainte)
    sterse = sorted(inainte - dupa)
    if create:
        try:
            ec.add_created_elements_to_undo(create)
        except Exception:
            pass
    return {
        "stare": "eroare" if eroare else "ok",
        "iesire": buf.getvalue(),
        "raspuns": {k: json_safe(v) for k, v in ns["raspuns"].items()} if isinstance(ns.get("raspuns"), dict) else json_safe(ns.get("raspuns")),
        "create": create,
        "sterse": sterse,
        "eroare": eroare,
        "durata_s": durata,
    }


def main():
    os.makedirs(ISTORIC, exist_ok=True)
    try:
        model = uc.get_3d_file_name() or "(model nesalvat)"
    except Exception:
        model = "?"
    if not os.path.exists(JOB):
        rez = {"stare": "fara_job", "descriere": "", "cand": acum().isoformat(timespec="seconds"), "model": model,
               "iesire": "Nicio comanda de la Claude: lipseste job.py in " + PUNTE, "create": [], "sterse": [], "durata_s": 0}
        scrie_rezultat(rez)
        uc.print_message("Puntea RDL: nicio comanda de rulat (job.py lipseste)", 1, 1)
        return
    with open(JOB, "r", encoding="utf-8") as f:
        cod = f.read()
    stampila = acum().strftime("%Y%m%d-%H%M%S")
    rez = ruleaza_job(cod)
    rez.update({"descriere": descrierea(cod), "cand": acum().isoformat(timespec="seconds"), "model": model,
                "job": f"istoric/{stampila}_job.py"})
    linii = scrie_rezultat(rez)
    with open(ULTIMUL, "w", encoding="utf-8") as f:
        json.dump({"cand": rez["cand"], "descriere": rez["descriere"], "create": rez["create"], "sterse": rez["sterse"]}, f, ensure_ascii=False)
    shutil.move(JOB, os.path.join(ISTORIC, f"{stampila}_job.py"))
    shutil.copy(REZ_JSON, os.path.join(ISTORIC, f"{stampila}_rezultat.json"))
    for l in linii:
        uc.print_to_console(l)
    if rez["stare"] == "ok":
        uc.print_message(f"Puntea RDL: job „{rez['descriere']}” rulat in {rez['durata_s']} s, {len(rez['create'])} elemente create — rezultatul e la Claude", 1, 1)
    else:
        uc.print_message(f"Puntea RDL: jobul „{rez['descriere']}” a dat eroare — vezi rezultat.txt", 1, 1)


try:
    main()
except Exception:
    os.makedirs(PUNTE, exist_ok=True)
    with open(REZ_TXT, "w", encoding="utf-8") as f:
        f.write("EROARE in punte_rdl:\n" + traceback.format_exc())
    uc.print_message("Puntea RDL: eroare in plugin — vezi rezultat.txt", 1, 1)
