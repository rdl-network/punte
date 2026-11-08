# -*- coding: utf-8 -*-
"""instaleaza — pune puntea Claude ↔ cadwork 3D pe un calculator Windows cu cadwork 2026 (v0, 5 nov 2026).

Rulează din folderul `punte`, cu Python-ul obișnuit (3.10+):
    python instaleaza.py              instalează
    python instaleaza.py --scoate     dezinstalează (pluginurile + intrarea din Claude Desktop)

Ce face:
  1. copiază pluginurile `punte_viu_rdl` (puntea vie) și `punte_rdl` (puntea cu buton) în profilul cadwork:
       C:\\Users\\Public\\Documents\\cadwork\\userprofil_2026\\3d\\API.x64\\<nume>\\<nume>.py
  2. instalează pachetul Python `mcp` (serverul MCP are nevoie de el);
  3. înscrie serverul `punte-cadwork` în Claude Desktop (%APPDATA%\\Claude\\claude_desktop_config.json; copie de siguranță înainte);
  4. dacă există comanda `claude` (Claude Code), îl înscrie și acolo;
  5. îți spune ce mai ai de făcut: repornești Claude Desktop, deschizi cadwork, apeși o dată `punte_viu_rdl`.
Nu atinge nimic altceva. Nu trimite nimic pe internet în afară de descărcarea pachetului `mcp`.
"""
import os
import sys
import json
import glob
import shutil
import datetime
import subprocess

AICI = os.path.dirname(os.path.abspath(__file__))
PLUGINURI = ("punte_viu_rdl", "punte_rdl")
SERVER = os.path.join(AICI, "server_punte_rdl.py")
NUME_SERVER = "punte-cadwork"


def spune(text):
    print(text)


def profil_cadwork():
    """Folderul API.x64 al profilului cadwork (cel mai nou userprofil_*)."""
    candidati = sorted(glob.glob(r"C:\Users\Public\Documents\cadwork\userprofil_*\3d\API.x64"))
    if not candidati:
        candidati = sorted(glob.glob(os.path.join(os.path.expanduser("~"), "Documents", "cadwork", "userprofil_*", "3d", "API.x64")))
    return candidati[-1] if candidati else None


def instaleaza_pluginuri(api):
    for nume in PLUGINURI:
        sursa = os.path.join(AICI, nume + ".py")
        if not os.path.exists(sursa):
            spune(f"  LIPSĂ: {sursa}")
            continue
        dest = os.path.join(api, nume)
        os.makedirs(dest, exist_ok=True)
        shutil.copy(sursa, os.path.join(dest, nume + ".py"))
        spune(f"  plugin {nume} → {dest}")


def scoate_pluginuri(api):
    for nume in PLUGINURI:
        dest = os.path.join(api, nume)
        if os.path.isdir(dest):
            shutil.rmtree(dest)
            spune(f"  scos pluginul {nume}")


def instaleaza_mcp():
    try:
        import mcp  # noqa: F401
        spune("  pachetul mcp: deja instalat")
        return True
    except ImportError:
        pass
    spune("  instalez pachetul mcp (pip)…")
    r = subprocess.run([sys.executable, "-m", "pip", "install", "--user", "-q", "mcp"], capture_output=True, text=True)
    if r.returncode != 0:
        spune("  pip a dat eroare:\n" + (r.stderr or r.stdout)[-800:])
        return False
    spune("  pachetul mcp: instalat")
    return True


def config_claude_desktop():
    return os.path.join(os.environ.get("APPDATA", ""), "Claude", "claude_desktop_config.json")


def inscrie_claude_desktop():
    cfg = config_claude_desktop()
    d = {}
    if os.path.exists(cfg):
        shutil.copy(cfg, cfg + ".bak-" + datetime.datetime.now().strftime("%Y%m%d-%H%M"))
        with open(cfg, encoding="utf-8") as f:
            d = json.load(f)
    else:
        os.makedirs(os.path.dirname(cfg), exist_ok=True)
    d.setdefault("mcpServers", {})[NUME_SERVER] = {"command": sys.executable, "args": [SERVER]}
    with open(cfg, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    spune(f"  Claude Desktop: {NUME_SERVER} înscris în {cfg}")


def scoate_claude_desktop():
    cfg = config_claude_desktop()
    if not os.path.exists(cfg):
        return
    with open(cfg, encoding="utf-8") as f:
        d = json.load(f)
    if NUME_SERVER in d.get("mcpServers", {}):
        shutil.copy(cfg, cfg + ".bak-" + datetime.datetime.now().strftime("%Y%m%d-%H%M"))
        del d["mcpServers"][NUME_SERVER]
        with open(cfg, "w", encoding="utf-8") as f:
            json.dump(d, f, indent=2, ensure_ascii=False)
        spune(f"  Claude Desktop: {NUME_SERVER} scos din config")


def inscrie_claude_code():
    claude = shutil.which("claude")
    if not claude:
        spune("  Claude Code: comanda `claude` nu e în PATH, sar peste (opțional)")
        return
    r = subprocess.run([claude, "mcp", "add", NUME_SERVER, "--", sys.executable, SERVER], capture_output=True, text=True, shell=True)
    spune("  Claude Code: " + ((r.stdout or r.stderr).strip().splitlines() or ["?"])[-1])


def main():
    scoate = "--scoate" in sys.argv
    spune("Puntea Claude ↔ cadwork 3D — " + ("dezinstalare" if scoate else "instalare"))
    api = profil_cadwork()
    if not api:
        spune("  NU găsesc profilul cadwork (userprofil_*\\3d\\API.x64). E instalat cadwork 2026? Deschide-l o dată, apoi rulează din nou.")
        return 1
    spune(f"  profilul cadwork: {api}")
    if scoate:
        scoate_pluginuri(api)
        scoate_claude_desktop()
        spune("Gata. Repornește Claude Desktop ca să uite serverul.")
        return 0
    instaleaza_pluginuri(api)
    if not instaleaza_mcp():
        spune("  Fără pachetul mcp serverul nu pornește. Rulează manual: python -m pip install mcp")
    inscrie_claude_desktop()
    inscrie_claude_code()
    spune("")
    spune("Mai ai de făcut, o singură dată:")
    spune("  1. Închide complet Claude Desktop (clic dreapta pe pictograma de lângă ceas → Quit) și deschide-l din nou.")
    spune("  2. Deschide cadwork 3D cu modelul tău. Dacă cadwork era deja deschis, închide-l și deschide-l din nou (pluginurile noi apar la pornire).")
    spune("  3. În cadwork: Window → User Plugins → apasă o dată `punte_viu_rdl`. În bara de jos apare „Puntea RDL e vie pe portul 53900, modul «întreabă»”.")
    spune("  4. În Claude Desktop, conversație nouă: „Citește modelul din cadwork și scoate lista de materiale.”")
    punte = os.path.join(os.path.expanduser("~"), "cadwork-punte")
    spune("Modul de permisiune (fișierul " + os.path.join(punte, "mod.txt") + "): «intreaba» = Claude cere un Da în cadwork înainte de orice")
    spune("  modificare (implicit); «citire» = Claude doar citește modelul; «liber» = rulează fără să întrebe. Claude se poate restrânge singur,")
    spune("  dar spre mai liber trece doar dacă accepți dialogul din cadwork. Îl poți schimba oricând scriind cuvântul în fișier.")
    spune("Oprirea punții, oricând: creează fișierul stop.txt în " + punte + " sau închide cadwork.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
