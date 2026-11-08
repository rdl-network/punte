# -*- coding: utf-8 -*-
"""ruleaza_fisier — trimite un fișier de cod Python punții vii și tipărește răspunsul (JSON).

  python ruleaza_fisier.py cod.py                  (declarat «citire»: trece garda, rulează fără întrebare)
  python ruleaza_fisier.py cod.py --scrie "descriere"   (poate modifica modelul: după modul de permisiune, dialog în cadwork)
  python ruleaza_fisier.py cod.py --brut           (tipărește tot răspunsul, nu doar ieșirea + raspuns)
Codul are la îndemână: cadwork, ec, ac, gc, mc, uc, raspuns (dict), SELECTIE (ID-urile selectate), MOD.
"""
import io
import os
import sys
import json

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_viu import cere  # noqa: E402

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    cale = sys.argv[1]
    scrie = "--scrie" in sys.argv
    brut = "--brut" in sys.argv
    descriere = os.path.basename(cale)
    if scrie:
        i = sys.argv.index("--scrie")
        if i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("--"):
            descriere = sys.argv[i + 1]
    with open(cale, encoding="utf-8") as f:
        cod = f.read()
    r = cere({"op": "ruleaza", "cod": cod, "descriere": descriere, "citire": not scrie}, timeout=900)
    if brut or not r.get("ok"):
        print(json.dumps(r, ensure_ascii=False, indent=1))
        return 0 if r.get("ok") else 1
    print(f"[{r.get('stare')} | {r.get('durata_s')} s | model {r.get('model')} | mod {r.get('mod')}"
          f"{' | dialog ' + str(r['dialog_s']) + ' s' if r.get('dialog_s') is not None else ''}]")
    if r.get("iesire"):
        print(r["iesire"].rstrip())
    if r.get("raspuns"):
        print("raspuns:", json.dumps(r["raspuns"], ensure_ascii=False, indent=1))
    sch = r.get("schimbari") or {}
    if sch.get("create") or sch.get("sterse") or sch.get("modificate"):
        print("schimbari:", json.dumps({k: sch.get(k) for k in ("create", "sterse", "modificate")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
