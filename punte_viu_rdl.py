# -*- coding: utf-8 -*-
"""punte_viu_rdl — puntea rezidentă Claude ↔ cadwork 3D, v2: pluginul rămâne viu în cadwork după click, primește comenzi pe
un port local și le rulează după MODUL DE PERMISIUNE ales de om.
(Revista din Lemn / Hub-ul Lemnului, 5–6 nov 2026)

Cum merge:
  - La click, pluginul pornește (1) un fir care ascultă pe 127.0.0.1:53900 (sau 53901/53902) și (2) un cronometru Qt
    (QTimer, la 100 ms) pe firul principal al cadwork. Scriptul se termină imediat, dar obiectele rămân vii (referință în
    `builtins._punte_rdl`), iar cronometrul e ținut de bucla de evenimente a cadwork.
  - Firul de ascultare NU atinge cwapi3d: pune cererile într-o coadă. Cronometrul, pe firul principal, le scoate din coadă,
    le execută cu cwapi3d și pune răspunsul înapoi. Regula cadwork: apelurile API doar pe firul principal.

Modurile de permisiune (fișierul %USERPROFILE%\\cadwork-punte\\mod.txt; implicit «intreaba»):
  citire    — Claude doar citește modelul. Rulează cod numai dacă îl declară «citire» și codul trece garda (fără create / set /
              delete… pe controlere, fără import-uri în afara listei, fără exec / eval / getattr). După rulare se verifică
              amprenta modelului: dacă totuși s-a schimbat ceva, elementele create se șterg cu undo și omul e anunțat.
  intreaba  — orice cod care poate modifica modelul (și anularea ultimului job) deschide un dialog Da/Nu în cadwork, cu
              descrierea jobului; omul decide cu un click. Codul declarat «citire» trece prin garda de la «citire» și rulează fără
              întrebare.
  liber     — rulează pe loc; după fiecare job apare un rând în bara cadwork cu ce s-a făcut.
  Schimbarea modului: spre mai strict, oricând, pe loc (Claude se poate restrânge singur). Spre mai liber, DOAR cu Da-ul omului
  în dialogul din cadwork. Omul poate scrie oricând modul direct în mod.txt; pluginul îl citește la fiecare cerere.

Protocol: o conexiune = o cerere JSON pe o linie + un răspuns JSON pe o linie.
    {"op": "ping"}                                          → stare, mod, model, versiune
    {"op": "mod"}                                           → modul curent
    {"op": "seteaza_mod", "mod": "citire|intreaba|liber", "motiv": "..."}
    {"op": "lista"}                                         → piesele modelului (categorie, material, secțiune, lungime, volum)
    {"op": "ruleaza", "cod": "...", "descriere": "...", "citire": false}
                                                            → rulează cod Python cu cadwork, ec, ac, gc, mc, uc, raspuns; undo pe create
    {"op": "anuleaza"}                                      → șterge (cu undo) elementele create de ultimul job
    {"op": "stop"}                                          → oprește puntea
  Semn de viață: %USERPROFILE%\\cadwork-punte\\viu.txt (rescris la fiecare 10 s) + un rând în consola cadwork.
  Jurnal: punte_viu.log. Oprire fără Claude: creează fișierul stop.txt în același folder.
  Al doilea click, când puntea e deja vie, nu pornește a doua punte: doar spune portul și tick-ul.

Instalare: `userprofil_2026\\3d\\API.x64\\punte_viu_rdl\\punte_viu_rdl.py` → Window → User Plugins → punte_viu_rdl.
"""
import os
import io
import re
import sys
import json
import time
import queue
import socket
import builtins
import datetime
import threading
import traceback

import cadwork
import element_controller as ec
import attribute_controller as ac
import geometry_controller as gc
import material_controller as mc
import utility_controller as uc

try:
    from PyQt6.QtCore import QTimer
    QT_OK, QT_EROARE = True, ""
except Exception as _e:  # pragma: no cover
    QTimer, QT_OK, QT_EROARE = None, False, repr(_e)

VERSIUNE_PUNTE = "v4.4 (moduri + selecție + diff cu poziție + dialog.txt cât e dialogul deschis, 6 nov 2026)"
PUNTE = os.path.join(os.path.expanduser("~"), "cadwork-punte")
VIU = os.path.join(PUNTE, "viu.txt")
LOG = os.path.join(PUNTE, "punte_viu.log")
STOP = os.path.join(PUNTE, "stop.txt")
DIALOG = os.path.join(PUNTE, "dialog.txt")    # există doar cât e deschis un dialog Da/Nu
MOD = os.path.join(PUNTE, "mod.txt")
ULTIMUL = os.path.join(PUNTE, "ultimul_job.json")
ISTORIC = os.path.join(PUNTE, "istoric")
PORTURI = (53900, 53901, 53902)
INTERVAL_MS = 100
VIU_LA_SECUNDE = 10

MODURI = ("citire", "intreaba", "liber")          # de la cel mai strict la cel mai liber
MOD_IMPLICIT = "intreaba"
NUME_MOD = {"citire": "doar citire", "intreaba": "întreabă", "liber": "liber"}
AMPRENTA_MAX = 2000                                # peste atâtea elemente, amprenta = doar ID-urile

# garda pentru codul declarat «citire»: ce NU are voie să conțină
_GARDA_APELURI = re.compile(
    r"\b(ec|ac|gc|mc|uc|\w+_controller)\s*\."
    r"(create|set|delete|move|rotate|copy|cut|join|split|remove|add|apply|convert|subtract|unite|mirror|stretch|extend|"
    r"chamfer|solder|save|load|open|start|run|clear|reset|recreate|refresh|fill|glue|change|assign|attach|detach|invert|"
    r"activate|deactivate|hide|show|lock|unlock|auto|check_and|rebuild|dissolve|flip|pivot|push|pull|enable|disable|"
    r"execute|import|export)\w*\s*\(", re.IGNORECASE)
_GARDA_CUVINTE = re.compile(r"\b(exec|eval|getattr|setattr|delattr|__import__|importlib|compile|globals|locals|vars|open)\s*\(")
_GARDA_IMPORT = re.compile(r"^\s*(import|from)\s+([\w\.]+)", re.MULTILINE)
_IMPORT_VOIE = {"cadwork", "math", "json", "collections", "datetime", "itertools", "re", "statistics", "functools", "operator",
                "string", "decimal", "fractions", "textwrap", "csv", "io"}


def acum():
    return datetime.datetime.now()


def log(mesaj):
    try:
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"{acum():%Y-%m-%d %H:%M:%S} {mesaj}\n")
    except Exception:
        pass


# ---------------------------------------------------------------- modul de permisiune (fișier, citit la fiecare cerere)

def citeste_mod():
    try:
        with open(MOD, encoding="utf-8") as f:
            m = f.read().strip().lower()
        if m in MODURI:
            return m
        log(f"mod.txt are o valoare necunoscută «{m}», folosesc «{MOD_IMPLICIT}»")
    except FileNotFoundError:
        scrie_mod(MOD_IMPLICIT, "implicit, la prima pornire")
    except Exception as e:
        log(f"mod.txt necitibil: {e}")
    return MOD_IMPLICIT


def scrie_mod(mod, motiv=""):
    with open(MOD, "w", encoding="utf-8") as f:
        f.write(mod + "\n")
    log(f"mod → {mod} ({motiv})")


def garda_citire(cod):
    """Întoarce lista motivelor pentru care codul NU trece ca «citire» (goală = trece)."""
    motive = []
    for m in _GARDA_APELURI.finditer(cod):
        motive.append(f"apel care poate modifica: «{m.group(0).strip().rstrip('(').strip()}(»")
    for m in _GARDA_CUVINTE.finditer(cod):
        motive.append(f"nu e voie în modul citire: «{m.group(1)}(»")
    for m in _GARDA_IMPORT.finditer(cod):
        radacina = m.group(2).split(".")[0]
        if radacina not in _IMPORT_VOIE and not radacina.endswith("_controller"):
            motive.append(f"import în afara listei: «{m.group(2)}»")
    return motive


# ---------------------------------------------------------------- operațiile pe model (doar pe firul principal)

def categoria(eid):
    et = ac.get_element_type(eid)
    if et.is_rectangular_beam() or et.is_circular_beam():
        return "ecarisat"
    if et.is_panel():
        return "panouri"
    if et.is_connector_axis() or et.is_connector_node():
        return "feronerie"
    return "altele"


def selectie_ids():
    """ID-urile elementelor active (selectate de om) în fereastra cadwork."""
    try:
        return list(ec.get_active_identifiable_element_ids())
    except Exception:
        return []


def lista_piese(ids=None):
    """Fișele pieselor: tot modelul, sau doar `ids` (de ex. selecția omului)."""
    piese = []
    for eid in (ec.get_all_identifiable_element_ids() if ids is None else ids):
        try:
            material = ac.get_element_material_name(eid) or "(fara material)"
        except Exception:
            material = "(fara material)"
        piese.append({
            "id": eid, "nume": ac.get_name(eid) or "(fara nume)", "categorie": categoria(eid), "material": material,
            "grupa": ac.get_group(eid) or "", "subgrupa": ac.get_subgroup(eid) or "",
            "latime_mm": round(gc.get_width(eid)), "inaltime_mm": round(gc.get_height(eid)),
            "lungime_mm": round(gc.get_length(eid)), "volum_m3": round(gc.get_volume(eid) / 1e9, 5),
        })
    return piese


def amprenta_model():
    """Amprenta modelului: {id: (nume, material, lățime, înălțime, lungime, volum, P1 [x,y,z] mm)}; peste AMPRENTA_MAX doar ID-urile."""
    ids = ec.get_all_identifiable_element_ids()
    if len(ids) > AMPRENTA_MAX:
        return {eid: None for eid in ids}
    amp = {}
    for eid in ids:
        try:
            p1 = gc.get_p1(eid)
            amp[eid] = (ac.get_name(eid), ac.get_element_material_name(eid), round(gc.get_width(eid), 1),
                        round(gc.get_height(eid), 1), round(gc.get_length(eid), 1), round(gc.get_volume(eid)),
                        [round(p1.x), round(p1.y), round(p1.z)])
        except Exception:
            amp[eid] = ("?",)
    return amp


CAMPURI_AMPRENTA = ("nume", "material", "latime_mm", "inaltime_mm", "lungime_mm", "volum_mm3", "p1_mm")


def diff_amprente(inainte, dupa):
    """Ce s-a schimbat între două amprente: create / șterse / modificate (cu câmpurile vechi → noi). Cheile pot fi int sau str."""
    a = {int(k): v for k, v in inainte.items()}
    b = {int(k): v for k, v in dupa.items()}
    create = sorted(set(b) - set(a))
    sterse = sorted(set(a) - set(b))
    modificate = []
    for eid in sorted(set(a) & set(b)):
        va, vb = a[eid], b[eid]
        if va is None or vb is None:
            continue
        va, vb = list(va), list(vb)
        if va == vb:
            continue
        ce = {CAMPURI_AMPRENTA[i]: [va[i], vb[i]] for i in range(min(len(va), len(vb), len(CAMPURI_AMPRENTA))) if va[i] != vb[i]}
        modificate.append({"id": eid, "nume": vb[0] if vb else "?", "ce": ce})
    return {"create": create, "sterse": sterse, "modificate": modificate,
            "fise": {str(eid): list(b[eid]) if b[eid] else None for eid in create},
            "fise_sterse": {str(eid): list(a[eid]) if a[eid] else None for eid in sterse}}


def json_safe(obj):
    try:
        json.dumps(obj)
        return obj
    except Exception:
        return str(obj)


def ruleaza_cod(cod, descriere="", mod="liber", citire=False):
    """Rulează codul unui job pe firul principal, cu stdout prins; elementele create intră în undo și în ultimul_job.json.
    Cu citire=True se ia amprenta modelului înainte și după: orice schimbare se raportează, iar elementele create se șterg."""
    ns = {
        "__name__": "__punte__",
        "cadwork": cadwork, "ec": ec, "ac": ac, "gc": gc, "mc": mc, "uc": uc,
        "element_controller": ec, "attribute_controller": ac, "geometry_controller": gc,
        "material_controller": mc, "utility_controller": uc,
        "raspuns": {}, "PUNTE": PUNTE, "MOD": mod,
        "SELECTIE": selectie_ids(),
    }
    amp_inainte = amprenta_model()          # la orice job: diff-ul vine înapoi cu rezultatul
    inainte = set(amp_inainte)
    buf = io.StringIO()
    stdout_vechi = sys.stdout
    sys.stdout = buf
    eroare = ""
    t0 = time.perf_counter()
    try:
        exec(compile(cod, "<job punte>", "exec"), ns)
    except Exception:
        eroare = traceback.format_exc()
    finally:
        sys.stdout = stdout_vechi
    durata = round(time.perf_counter() - t0, 3)
    amp_dupa = amprenta_model()
    dupa = set(amp_dupa)
    create = sorted(dupa - inainte)
    sterse = sorted(inainte - dupa)
    schimbari = diff_amprente(amp_inainte, amp_dupa)
    incalcare = ""
    if citire:
        modificate = [m["id"] for m in schimbari["modificate"]]
        if create or sterse or modificate:
            incalcare = (f"codul declarat «citire» a schimbat modelul: create {create}, șterse {sterse}, modificate {modificate}; "
                         f"elementele create au fost șterse cu undo")
            if create:
                try:
                    ec.delete_elements_with_undo(create)
                except Exception:
                    pass
            log("ÎNCĂLCARE: " + incalcare)
            try:
                uc.print_message(f"Puntea RDL: jobul «{descriere}» era declarat doar citire, dar a schimbat modelul; anulat.", 1, 1)
            except Exception:
                pass
    elif create:
        try:
            ec.add_created_elements_to_undo(create)
        except Exception:
            pass
    rez = {
        "ok": not eroare and not incalcare, "stare": "eroare" if eroare else ("incalcare" if incalcare else "ok"),
        "descriere": descriere, "mod": mod, "citire": citire,
        "iesire": buf.getvalue(),
        "raspuns": {k: json_safe(v) for k, v in ns["raspuns"].items()} if isinstance(ns.get("raspuns"), dict) else json_safe(ns.get("raspuns")),
        "create": [] if incalcare else create, "sterse": sterse, "eroare": eroare or incalcare, "durata_s": durata,
        "schimbari": schimbari,
        "cand": acum().isoformat(timespec="seconds"), "model": uc.get_3d_file_name(),
    }
    try:
        os.makedirs(ISTORIC, exist_ok=True)
        stampila = acum().strftime("%Y%m%d-%H%M%S")
        with open(os.path.join(ISTORIC, f"{stampila}_viu_job.py"), "w", encoding="utf-8") as f:
            f.write(f"# punte viu [{mod}{', citire' if citire else ''}]: {descriere}\n" + cod)
        with open(os.path.join(ISTORIC, f"{stampila}_viu_rezultat.json"), "w", encoding="utf-8") as f:
            json.dump(rez, f, ensure_ascii=False, indent=1, default=str)
        if not citire:
            with open(ULTIMUL, "w", encoding="utf-8") as f:
                json.dump({"cand": rez["cand"], "descriere": descriere, "create": create, "sterse": sterse}, f, ensure_ascii=False)
    except Exception:
        log("istoric: " + traceback.format_exc())
    if mod == "liber" and not citire:
        try:
            uc.print_message(f"Claude [{NUME_MOD[mod]}]: «{descriere}» — {rez['stare']}, create {len(create)}, șterse {len(sterse)}", 1, 1)
        except Exception:
            pass
    return rez


def anuleaza_ultimul():
    u = {}
    if os.path.exists(ULTIMUL):
        with open(ULTIMUL, encoding="utf-8") as f:
            u = json.load(f)
    in_model = set(ec.get_all_identifiable_element_ids())
    ids = [i for i in u.get("create", []) if i in in_model]
    if ids:
        ec.delete_elements_with_undo(ids)
    return {"ok": True, "sterse": ids, "job": u.get("descriere"), "cand": u.get("cand")}


# ---------------------------------------------------------------- puntea

class Punte:
    def __init__(self):
        self.coada = queue.Queue()
        self.timer = None
        self.sock = None
        self.port = None
        self.fir = None
        self.pornit = acum()
        self.ticks = 0
        self.ultimul_viu = 0.0
        self.oprit = False
        self.ocupat = False          # un dialog e deschis pe firul principal → tick-urile nu intră peste el
        self.intrebare = ""          # textul dialogului deschis (firul de ascultare îl raportează la ping)
        self.ocupat_de = 0.0
        self.joburi = 0
        self.cereri = 0
        self.refuzate = 0

    # --- firul de ascultare (nu atinge cwapi3d)
    def porneste_socket(self):
        for p in PORTURI:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("127.0.0.1", p))
                s.listen(5)
                s.settimeout(1.0)
                self.sock, self.port = s, p
                return
            except OSError as e:
                log(f"portul {p} nu e liber: {e}")
        raise RuntimeError("niciun port liber din " + ", ".join(map(str, PORTURI)))

    def asculta(self):
        log(f"ascult pe 127.0.0.1:{self.port}")
        while not self.oprit:
            try:
                conn, _ = self.sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=self.serveste, args=(conn,), daemon=True).start()
        log("firul de ascultare s-a oprit")

    def serveste(self, conn):
        conn.settimeout(900)
        try:
            f = conn.makefile("rwb")
            linie = f.readline()
            if not linie:
                return
            try:
                cerere = json.loads(linie.decode("utf-8"))
            except Exception as e:
                raspuns = {"ok": False, "eroare": f"JSON invalid: {e}"}
            else:
                self.cereri += 1
                gata = threading.Event()
                holder = {}
                self.coada.put((cerere, gata, holder))
                # cât e dialogul deschis, firul principal ține GIL-ul în C++; cererea e luată tot de cronometru (tick), care
                # eliberează GIL-ul o clipă și răspunde «ocupată» fără cwapi3d
                if gata.wait(timeout=float(cerere.get("timeout", 600))):
                    raspuns = holder.get("raspuns", {"ok": False, "eroare": "fara raspuns de pe firul principal"})
                else:
                    holder["abandonat"] = True   # dacă omul răspunde la dialog după asta, jobul NU mai rulează
                    raspuns = {"ok": False, "eroare": "timeout: firul principal al cadwork nu a raspuns (dialog deschis? script lung?)"}
            try:
                f.write((json.dumps(raspuns, ensure_ascii=False, default=str) + "\n").encode("utf-8"))
                f.flush()
            except OSError as e:
                log(f"clientul plecase când a venit răspunsul la «{cerere.get('op')}» ({e.__class__.__name__})")
        except Exception:
            log("serveste: " + traceback.format_exc())
        finally:
            try:
                conn.close()
            except Exception:
                pass

    # --- cronometrul (firul principal)
    def porneste_timer(self):
        self.timer = QTimer()
        self.timer.setInterval(INTERVAL_MS)
        self.timer.timeout.connect(self.tick)
        self.timer.start()

    def tick(self):
        if self.ocupat:
            # cât e dialogul nativ deschis NU rulează niciun rând de Python (GIL-ul e în C++, bucla e nativă): nici firul de
            # ascultare, nici cronometrul. Semnalul pentru client e fișierul dialog.txt (scris în intreaba_omul, înainte de dialog).
            return
        self.ticks += 1
        try:
            if os.path.exists(STOP):
                self.opreste("stop.txt")
                return
            if time.time() - self.ultimul_viu >= VIU_LA_SECUNDE:
                self.scrie_viu()
            for _ in range(10):
                try:
                    cerere, gata, holder = self.coada.get_nowait()
                except queue.Empty:
                    break
                try:
                    holder["raspuns"] = self.executa(cerere, holder)
                except Exception:
                    holder["raspuns"] = {"ok": False, "eroare": traceback.format_exc()}
                finally:
                    gata.set()
        except Exception:
            log("tick: " + traceback.format_exc())

    def scrie_viu(self):
        self.ultimul_viu = time.time()
        try:
            n = len(ec.get_all_identifiable_element_ids())
            model = uc.get_3d_file_name()
        except Exception as e:
            n, model = -1, f"? ({e})"
        text = (f"viu: tick {self.ticks}, {acum():%H:%M:%S}, port {self.port}, mod {citeste_mod()}, pornit {self.pornit:%H:%M:%S}, "
                f"model {model}, {n} elemente, cereri {self.cereri}, joburi {self.joburi}, refuzate {self.refuzate}")
        try:
            with open(VIU, "w", encoding="utf-8") as f:
                f.write(text + "\n")
        except Exception:
            pass
        try:
            uc.print_to_console(text)
        except Exception:
            pass

    # --- dialogul Da/Nu în cadwork (firul principal, blocant)
    def intreaba_omul(self, intrebare, holder, implicit_da=False):
        """Pune întrebarea în cadwork. Întoarce True doar dacă omul a zis Da ȘI cererea nu a fost abandonată între timp."""
        self.intrebare = intrebare
        self.ocupat_de = time.time()
        self.ocupat = True
        t0 = time.perf_counter()
        try:
            with open(DIALOG, "w", encoding="utf-8") as f:
                json.dump({"intrebare": intrebare, "de_la": acum().isoformat(timespec="seconds"), "port": self.port}, f, ensure_ascii=False)
        except Exception:
            pass
        try:
            da = bool(uc.get_user_bool(intrebare, implicit_da))
        except Exception as e:
            log(f"dialogul nu a mers: {e}")
            da = False
        finally:
            self.ocupat = False
            self.intrebare = ""
            try:
                os.remove(DIALOG)
            except Exception:
                pass
        holder["dialog_s"] = round(time.perf_counter() - t0, 1)
        if holder.get("abandonat"):
            log(f"omul a răspuns {'Da' if da else 'Nu'} după ce Claude renunțase; nu rulez nimic")
            try:
                uc.print_message("Puntea RDL: răspunsul a venit prea târziu, Claude renunțase; nimic nu s-a rulat.", 1, 1)
            except Exception:
                pass
            return False
        return da

    def refuz(self, mesaj, holder=None):
        self.refuzate += 1
        log("refuzat: " + mesaj)
        r = {"ok": False, "refuzat": True, "mod": citeste_mod(), "eroare": mesaj}
        if holder and "dialog_s" in holder:
            r["dialog_s"] = holder["dialog_s"]
        return r

    def executa(self, cerere, holder):
        op = cerere.get("op")
        mod = citeste_mod()
        if op == "ping":
            return {"ok": True, "tick": self.ticks, "port": self.port, "mod": mod, "versiune_punte": VERSIUNE_PUNTE,
                    "model": uc.get_3d_file_name(), "elemente": len(ec.get_all_identifiable_element_ids()),
                    "selectate": len(selectie_ids()),
                    "pornit": self.pornit.isoformat(timespec="seconds"), "joburi": self.joburi, "refuzate": self.refuzate,
                    "versiune_cadwork": f"{uc.get_3d_version()} build {uc.get_3d_build()}"}
        if op == "mod":
            return {"ok": True, "mod": mod, "nume": NUME_MOD[mod], "fisier": MOD}
        if op == "seteaza_mod":
            nou = str(cerere.get("mod", "")).strip().lower()
            motiv = str(cerere.get("motiv", "")).strip()
            if nou not in MODURI:
                return {"ok": False, "eroare": f"mod necunoscut «{nou}»; modurile sunt: {', '.join(MODURI)}", "mod": mod}
            if nou == mod:
                return {"ok": True, "mod": mod, "schimbat": False}
            if MODURI.index(nou) < MODURI.index(mod):          # spre mai strict: pe loc
                scrie_mod(nou, f"cerut de Claude, mai strict: {motiv}")
                return {"ok": True, "mod": nou, "schimbat": True, "intrebat": False}
            intrebare = (f"Claude cere modul «{NUME_MOD[nou]}» (acum: «{NUME_MOD[mod]}»). "
                         f"{('Motiv: ' + motiv + '. ') if motiv else ''}Accepți?")
            if self.intreaba_omul(intrebare, holder, implicit_da=False):
                scrie_mod(nou, f"acceptat de om în cadwork: {motiv}")
                return {"ok": True, "mod": nou, "schimbat": True, "intrebat": True, "dialog_s": holder.get("dialog_s")}
            return self.refuz(f"omul NU a acceptat trecerea la modul «{NUME_MOD[nou]}»; rămâne «{NUME_MOD[mod]}»", holder)
        if op == "lista":
            return {"ok": True, "piese": lista_piese(), "model": uc.get_3d_file_name(), "mod": mod,
                    "selectate": selectie_ids()}
        if op == "amprenta":
            amp = amprenta_model()
            return {"ok": True, "amprenta": {str(k): (list(v) if v else None) for k, v in amp.items()},
                    "model": uc.get_3d_file_name(), "cand": acum().isoformat(timespec="seconds"), "mod": mod,
                    "campuri": list(CAMPURI_AMPRENTA), "elemente": len(amp)}
        if op == "diff":
            veche = cerere.get("amprenta") or {}
            amp = amprenta_model()
            d = diff_amprente(veche, amp)
            return {"ok": True, "model": uc.get_3d_file_name(), "cand": acum().isoformat(timespec="seconds"), "mod": mod,
                    "elemente": len(amp), "elemente_atunci": len(veche), **d}
        if op == "selectie":
            ids = selectie_ids()
            return {"ok": True, "ids": ids, "piese": lista_piese(ids), "model": uc.get_3d_file_name(), "mod": mod,
                    "elemente": len(ec.get_all_identifiable_element_ids())}
        if op == "ruleaza":
            cod = cerere.get("cod", "")
            descriere = cerere.get("descriere", "") or "(fara descriere)"
            citire = bool(cerere.get("citire", False))
            if citire:
                motive = garda_citire(cod)
                if motive:
                    return self.refuz("codul e declarat «citire», dar nu trece garda: " + "; ".join(motive) +
                                      ". Scoate apelurile care modifică sau trimite-l fără «citire» (în modul întreabă/liber).")
            elif mod == "citire":
                return self.refuz(f"modul e «doar citire»: codul «{descriere}» nu e declarat citire, deci nu rulează. "
                                  "Trimite-l cu citire=True dacă doar citește, sau cere omului alt mod (dialog în cadwork).")
            elif mod == "intreaba":
                n = len(cod.splitlines())
                intrebare = f"Claude vrea să ruleze în model: «{descriere}» ({n} linii de cod). Rulez?"
                if not self.intreaba_omul(intrebare, holder, implicit_da=False):
                    if holder.get("abandonat"):
                        return self.refuz(f"răspunsul omului la «{descriere}» a venit după ce Claude renunțase; nimic rulat", holder)
                    return self.refuz(f"omul a zis NU la «{descriere}»", holder)
            rez = ruleaza_cod(cod, descriere, mod=mod, citire=citire)
            if "dialog_s" in holder:
                rez["dialog_s"] = holder["dialog_s"]
            self.joburi += 1
            return rez
        if op == "anuleaza":
            if mod == "citire":
                return self.refuz("modul e «doar citire»: anularea modifică modelul (șterge elemente); cere omului alt mod")
            if mod == "intreaba":
                u = {}
                try:
                    with open(ULTIMUL, encoding="utf-8") as f:
                        u = json.load(f)
                except Exception:
                    pass
                intrebare = (f"Claude vrea să șteargă (cu undo) cele {len(u.get('create', []))} elemente create de jobul "
                             f"«{u.get('descriere', '?')}». Șterg?")
                if not self.intreaba_omul(intrebare, holder, implicit_da=False):
                    if holder.get("abandonat"):
                        return self.refuz("răspunsul omului la anulare a venit după ce Claude renunțase; nimic anulat", holder)
                    return self.refuz("omul a zis NU la anularea ultimului job", holder)
            r = anuleaza_ultimul()
            r["mod"] = mod
            return r
        if op == "stop":
            # răspunsul pleacă întâi; oprirea vine 300 ms mai târziu, ca socketul să nu se închidă sub client
            QTimer.singleShot(300, lambda: self.opreste("cerere stop"))
            return {"ok": True, "oprit": True}
        return {"ok": False, "eroare": f"op necunoscut: {op}"}

    def opreste(self, motiv):
        self.oprit = True
        try:
            self.timer.stop()
        except Exception:
            pass
        try:
            self.sock.close()
        except Exception:
            pass
        try:
            if os.path.exists(STOP):
                os.remove(STOP)
        except Exception:
            pass
        log(f"oprit: {motiv} (tick {self.ticks}, cereri {self.cereri}, joburi {self.joburi}, refuzate {self.refuzate})")
        try:
            with open(VIU, "w", encoding="utf-8") as f:
                f.write(f"oprit: {motiv}, {acum():%H:%M:%S}\n")
            uc.print_message(f"Puntea RDL s-a oprit ({motiv})", 1, 1)
        except Exception:
            pass


def main():
    os.makedirs(PUNTE, exist_ok=True)
    try:
        os.remove(DIALOG)        # un dialog.txt rămas de la o închidere bruscă nu trebuie să mintă clientul
    except Exception:
        pass
    if not QT_OK:
        log("PyQt6 lipseste: " + QT_EROARE)
        uc.print_message("Puntea RDL: PyQt6 lipseste din Python-ul cadwork: " + QT_EROARE, 1, 1)
        return
    veche = getattr(builtins, "_punte_rdl", None)
    if veche is not None and not getattr(veche, "oprit", True):
        uc.print_message(f"Puntea RDL e deja vie pe portul {veche.port} (tick {veche.ticks}, pornita {veche.pornit:%H:%M:%S}, "
                         f"mod {citeste_mod()})", 1, 1)
        return
    p = Punte()
    try:
        p.porneste_socket()
        p.fir = threading.Thread(target=p.asculta, name="punte-rdl-ascultare", daemon=True)
        p.fir.start()
        p.porneste_timer()
    except Exception:
        log("pornire: " + traceback.format_exc())
        uc.print_message("Puntea RDL: nu a pornit, vezi punte_viu.log", 1, 1)
        return
    builtins._punte_rdl = p
    mod = citeste_mod()
    log(f"pornita {VERSIUNE_PUNTE}: port {p.port}, mod {mod}, PyQt6 OK, python {sys.version.split()[0]}")
    p.scrie_viu()
    uc.print_message(f"Puntea RDL e vie pe portul {p.port}, modul «{NUME_MOD[mod]}» (mod.txt). Oprire: stop.txt în cadwork-punte.", 1, 1)


main()
