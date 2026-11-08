# -*- coding: utf-8 -*-
"""server_punte_rdl — serverul MCP al punții Claude ↔ cadwork 3D, v2 (5–6 nov 2026).

Rulează pe același calculator cu cadwork, în Python-ul obișnuit (3.12, pachetul `mcp`), pornit de Claude Desktop sau
Claude Code prin stdio. Două căi, alese singur la fiecare apel:

  1. PUNTEA VIE (fără buton): pluginul `punte_viu_rdl` rulează în cadwork și ascultă pe 127.0.0.1:53900 (sau 53901/53902).
     Serverul îi trimite comanda pe socket și primește răspunsul pe loc. Așa lucrează nișa „din Claude Desktop, direct”.
  2. PUNTEA CU BUTON (rezerva): dacă puntea vie nu răspunde, serverul scrie comanda în %USERPROFILE%\\cadwork-punte\\job.py,
     omul apasă `punte_rdl` în cadwork, pluginul lasă rezultatul în rezultat.json, iar serverul îl citește cu cadwork_rezultat().

Modul de permisiune (al omului, în %USERPROFILE%\\cadwork-punte\\mod.txt; implicit «intreaba»):
  citire    — Claude doar citește: rulează numai cod declarat doar_citire, trecut prin gardă și verificat cu amprenta modelului.
  intreaba  — orice cod care poate modifica modelul deschide un dialog Da/Nu în fereastra cadwork; omul decide cu un click.
  liber     — rulează pe loc; fiecare job lasă un rând în bara cadwork.
  Claude se poate restrânge singur oricând; spre mai liber trece DOAR cu Da-ul omului în cadwork (cadwork_mod).

Unelte:
  cadwork_stare()                                  — cadwork pornit? puntea vie răspunde? modul? job în așteptare? ultimul rezultat?
  cadwork_mod(mod="", motiv="")                    — citește sau schimbă modul (spre mai liber: dialog în cadwork)
  cadwork_lista_elemente()                         — lista de materiale pe sortimente (ecarisat / panouri / feronerie)
  cadwork_ruleaza_cod(cod, descriere, doar_citire) — cod Python cu cwapi3d (cadwork, ec, ac, gc, mc, uc, raspuns), după mod
  cadwork_anuleaza_ultimul_job()                   — șterge (cu undo) elementele create de ultimul job, după mod
  cadwork_rezultat()                               — rezultatul ultimului job rulat prin buton
  cadwork_opreste_puntea_vie()                     — oprește pluginul rezident (omul o poate face și cu fișierul stop.txt)
  Facilitățile nișei (6–8 nov): cadwork_lista_comanda (lista gata de comandă), cadwork_oferta (oferta de preț),
  cadwork_verificari (ce lipsește / ce nu se leagă) + cadwork_selecteaza (piesele găsite, evidențiate în cadwork).
  Dosarul casei (8 nov): cadwork_dosar_nou (folderul standard al unei lucrări) + cadwork_dosar_stadiu („unde suntem”); cele trei
  facilități primesc `dosar=<cale>` și scriu și acolo (5-comenzi / 2-oferta / 4-proiect), cu o linie în casa.md.

Înregistrare în Claude Code (din folderul proiectului):
  claude mcp add punte-cadwork -- "<python.exe>" "<calea>\\server_punte_rdl.py"
Claude Desktop: %APPDATA%\\Claude\\claude_desktop_config.json → "mcpServers": {"punte-cadwork": {"command": "<python.exe>", "args": ["<calea>\\server_punte_rdl.py"]}}
"""
import os
import json
import socket
import datetime
import subprocess
from collections import OrderedDict

sys_dir = os.path.dirname(os.path.abspath(__file__))
if sys_dir not in __import__('sys').path:
    __import__('sys').path.insert(0, sys_dir)

try:
    from mcp.server.mcpserver import MCPServer as _Server   # SDK-ul mcp 2.x (FastMCP a devenit MCPServer)
except ImportError:
    from mcp.server.fastmcp import FastMCP as _Server       # SDK-ul mcp 1.x

PUNTE = os.path.join(os.path.expanduser("~"), "cadwork-punte")
JOB = os.path.join(PUNTE, "job.py")
REZ_JSON = os.path.join(PUNTE, "rezultat.json")
REZ_TXT = os.path.join(PUNTE, "rezultat.txt")
ULTIMUL = os.path.join(PUNTE, "ultimul_job.json")
MOD = os.path.join(PUNTE, "mod.txt")
DIALOG = os.path.join(PUNTE, "dialog.txt")
AMPRENTE = os.path.join(PUNTE, "amprente")
PORTURI_VII = (53900, 53901, 53902)
MODURI = ("citire", "intreaba", "liber")
NUME_MOD = {"citire": "doar citire", "intreaba": "întreabă", "liber": "liber"}

APASA = "Apasă butonul «punte_rdl» în cadwork 3D (Window → User Plugins), apoi cere cadwork_rezultat()."
PORNESTE_VIE = "Ca să lucrezi fără buton, omul apasă o singură dată «punte_viu_rdl» în cadwork (Window → User Plugins)."
EXPLICA_MOD = ("Modurile: «citire» = Claude doar citește modelul; «intreaba» = orice modificare cere un Da în fereastra cadwork; "
               "«liber» = rulează pe loc. Omul îl schimbă în mod.txt sau acceptând dialogul din cadwork.")

mcp = _Server("punte-cadwork")


def _mod_din_fisier() -> str:
    """Modul din mod.txt (folosit când puntea vie nu răspunde; puntea vie îl citește singură)."""
    try:
        with open(MOD, encoding="utf-8") as f:
            m = f.read().strip().lower()
        return m if m in MODURI else "intreaba"
    except Exception:
        return "intreaba"


# ---------------------------------------------------------------- puntea vie (socket)

def _dialog_deschis():
    """Dialogul Da/Nu deschis în cadwork (fișierul dialog.txt, scris de punte chiar înainte de dialog); None dacă nu e niciunul.
    Cât e dialogul deschis, în procesul cadwork nu rulează niciun rând de Python, deci puntea nu poate răspunde: fișierul e semnalul."""
    try:
        if not os.path.exists(DIALOG):
            return None
        if datetime.datetime.now().timestamp() - os.path.getmtime(DIALOG) > 2 * 3600:
            return None                                   # rămas de la o închidere bruscă
        with open(DIALOG, encoding="utf-8") as f:
            d = json.load(f)
        d["dialog_de_s"] = int(datetime.datetime.now().timestamp() - os.path.getmtime(DIALOG))
        return d
    except Exception:
        return None


def _cere_viu(cerere: dict, timeout: float = 600.0):
    """Trimite o cerere punții vii; None dacă nu răspunde niciun port. Cu un dialog deschis în cadwork răspunde pe loc «ocupată»."""
    d = _dialog_deschis()
    if d:
        comun = {"ocupat": True, "dialog": d.get("intrebare"), "dialog_de_s": d.get("dialog_de_s"), "port": d.get("port"),
                 "mod": _mod_din_fisier(), "versiune_punte": "?"}
        if cerere.get("op") == "ping":
            return {"ok": True, **comun}
        return {"ok": False, "refuzat": True, **comun,
                "eroare": f"puntea e ocupată: dialogul «{d.get('intrebare')}» e deschis în fereastra cadwork de {d.get('dialog_de_s')} s; "
                          f"omul trebuie să răspundă acolo întâi (Da sau Nu), apoi trimite din nou"}
    for p in PORTURI_VII:
        try:
            s = socket.create_connection(("127.0.0.1", p), timeout=3)
        except OSError:
            continue                      # nimeni pe portul ăsta: încerc următorul
        with s:
            try:
                s.settimeout(timeout)
                s.sendall((json.dumps(cerere, ensure_ascii=False) + "\n").encode("utf-8"))
                linie = s.makefile("rb").readline()
            except socket.timeout:
                return {"ok": False, "timeout": True,
                        "eroare": f"puntea vie e pe portul {p}, dar nu a răspuns în {timeout:g} s (dialog deschis în cadwork? script lung?)"}
            except OSError as e:
                return {"ok": False, "eroare": f"puntea de pe portul {p}: {e}"}
            if not linie:
                return {"ok": False, "eroare": f"puntea de pe portul {p} a închis conexiunea fără răspuns"}
            try:
                return json.loads(linie.decode("utf-8"))
            except Exception as e:
                return {"ok": False, "eroare": f"răspuns invalid de la punte: {e}"}
    return None


def _ping():
    return _cere_viu({"op": "ping"}, timeout=10)


# ---------------------------------------------------------------- puntea cu buton (fișiere)

def _cadwork_pornit() -> bool:
    try:
        out = subprocess.run(["tasklist", "/FI", "IMAGENAME eq 3d.exe", "/NH"], capture_output=True, text=True, timeout=10).stdout
        return "3d.exe" in out
    except Exception:
        return False


def _scrie_job(cod: str, descriere: str) -> str:
    os.makedirs(PUNTE, exist_ok=True)
    if os.path.exists(JOB):
        return ("Există deja un job în așteptare (job.py), încă nerulat în cadwork. " + APASA +
                " Dacă vrei să-l înlocuiești, trimite din nou cu descrierea începând cu «inlocuieste:».")
    antet = f"# punte: {descriere.strip() or '(fara descriere)'}\n# scris de Claude la {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\n"
    with open(JOB, "w", encoding="utf-8") as f:
        f.write(antet + cod.rstrip() + "\n")
    return (f"Puntea vie nu e pornită, deci jobul «{descriere}» e scris în {JOB} ({len(cod.splitlines())} linii). "
            + APASA + " " + PORNESTE_VIE)


# ---------------------------------------------------------------- formatarea listei

def _m(mm):
    return f"{mm / 1000:.2f}".replace(".", ",")


def _formateaza_lista(piese, model) -> str:
    linii = [f"Lista de materiale — model {model}, {len(piese)} elemente identificabile"]
    for cat in ("ecarisat", "panouri", "feronerie"):
        sortimente = OrderedDict()
        for pz in piese:
            if pz["categorie"] != cat:
                continue
            cheie = (pz["material"], pz["latime_mm"], pz["inaltime_mm"])
            s = sortimente.setdefault(cheie, {"buc": 0, "lungimi": [], "total": 0, "volum": 0.0})
            s["buc"] += 1
            s["lungimi"].append(pz["lungime_mm"])
            s["total"] += pz["lungime_mm"]
            s["volum"] += pz["volum_m3"]
        linii.append("")
        linii.append(cat.upper() + ":")
        if not sortimente:
            linii.append("  (nimic)")
            continue
        tb = tl = tv = 0
        for (mat, w, h), s in sorted(sortimente.items()):
            lungimi = OrderedDict()
            for l in sorted(s["lungimi"]):
                lungimi[l] = lungimi.get(l, 0) + 1
            lung = ", ".join(f"{_m(l)} ×{n}" for l, n in lungimi.items())
            linii.append(f"  {mat:<10} {w:>4} x {h:<4} mm  {s['buc']:>3} buc   {lung:<30} {_m(s['total']):>7} m   {s['volum']:.4f} m3")
            tb += s["buc"]
            tl += s["total"]
            tv += s["volum"]
        linii.append(f"  TOTAL {cat:<26} {tb:>3} buc   {'':<30} {_m(tl):>7} m   {tv:.4f} m3")
    altele = [pz["nume"] for pz in piese if pz["categorie"] == "altele"]
    linii.append("")
    linii.append("ALTELE (nu intră în cantități): " + (", ".join(altele) if altele else "(nimic)"))
    linii.append("")
    linii.append("Cantitățile sunt nete, din model. Piesele, una pe rând:")
    for pz in piese:
        linii.append(f"  {pz['nume']:<16} {pz['categorie']:<10} {pz['material']:<10} {pz['latime_mm']:>4} x {pz['inaltime_mm']:<4} "
                     f"L {pz['lungime_mm']:>5}  {pz['volum_m3']:.4f} m3  [{pz['grupa']} / {pz['subgrupa']}]")
    return "\n".join(linii)


def _formateaza_rulare(rez: dict) -> str:
    if rez.get("ocupat"):
        return "PUNTEA E OCUPATĂ: " + str(rez.get("eroare"))
    if rez.get("timeout") or ("stare" not in rez and not rez.get("ok") and not rez.get("refuzat")):
        return "EROARE: " + str(rez.get("eroare"))
    if rez.get("refuzat"):
        return (f"REFUZAT (modul «{NUME_MOD.get(rez.get('mod'), rez.get('mod'))}»): {rez.get('eroare')}"
                + (f" [dialogul a stat deschis {rez['dialog_s']} s]" if rez.get("dialog_s") is not None else ""))
    mod = rez.get("mod")
    eticheta = f" [mod {NUME_MOD.get(mod, mod)}{', doar citire' if rez.get('citire') else ''}" \
               f"{(', Da-ul omului în ' + str(rez['dialog_s']) + ' s') if rez.get('dialog_s') is not None else ''}]" if mod else ""
    linii = [f"job «{rez.get('descriere')}»: stare {rez.get('stare')}, {rez.get('durata_s')} s, model {rez.get('model')}, "
             f"create {rez.get('create')}, șterse {rez.get('sterse')}{eticheta}", "", "ieșire:", rez.get("iesire") or "(nimic)"]
    if rez.get("raspuns"):
        linii += ["", "raspuns:", json.dumps(rez["raspuns"], ensure_ascii=False, indent=1, default=str)]
    if rez.get("schimbari"):
        linii += ["", "ce s-a schimbat în model:"] + _linii_diff(rez["schimbari"])
    if rez.get("eroare"):
        linii += ["", "EROARE:", rez["eroare"]]
    return "\n".join(linii)


def _fisa(f) -> str:
    if not f:
        return "(peste limita amprentei: doar ID)"
    nume, mat, w, h, l, vol, p1 = (list(f) + [None] * 7)[:7]
    poz = f"  la P1 {tuple(p1)}" if p1 else ""
    return f"{nume}  {mat}  {w:g} x {h:g}  L {l:g} mm  {(vol or 0) / 1e9:.4f} m3{poz}"


def _linii_diff(d: dict) -> list:
    """Rândurile diff-ului: create / șterse / modificate (câmp: vechi → nou)."""
    linii = []
    create, sterse, modificate = d.get("create") or [], d.get("sterse") or [], d.get("modificate") or []
    if not (create or sterse or modificate):
        return ["  nimic: modelul e neschimbat"]
    for eid in create:
        linii.append(f"  + creat    id {eid}: {_fisa((d.get('fise') or {}).get(str(eid)))}")
    for eid in sterse:
        linii.append(f"  - șters    id {eid}: {_fisa((d.get('fise_sterse') or {}).get(str(eid)))}")
    for m in modificate:
        ce = ", ".join((f"mutat: P1 {tuple(v[0])} → {tuple(v[1])}" if k == "p1_mm" else f"{k}: {v[0]} → {v[1]}")
                       for k, v in (m.get("ce") or {}).items())
        linii.append(f"  ~ schimbat id {m['id']} ({m.get('nume')}): {ce}")
    linii.append(f"  total: {len(create)} create, {len(sterse)} șterse, {len(modificate)} modificate")
    return linii


def _amprenta_cale(nume: str) -> str:
    sigur = "".join(c if c.isalnum() or c in "-_" else "_" for c in (nume or "").strip()) or "ultima"
    return os.path.join(AMPRENTE, sigur + ".json")


def _amprente_salvate() -> list:
    if not os.path.isdir(AMPRENTE):
        return []
    return sorted(os.listdir(AMPRENTE), key=lambda f: os.path.getmtime(os.path.join(AMPRENTE, f)), reverse=True)


# ---------------------------------------------------------------- uneltele

@mcp.tool()
def cadwork_stare() -> str:
    """Starea punții: cadwork 3D pornit sau nu, puntea vie (fără buton) răspunde sau nu, job în așteptare, ultimul rezultat."""
    linii = [f"cadwork 3D: {'pornit' if _cadwork_pornit() else 'NU e pornit'}", f"folderul punții: {PUNTE}"]
    p = _ping()
    if p and p.get("ocupat"):
        linii.append(f"puntea vie: OCUPATĂ — dialogul «{p.get('dialog')}» e deschis în fereastra cadwork de {p.get('dialog_de_s')} s; "
                     f"omul trebuie să răspundă acolo (Da / Nu) înainte de orice altă comandă. Portul {p.get('port')}.")
        mod = p.get("mod") or _mod_din_fisier()
    elif p and p.get("ok"):
        linii.append(f"puntea vie: DA — portul {p.get('port')}, tick {p.get('tick')}, pornită {p.get('pornit')}, "
                     f"model {p.get('model')}, {p.get('elemente')} elemente, {p.get('joburi')} joburi, {p.get('refuzate', 0)} refuzate, "
                     f"cadwork {p.get('versiune_cadwork')}, puntea {p.get('versiune_punte', 'v1')}. Comenzile rulează pe loc, fără buton.")
        if "selectate" in p:
            linii.append(f"selecția omului în cadwork: {p['selectate']} elemente active (cadwork_selectie le citește; în cod = SELECTIE).")
        mod = p.get("mod") or _mod_din_fisier()
    elif p:
        linii.append(f"puntea vie: răspunde cu eroare: {p.get('eroare')}")
        mod = _mod_din_fisier()
    else:
        linii.append("puntea vie: nu răspunde. " + PORNESTE_VIE + " Până atunci merge calea cu buton.")
        mod = _mod_din_fisier()
    linii.append(f"modul de permisiune: «{NUME_MOD[mod]}» ({mod}). " + EXPLICA_MOD)
    if os.path.exists(JOB):
        with open(JOB, encoding="utf-8") as f:
            prima = f.readline().strip()
        linii.append(f"job în așteptare (buton): DA — {prima}. " + APASA)
    else:
        linii.append("job în așteptare (buton): nu")
    if os.path.exists(REZ_JSON):
        try:
            rez = json.load(open(REZ_JSON, encoding="utf-8"))
            linii.append(f"ultimul rezultat prin buton: {rez.get('cand')} — «{rez.get('descriere')}», stare {rez.get('stare')}")
        except Exception as e:
            linii.append(f"ultimul rezultat prin buton: necitibil ({e})")
    return "\n".join(linii)


JOB_LISTA = r'''
from collections import OrderedDict
def categoria(eid):
    et = ac.get_element_type(eid)
    if et.is_rectangular_beam() or et.is_circular_beam():
        return "ecarisat"
    if et.is_panel():
        return "panouri"
    if et.is_connector_axis() or et.is_connector_node():
        return "feronerie"
    return "altele"
piese = []
for eid in ec.get_all_identifiable_element_ids():
    try:
        material = ac.get_element_material_name(eid) or "(fara material)"
    except Exception:
        material = "(fara material)"
    piese.append({"id": eid, "nume": ac.get_name(eid) or "(fara nume)", "categorie": categoria(eid),
                  "material": material, "grupa": ac.get_group(eid) or "", "subgrupa": ac.get_subgroup(eid) or "",
                  "latime_mm": round(gc.get_width(eid)), "inaltime_mm": round(gc.get_height(eid)),
                  "lungime_mm": round(gc.get_length(eid)), "volum_m3": round(gc.get_volume(eid) / 1e9, 5)})
raspuns["piese"] = piese
raspuns["model"] = uc.get_3d_file_name()
print(f"{len(piese)} elemente citite din {raspuns['model']}")
'''


@mcp.tool()
def cadwork_lista_elemente() -> str:
    """Lista de materiale a modelului deschis în cadwork 3D: toate elementele, împărțite pe ecarisat / panouri / feronerie
    și grupate pe sortimente (material + secțiune), cu bucăți, lungimi și volume nete; cadrele de vedere și alte obiecte
    care nu sunt lemn rămân la «altele». Cu puntea vie răspunsul vine pe loc; altfel scrie jobul pentru butonul punte_rdl."""
    r = _cere_viu({"op": "lista"}, timeout=120)
    if r is None:
        return _scrie_job(JOB_LISTA, "lista de materiale pe sortimente")
    if not r.get("ok"):
        return "Puntea vie a răspuns cu eroare: " + str(r.get("eroare"))
    return _formateaza_lista(r["piese"], r.get("model"))


def _formateaza_selectie(r: dict) -> str:
    piese = r.get("piese") or []
    if not piese:
        return (f"Nimic selectat în cadwork (model {r.get('model')}, {r.get('elemente')} elemente). "
                "Omul selectează elementele în fereastra cadwork (click / fereastră de selecție), apoi întreabă din nou.")
    linii = [f"Selecția omului în cadwork — {len(piese)} din {r.get('elemente')} elemente, model {r.get('model')}:"]
    vol = 0.0
    for pz in piese:
        vol += pz["volum_m3"]
        linii.append(f"  id {pz['id']:<11} {pz['nume']:<16} {pz['categorie']:<10} {pz['material']:<10} "
                     f"{pz['latime_mm']:>4} x {pz['inaltime_mm']:<4} L {pz['lungime_mm']:>5}  {pz['volum_m3']:.4f} m3"
                     f"  [{pz['grupa']} / {pz['subgrupa']}]")
    linii.append(f"  volum net total: {vol:.4f} m3. ID-urile de mai sus merg direct în cod (sau lista SELECTIE din cadwork_ruleaza_cod).")
    return "\n".join(linii)


@mcp.tool()
def cadwork_amprenta(nume: str = "") -> str:
    """Salvează amprenta modelului de acum (id → nume, material, secțiune, lungime, volum) ca punct de reper, sub un nume
    (implicit «ultima»). Mai târziu cadwork_diff(nume) spune exact ce s-a schimbat față de ea: ce a fost creat, șters sau
    modificat (câmp cu câmp). Ia-o înainte ca omul să lucreze în model sau înainte de o serie de joburi. Doar cu puntea vie."""
    r = _cere_viu({"op": "amprenta"}, timeout=120)
    if r is None:
        return "Puntea vie nu răspunde, iar amprenta se ia doar pe loc. " + PORNESTE_VIE
    if not r.get("ok"):
        return "Puntea vie a răspuns cu eroare: " + str(r.get("eroare"))
    os.makedirs(AMPRENTE, exist_ok=True)
    cale = _amprenta_cale(nume)
    with open(cale, "w", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False)
    eticheta = os.path.basename(cale)[:-5]
    return (f"Amprentă salvată: «{eticheta}» — model {r.get('model')}, {r.get('elemente')} elemente, {r.get('cand')}. "
            f"Compari mai târziu cu cadwork_diff(\"{eticheta}\"). Amprente salvate: "
            + ", ".join(f[:-5] for f in _amprente_salvate()))


@mcp.tool()
def cadwork_diff(nume: str = "") -> str:
    """Ce s-a schimbat în modelul din cadwork față de amprenta salvată cu cadwork_amprenta(nume) (implicit cea mai recentă):
    elemente create, șterse, modificate (nume / material / secțiune / lungime / volum, vechi → nou). Folosește-o după ce omul
    a lucrat în model („ce ai schimbat?”) sau ca să verifici efectul unei serii de joburi. Doar cu puntea vie."""
    salvate = _amprente_salvate()
    if not salvate:
        return "Nicio amprentă salvată încă. Ia una cu cadwork_amprenta(), apoi compară."
    cale = _amprenta_cale(nume) if nume else os.path.join(AMPRENTE, salvate[0])
    if not os.path.exists(cale):
        return f"Nu există amprenta «{nume}». Salvate: " + ", ".join(f[:-5] for f in salvate)
    with open(cale, encoding="utf-8") as f:
        veche = json.load(f)
    r = _cere_viu({"op": "diff", "amprenta": veche.get("amprenta") or {}}, timeout=120)
    if r is None:
        return "Puntea vie nu răspunde, iar diff-ul se face doar pe loc. " + PORNESTE_VIE
    if not r.get("ok"):
        return "Puntea vie a răspuns cu eroare: " + str(r.get("eroare"))
    alt_model = f", model {veche.get('model')}" if veche.get("model") != r.get("model") else ""
    cap = (f"Diff față de amprenta «{os.path.basename(cale)[:-5]}» ({veche.get('cand')}, {veche.get('elemente')} elemente{alt_model}) "
           f"→ acum {r.get('cand')}, model {r.get('model')}, {r.get('elemente')} elemente:")
    return "\n".join([cap] + _linii_diff(r))


@mcp.tool()
def cadwork_lista_comanda(lungimi_comerciale: str = "", adaos_mm: int = 50, subgrupe: str = "", doar_selectia: bool = False,
                          scurt: bool = True, salveaza: bool = True, dosar: str = "") -> str:
    """LISTA DE MATERIALE GATA DE COMANDĂ din modelul deschis în cadwork 3D (prima facilitate a nișei): lemnul ecarisat pe
    sortimente (material + secțiune), croit pe lungimi comerciale → câte bare de fiecare lungime, m3 de comandat și pierderea
    la croit; panourile pe material + grosime, în m2; ce nu intră în cantități e numărat separat. Salvează raportul (.md) și
    tabelul (.csv, pentru Excel) în cadwork-punte/liste/ — spune omului căile, le poate trimite furnizorului.
    `lungimi_comerciale`: „3,4,5,6” (m) sau „4000 5000 13000” (mm); gol = 3/4/5/6/8/10/12/13 m. `adaos_mm` = adaos de tăiere
    pe piesă. `subgrupe` = „gg01, EG16” → doar pereții/subgrupele acelea. `doar_selectia` = doar ce a selectat omul în cadwork.
    `scurt=False` adaugă, sub fiecare sortiment, lungimile pieselor și ce sunt. Doar citire; cu puntea vie răspunde pe loc.
    `dosar` = calea folderului casei (dosarul casei, vezi cadwork_dosar_nou): lista intră și în `5-comenzi/lista-comanda-<data>.md` + `.csv`,
    cu o linie în `casa.md`. Întreabă omul de dosar când lucrează la o casă anume; fără dosar, rămâne doar în cadwork-punte/liste/."""
    import lista_comanda as lc
    lungimi = lc.parseaza_lungimi(lungimi_comerciale)
    r = _cere_viu({"op": "selectie" if doar_selectia else "lista"}, timeout=180)
    if r is None:
        return "Puntea vie nu răspunde, iar lista de comandă se face pe loc. " + PORNESTE_VIE
    if not r.get("ok"):
        return _formateaza_rulare(r) if r.get("ocupat") or r.get("refuzat") else "Puntea vie a răspuns cu eroare: " + str(r.get("eroare"))
    piese = r.get("piese") or []
    if doar_selectia and not piese:
        return "Nimic selectat în cadwork. Omul selectează piesele (sau un perete întreg), apoi cere din nou lista de comandă."
    frag = [s.strip() for s in subgrupe.replace(";", ",").split(",") if s.strip()] if subgrupe else None
    doar_ids = pereti = None
    if doar_selectia:
        # un perete selectat ca obiect (învelișul lui, categoria «altele», cu subgrupă) = toate piesele din subgrupa aceea
        doar_ids = [p["id"] for p in piese if p["categorie"] in ("ecarisat", "panouri")]
        pereti = sorted({p.get("subgrupa") for p in piese if p["categorie"] not in ("ecarisat", "panouri") and p.get("subgrupa")})
        if pereti:
            tot = _cere_viu({"op": "lista"}, timeout=180)
            if tot and tot.get("ok"):
                piese = tot["piese"]
    rez = lc.calculeaza(piese, lungimi_comerciale=lungimi, adaos_mm=int(adaos_mm), subgrupe=frag,
                        doar_ids=doar_ids, subgrupe_exacte=pereti or None)
    if doar_selectia and rez["piese_in_calcul"] == 0:
        return "Selecția nu conține piese de lemn și niciun perete cu subgrupă. Selectează bârnele sau peretele (învelișul lui)."
    if frag and rez["piese_in_calcul"] == 0:
        return f"Nicio piesă în subgrupele «{subgrupe}». Subgrupele din model le vezi cu cadwork_lista_elemente (coloana din paranteze)."
    text = lc.formateaza(rez, r.get("model"), scurt=scurt)
    if salveaza:
        md, csvp = lc.salveaza(rez, os.path.join(PUNTE, "liste"), r.get("model"), text)
        text += f"\n\nSalvat: {md}\n        {csvp}"
        if dosar:
            nota = (f"{len(rez['ecarisat'])} sortimente, {rez['ecarisat_comanda_m3']:.3f} m3 de comandat, {len(rez['panouri'])} tipuri de panouri".replace(".", ",", 1)
                    + f" (din {r.get('model')}, {rez['piese_in_calcul']} piese)")
            text += _in_dosar(dosar, "5-comenzi", "lista-comanda", [(md, "md"), (csvp, "csv")], nota)
    elif dosar:
        text += "\n\nNU am scris în dosar: salveaza=False."
    return text


@mcp.tool()
def cadwork_oferta(preturi_csv: str = "", lungimi_comerciale: str = "", adaos_mm: int = 50, subgrupe: str = "",
                   doar_selectia: bool = False, client: str = "", obiect: str = "", firma: str = "", dosar: str = "") -> str:
    """OFERTA DE PREȚ pentru structura din modelul deschis în cadwork (sarcina 1 din program): lista de comandă × fișierul de
    prețuri → lemn de structură pe sortimente (m3 de comandat × lei/m3), panouri (m2 × lei/m2), transport, manoperă, regie și
    profit, TVA 21 %, total. `preturi_csv` = calea fișierului de prețuri (CSV cu ;, coloane tip/material/unitate/
    pret_lei_fara_tva/sursa/data/nota); gol = `preturi-referinta.csv` de lângă server, cu prețuri ORIENTATIVE din liste publice
    (noiembrie 2026) — spune-i omului asta și că rândurile cu 0 (manopera, stejar, geam…) sunt DE COMPLETAT și nu intră în total.
    Restul parametrilor ca la cadwork_lista_comanda. Scrie oferta (.md) în cadwork-punte/liste/ și spune calea.
    `dosar` = folderul casei: oferta intră și în `2-oferta/oferta-<data>.md`, cu o linie în `casa.md` (omul o semnează înainte să plece)."""
    import lista_comanda as lc
    import oferta as ofm
    cale = preturi_csv or os.path.join(sys_dir, "preturi-referinta.csv")
    if not os.path.exists(cale):
        return f"Nu găsesc fișierul de prețuri: {cale}"
    pr = ofm.incarca_preturi(cale)
    lungimi = lc.parseaza_lungimi(lungimi_comerciale)
    r = _cere_viu({"op": "selectie" if doar_selectia else "lista"}, timeout=180)
    if r is None:
        return "Puntea vie nu răspunde, iar oferta se face din modelul deschis. " + PORNESTE_VIE
    if not r.get("ok"):
        return _formateaza_rulare(r) if r.get("ocupat") or r.get("refuzat") else "Puntea vie a răspuns cu eroare: " + str(r.get("eroare"))
    piese = r.get("piese") or []
    if doar_selectia and not piese:
        return "Nimic selectat în cadwork. Omul selectează piesele sau un perete, apoi cere din nou oferta."
    frag = [s.strip() for s in subgrupe.replace(";", ",").split(",") if s.strip()] if subgrupe else None
    doar_ids = pereti = None
    if doar_selectia:
        doar_ids = [p["id"] for p in piese if p["categorie"] in ("ecarisat", "panouri")]
        pereti = sorted({p.get("subgrupa") for p in piese if p["categorie"] not in ("ecarisat", "panouri") and p.get("subgrupa")})
        if pereti:
            tot = _cere_viu({"op": "lista"}, timeout=180)
            if tot and tot.get("ok"):
                piese = tot["piese"]
    rez = lc.calculeaza(piese, lungimi_comerciale=lungimi, adaos_mm=int(adaos_mm), subgrupe=frag,
                        doar_ids=doar_ids, subgrupe_exacte=pereti or None)
    if rez["piese_in_calcul"] == 0:
        return "Nicio piesă în calcul (filtrul sau selecția nu prind lemn)."
    of = ofm.calculeaza_oferta(rez, pr)
    text = ofm.formateaza_oferta(of, rez, r.get("model"), client=client, obiect=obiect, firma=firma)
    cale_md = ofm.salveaza_oferta(text, os.path.join(PUNTE, "liste"), r.get("model"))
    text += f"\n\nSalvat: {cale_md}"
    if dosar:
        tot = of.get("total") or ""
        suma = f"{tot:,.0f}".replace(",", ".") if isinstance(tot, (int, float)) and tot else ""
        nota = f"oferta orientativă din model{(' pentru ' + client) if client else ''}" + (f", total {suma} lei cu TVA" if suma else "") \
               + " — de semnat de om înainte să plece"
        text += _in_dosar(dosar, "2-oferta", "oferta", [(cale_md, "md")], nota)
    return text


VERIFICARI_ULTIMELE = os.path.join(PUNTE, "ultimele_verificari.json")


def _in_dosar(dosar: str, etapa: str, baza: str, surse: list, nota: str):
    """Pune fișierele deja scrise (în cadwork-punte/liste/) și în dosarul casei, la etapa lor, cu data în nume, și scrie linia în casa.md.
    Întoarce textul de adăugat la răspuns. `surse` = [(cale_sursă, ext), …]. Nu mută nimic: copiază; nu suprascrie."""
    import shutil
    import dosar as dz
    ok, mesaj = dz.verifica(dosar)
    if not ok:
        return "\n\nNU am scris în dosar: " + mesaj
    puse = []
    for sursa, ext in surse:
        if sursa and os.path.exists(sursa):
            dest = dz.cale_fisier(mesaj, etapa, baza, ext)
            shutil.copyfile(sursa, dest)
            puse.append(dest)
    if not puse:
        return "\n\nNU am scris în dosar: n-aveam ce (salvarea e oprită?)."
    casa = dz.noteaza(mesaj, etapa, f"{os.path.basename(puse[0])}: {nota}")
    return "\n\nÎn dosarul casei: " + "\n                 ".join(puse) + f"\n  + o linie la «{dz.ETICHETA.get(etapa, etapa)}» în {casa}"


@mcp.tool()
def cadwork_verificari(subgrupe: str = "", doar_selectia: bool = False, geometrie: bool = True, buget_s: int = 120,
                       lungime_max_m: float = 13.0, salveaza: bool = True, dosar: str = "") -> str:
    """VERIFICĂRILE PE MODEL — „ce lipsește / ce nu se leagă” în modelul deschis în cadwork 3D (a treia facilitate a nișei).
    Pe lista de piese: lemn fără material / fără nume / fără subgrupă (nu aparține niciunui perete), secțiuni rare la 1–5 mm de
    una des folosită (dimensiune greșită?), piese peste lungimea comercială maximă, piese degenerate, aceeași secțiune cu
    materiale diferite. Pe geometrie (job «citire», cu buget de timp): piese dublate exact, piese care nu ating nimic
    („plutesc”), piese care se întrepătrund (coliziuni), gabaritul. Rezultatul e pe trei niveluri: DE CORECTAT / DE VERIFICAT /
    ÎN REGULĂ, cu fișele pieselor; ID-urile cu probleme rămân salvate pentru cadwork_selecteaza("probleme") — oferă-i omului asta.
    `subgrupe` = „gg01, EG16” → doar pereții aceia; `doar_selectia` = ce a selectat omul (un perete selectat ca obiect se
    desface în piesele lui); `geometrie=False` = doar lista (instant); `buget_s` = secunde pentru contact/coliziune (~0,35 s pe piesă:
    un perete de 40 de piese = 15 s, o casă de 2.000 de piese = ~12 min → pe toată casa cere cu buget_s=900 și spune omului că
    durează; raportul spune oricum cât a acoperit). Doar citire; merge numai cu puntea vie. Salvează .md în
    cadwork-punte/liste/ și spune calea. `dosar` = folderul casei: raportul intră și în `4-proiect/verificari-<data>.md`, cu o linie în `casa.md`."""
    import verificari as vf
    r = _cere_viu({"op": "selectie" if doar_selectia else "lista"}, timeout=180)
    if r is None:
        return "Puntea vie nu răspunde, iar verificările se fac pe modelul deschis. " + PORNESTE_VIE
    if not r.get("ok"):
        return _formateaza_rulare(r) if r.get("ocupat") or r.get("refuzat") else "Puntea vie a răspuns cu eroare: " + str(r.get("eroare"))
    piese = r.get("piese") or []
    if doar_selectia and not piese:
        return "Nimic selectat în cadwork. Omul selectează piesele sau un perete, apoi cere din nou verificările."
    frag = [s.strip() for s in subgrupe.replace(";", ",").split(",") if s.strip()] if subgrupe else None
    doar_ids = pereti = None
    if doar_selectia:
        doar_ids = [p["id"] for p in piese if p["categorie"] in ("ecarisat", "panouri")]
        pereti = sorted({p.get("subgrupa") for p in piese if p["categorie"] not in ("ecarisat", "panouri") and p.get("subgrupa")})
        tot = _cere_viu({"op": "lista"}, timeout=180)          # tot modelul: piesele peretelui selectat + partenerii de contact
        if tot and tot.get("ok"):
            piese = tot["piese"]
    rez = vf.verifica_lista(piese, lungime_max_mm=int(round(float(lungime_max_m) * 1000)), subgrupe=frag,
                            doar_ids=doar_ids, subgrupe_exacte=pereti or None)
    if rez["lemn"] == 0:
        return "Nicio piesă de lemn de verificat (filtrul sau selecția nu prind lemn)."
    nota = ""
    if geometrie:
        lemn_toate = [int(p["id"]) for p in piese if p["categorie"] in ("ecarisat", "panouri")]
        g = _cere_viu({"op": "ruleaza", "cod": vf.cod_geometrie(rez["ids_lemn"], buget_s=max(5, int(buget_s)), lemn_toate=lemn_toate),
                       "descriere": "verificari pe geometrie (dubluri, contact, coliziuni)", "citire": True,
                       "timeout": max(60, int(buget_s) + 120)},          # si puntea asteapta firul principal atat (implicit 600 s)
                      timeout=max(60, int(buget_s) + 150))
        if g and g.get("ok") and g.get("stare") == "ok" and isinstance(g.get("raspuns"), dict):
            rez = vf.combina(rez, vf.verifica_geometrie(g["raspuns"], {int(p["id"]): p for p in piese}))
        else:
            nota = "\n\nGeometria n-a putut fi verificată: " + (g.get("eroare") or g.get("iesire") or str(g)[:300] if g else "puntea nu a răspuns")
    text = vf.formateaza(rez, r.get("model")) + nota
    try:
        with open(VERIFICARI_ULTIMELE, "w", encoding="utf-8") as f:
            json.dump({"cand": rez["cand"], "model": r.get("model"), "probleme": vf.ids_probleme(rez),
                       "pe_constatare": {c["cheie"]: c["ids"] for c in rez["constatari"] if c["ids"]}}, f, ensure_ascii=False)
    except Exception:
        pass
    if salveaza:
        cale = vf.salveaza(text, os.path.join(PUNTE, "liste"), r.get("model"))
        text += f"\n\nSalvat: {cale}"
        if dosar:
            nc = sum(1 for c in rez["constatari"] if c["nivel"] == "corectat")
            nv = sum(1 for c in rez["constatari"] if c["nivel"] == "verificat")
            nota = f"{nc} de corectat, {nv} de verificat, {rez['lemn']} piese de lemn" + (", cu geometrie" if rez.get("geometrie") else ", fără geometrie") + f" (din {r.get('model')})"
            text += _in_dosar(dosar, "4-proiect", "verificari", [(cale, "md")], nota)
    elif dosar:
        text += "\n\nNU am scris în dosar: salveaza=False."
    return text


@mcp.tool()
def cadwork_dosar_nou(cale: str, client: str = "", ce_construim: str = "") -> str:
    """Face DOSARUL CASEI: folderul unei lucrări, în forma standard (dosarul-casei.md) — `1-cerere/ 2-oferta/ 3-contract/ 4-proiect/
    5-comenzi/ 6-productie/ 7-montaj/ 8-receptie/ corespondenta/` + `casa.md` („unde suntem”: client, ce construim, stadiul pe etape,
    următorul pas, istoric). `cale` = folderul casei, de obicei `…\\Case\\AAAA-NNN Client – Localitate` (anul, numărul lucrării în an, clientul,
    localitatea). Nu atinge ce există deja; dacă folderul e deja dosar, doar completează ce lipsește. Apoi uneltele punții primesc `dosar=<cale>`
    și scriu acolo. Nu scrie nimic în afara folderului dat."""
    import dosar as dz
    try:
        create = dz.creeaza(cale, client=client, ce=ce_construim)
    except OSError as e:
        return f"Nu pot face dosarul la {cale}: {e}"
    cale = os.path.abspath(cale)
    if not create:
        return f"Dosarul exista deja, complet: {cale}. Stadiul:\n\n" + (dz.stadiul(cale) or "")
    return (f"Dosarul casei e gata: {cale}\n" + "\n".join("  + " + os.path.relpath(c, cale) if c != cale else "  + (folderul)" for c in create)
            + "\n\nCompletează casa.md (client, ce construim, sursa) sau spune-mi datele și le pun eu. De acum, la lista de comandă / ofertă / verificări, dă-mi dosar=" + cale)


@mcp.tool()
def cadwork_dosar_stadiu(cale: str) -> str:
    """„Unde suntem cu casa asta?” — citește `casa.md` din dosarul casei (stadiul pe etape, următorul pas, istoricul). Doar citire."""
    import dosar as dz
    ok, mesaj = dz.verifica(cale)
    if not ok:
        return mesaj
    s = dz.stadiul(mesaj)
    return s if s else f"Dosarul {mesaj} n-are încă casa.md; cadwork_dosar_nou îl pune."


@mcp.tool()
def cadwork_selecteaza(ce: str = "probleme", motiv: str = "") -> str:
    """Selectează în fereastra cadwork (și face zoom pe ele) piese alese de Claude — „degetul invers”: omul vede în model ce
    a găsit Claude. `ce` = „probleme” (toate ID-urile cu probleme din ultimele cadwork_verificari), numele unei constatări
    („duplicate”, „izolate”, „coliziuni”, „fara_material”, „fara_subgrupa”, „sectiuni_rare”, „prea_lungi”, „degenerate”) sau o
    listă de ID-uri „123, 456”. Nu schimbă modelul, dar schimbă selecția omului, deci urmează modul de permisiune (în
    «întreabă» omul confirmă în cadwork; în «citire» e refuzat)."""
    import verificari as vf
    ids = []
    etic = ce.strip().lower()
    if etic and all(t.strip().isdigit() for t in etic.replace(";", ",").split(",") if t.strip()):
        ids = [int(t) for t in etic.replace(";", ",").split(",") if t.strip()]
    else:
        if not os.path.exists(VERIFICARI_ULTIMELE):
            return "Nu există verificări salvate pe acest calculator; rulează întâi cadwork_verificari."
        u = json.load(open(VERIFICARI_ULTIMELE, encoding="utf-8"))
        if etic in ("", "probleme", "toate"):
            ids = u.get("probleme") or []
        else:
            ids = (u.get("pe_constatare") or {}).get(etic) or []
            if not ids:
                return f"Nicio piesă la «{ce}» în ultimele verificări ({u.get('cand')}, {u.get('model')}). Constatări cu piese: " \
                       + ", ".join((u.get("pe_constatare") or {}).keys())
        if not ids:
            return f"Ultimele verificări ({u.get('cand')}, {u.get('model')}) n-au găsit piese cu probleme; nimic de selectat."
    r = _cere_viu({"op": "ruleaza", "cod": vf.cod_selecteaza(ids),
                   "descriere": f"selectează în model {len(ids)} piese: {ce}" + (f" ({motiv})" if motiv else ""), "citire": False},
                  timeout=600)
    if r is None:
        return "Puntea vie nu răspunde; selecția se face doar prin puntea vie. " + PORNESTE_VIE
    if r.get("refuzat") or r.get("ocupat") or not r.get("ok"):
        return _formateaza_rulare(r)
    return f"Selectate în cadwork {r.get('raspuns', {}).get('selectate', '?')} piese ({ce}), cu zoom pe ele. " \
           f"Omul le vede acum evidențiate; selecția lui de dinainte a fost înlocuită." \
           + (f" [Da-ul omului în {r['dialog_s']} s]" if r.get("dialog_s") is not None else "")


@mcp.tool()
def cadwork_selectie() -> str:
    """Ce a selectat omul în fereastra cadwork 3D chiar acum: fișa fiecărui element activ (id, nume, categorie, material,
    secțiune, lungime, volum, grupă). Folosește-o când omul zice «asta», «grinda selectată», «ce am ales» — selecția e
    felul lui de a arăta cu degetul. ID-urile merg apoi în cadwork_ruleaza_cod; acolo lista e gata în variabila SELECTIE.
    Merge doar cu puntea vie (selecția e o stare de moment a ferestrei)."""
    r = _cere_viu({"op": "selectie"}, timeout=60)
    if r is None:
        return "Puntea vie nu răspunde, iar selecția se citește doar pe loc. " + PORNESTE_VIE
    if not r.get("ok"):
        return "Puntea vie a răspuns cu eroare: " + str(r.get("eroare"))
    return _formateaza_selectie(r)


@mcp.tool()
def cadwork_mod(mod: str = "", motiv: str = "") -> str:
    """Modul de permisiune al punții. Fără argumente: îl citește. Cu `mod` = citire / intreaba / liber: îl schimbă.
    Spre mai strict se schimbă pe loc. Spre mai liber se deschide un dialog Da/Nu în fereastra cadwork și omul decide
    (spune-i că trebuie să răspundă acolo); `motiv` apare în dialog, scurt, în limba omului. Cere «liber» doar dacă omul
    ți-a spus el că vrea să lucrezi fără întrebări."""
    mod = (mod or "").strip().lower()
    if not mod:
        r = _cere_viu({"op": "mod"}, timeout=10)
        m = r.get("mod") if r and r.get("ok") else _mod_din_fisier()
        sursa = "puntea vie" if r and r.get("ok") else "mod.txt (puntea vie nu răspunde)"
        return f"modul de permisiune: «{NUME_MOD[m]}» ({m}), din {sursa}. " + EXPLICA_MOD
    if mod not in MODURI:
        return f"mod necunoscut «{mod}»; modurile sunt: citire, intreaba, liber."
    r = _cere_viu({"op": "seteaza_mod", "mod": mod, "motiv": motiv}, timeout=600)
    if r is None:
        actual = _mod_din_fisier()
        if MODURI.index(mod) <= MODURI.index(actual):
            with open(MOD, "w", encoding="utf-8") as f:
                f.write(mod + "\n")
            return f"modul e acum «{NUME_MOD[mod]}» (scris în mod.txt; puntea vie nu răspunde)."
        return (f"Puntea vie nu răspunde, deci nu pot întreba omul în cadwork. Modul rămâne «{NUME_MOD[actual]}»; omul îl poate "
                f"schimba singur scriind «{mod}» în {MOD}.")
    if r.get("refuzat"):
        return _formateaza_rulare(r)
    if not r.get("ok"):
        return "Puntea vie a răspuns cu eroare: " + str(r.get("eroare"))
    if not r.get("schimbat"):
        return f"modul era deja «{NUME_MOD[r['mod']]}»."
    cum = f"acceptat de om în cadwork (dialog {r.get('dialog_s')} s)" if r.get("intrebat") else "pe loc, spre mai strict"
    return f"modul e acum «{NUME_MOD[r['mod']]}» — {cum}."


@mcp.tool()
def cadwork_ruleaza_cod(cod_python: str, descriere: str, doar_citire: bool = False) -> str:
    """Rulează cod Python în cadwork 3D (cwapi3d). În cod ai la îndemână: cadwork, ec (element_controller),
    ac (attribute_controller), gc (geometry_controller), mc (material_controller), uc (utility_controller) și dicționarul
    `raspuns` (ce pui în el vine înapoi, împreună cu tot ce scrii cu print) și lista SELECTIE (ID-urile elementelor
    selectate de om în fereastra cadwork în clipa rulării; goală dacă nu e nimic selectat). Unități: milimetri. Elementele create intră
    automat în undo (Ctrl+Z) și pot fi șterse cu cadwork_anuleaza_ultimul_job(). Rezultatul vine cu «ce s-a schimbat în model»
    (create / șterse / modificate, câmp cu câmp) — spune-i omului asta, nu doar «gata». Descrierea, scurtă, în limba omului.
    `doar_citire=True` pentru cod care NUMAI citește modelul (fără create / set / delete, fără import-uri în afara
    bibliotecii standard, fără open / exec / getattr): trece garda și rulează fără întrebare în orice mod; dacă totuși
    schimbă ceva, e anulat. Codul care modifică modelul urmează modul de permisiune: în «citire» e refuzat, în «intreaba»
    omul primește un dialog Da/Nu în fereastra cadwork (spune-i să răspundă acolo), în «liber» rulează pe loc.
    Cu puntea vie codul rulează pe loc; altfel e scris ca job pentru butonul punte_rdl (butonul = Da-ul omului).
    Înainte de orice cod care modifică modelul, spune omului în două rânduri ce urmează să faci."""
    r = _cere_viu({"op": "ruleaza", "cod": cod_python, "descriere": descriere, "citire": bool(doar_citire)}, timeout=900)
    if r is None:
        if _mod_din_fisier() == "citire" and not doar_citire:
            return (f"Modul e «doar citire» (mod.txt) și codul «{descriere}» nu e declarat doar_citire, deci nu-l scriu ca job. "
                    "Trimite-l cu doar_citire=True dacă doar citește, sau omul schimbă modul în mod.txt.")
        if descriere.strip().lower().startswith("inlocuieste:") and os.path.exists(JOB):
            os.remove(JOB)
            descriere = descriere.split(":", 1)[1].strip()
        return _scrie_job(cod_python, descriere)
    return _formateaza_rulare(r)


JOB_ANULEAZA = r'''
import json, os
cale = os.path.join(PUNTE, "ultimul_job.json")
u = json.load(open(cale, encoding="utf-8")) if os.path.exists(cale) else {}
in_model = set(ec.get_all_identifiable_element_ids())
ids = [i for i in u.get("create", []) if i in in_model]
if ids:
    ec.delete_elements_with_undo(ids)
print(f"sterse {len(ids)} elemente create de jobul «{u.get('descriere')}» din {u.get('cand')} (si ele pot fi readuse cu Ctrl+Z)")
raspuns["sterse"] = ids
'''


@mcp.tool()
def cadwork_anuleaza_ultimul_job() -> str:
    """Șterge (cu undo) elementele create de ultimul job rulat prin punte. Urmează modul de permisiune: în «citire» e
    refuzat, în «intreaba» omul confirmă în fereastra cadwork, în «liber» rulează pe loc. Fără puntea vie: prin buton."""
    r = _cere_viu({"op": "anuleaza"}, timeout=600)
    if r is None:
        if _mod_din_fisier() == "citire":
            return "Modul e «doar citire» (mod.txt): anularea șterge elemente, deci nu o scriu ca job. Omul schimbă modul în mod.txt."
        return _scrie_job(JOB_ANULEAZA, "anuleaza ultimul job")
    if r.get("refuzat"):
        return _formateaza_rulare(r)
    if not r.get("ok"):
        return "Puntea vie a răspuns cu eroare: " + str(r.get("eroare"))
    return f"Șterse {len(r.get('sterse', []))} elemente create de jobul «{r.get('job')}» din {r.get('cand')}: {r.get('sterse')}. Ctrl+Z în cadwork le readuce."


@mcp.tool()
def cadwork_rezultat() -> str:
    """Rezultatul ultimului job rulat prin butonul punte_rdl: starea, ce a scris jobul, dicționarul raspuns, create/șterse."""
    if os.path.exists(JOB):
        return "Jobul încă n-a fost rulat în cadwork (job.py e tot acolo). " + APASA
    if not os.path.exists(REZ_JSON):
        return "Niciun rezultat prin buton încă pe acest calculator."
    rez = json.load(open(REZ_JSON, encoding="utf-8"))
    return _formateaza_rulare(rez)


@mcp.tool()
def cadwork_opreste_puntea_vie() -> str:
    """Oprește pluginul rezident din cadwork (puntea vie). Omul o poate reporni cu un click pe punte_viu_rdl."""
    r = _cere_viu({"op": "stop"}, timeout=10)
    if r is None:
        return "Puntea vie nu era pornită."
    return "Puntea vie s-a oprit." if r.get("ok") else "Puntea vie a răspuns cu eroare: " + str(r.get("eroare"))


if __name__ == "__main__":
    mcp.run()
