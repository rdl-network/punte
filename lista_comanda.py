# -*- coding: utf-8 -*-
"""lista_comanda — din piesele modelului (lista punții) → lista de materiale GATA DE COMANDĂ (prima facilitate a nișei, 6 nov 2026).

Ce face, pe scurt: grupează lemnul ecarisat pe sortimente (material + secțiune), apoi croiește fiecare sortiment pe lungimi
comerciale (implicit 3 / 4 / 5 / 6 / 8 / 10 / 12 / 13 m) cu un adaos de tăiere pe piesă, și spune câte bare de fiecare lungime
trebuie comandate, cât e net, cât e comandat și cât e pierderea. Panourile ies pe material + grosime, în m². Restul (goluri,
învelișuri, secțiuni ajutătoare) nu intră în cantități, dar e numărat.

Funcții pure (fără cadwork): calculeaza(piese, …) → dict; formateaza(rez) → text; salveaza(rez, folder) → (md, csv).
Piesele au forma dată de puntea vie (op `lista` / `selectie`): id, nume, categorie, material, grupa, subgrupa,
latime_mm, inaltime_mm, lungime_mm, volum_m3.
"""
import os
import csv
import datetime
from collections import Counter, OrderedDict, defaultdict

LUNGIMI_IMPLICITE = (3000, 4000, 5000, 6000, 8000, 10000, 12000, 13000)
ADAOS_IMPLICIT = 50          # mm pe piesă, pentru tăiere și capete


def _m(mm):
    return f"{mm / 1000:.2f}".replace(".", ",")


def croieste(lungimi_piese, lungimi_comerciale, adaos_mm):
    """Croiala unui sortiment: piesele (mm) în bare comerciale. First-fit-decreasing în bara cea mai lungă, apoi fiecare bară
    e strânsă la cea mai scurtă lungime comercială care încape ce s-a pus în ea. Întoarce (bare: Counter{lungime: buc},
    pierdere_mm, prea_lungi: [lungimi])."""
    comerciale = sorted(set(int(x) for x in lungimi_comerciale if x > 0))
    if not comerciale:
        return Counter(), 0, list(lungimi_piese)
    maxim = comerciale[-1]
    nevoie = sorted((int(l) + adaos_mm for l in lungimi_piese), reverse=True)
    prea_lungi = [n - adaos_mm for n in nevoie if n > maxim]
    nevoie = [n for n in nevoie if n <= maxim]
    bare = []                                   # fiecare bară = [spațiu folosit]
    for n in nevoie:
        for b in bare:
            if b[0] + n <= maxim:
                b[0] += n
                break
        else:
            bare.append([n])
    rezultat = Counter()
    pierdere = 0
    for b in bare:
        folosit = b[0]
        lung = next(c for c in comerciale if c >= folosit)
        rezultat[lung] += 1
        pierdere += lung - folosit
    return rezultat, pierdere, prea_lungi


def calculeaza(piese, lungimi_comerciale=LUNGIMI_IMPLICITE, adaos_mm=ADAOS_IMPLICIT, subgrupe=None, doar_ids=None,
               subgrupe_exacte=None):
    """Lista de comandă. `subgrupe` = listă de fragmente (ex. ["EG", "gg01"]) → doar piesele din acele subgrupe (pereți);
    `doar_ids` = doar piesele cu aceste ID-uri (ex. selecția omului); `subgrupe_exacte` = și toate piesele din aceste subgrupe
    (numele exact) — pentru când omul a selectat un perete ca obiect și vrea piesele lui."""
    sel = list(piese)
    if doar_ids is not None or subgrupe_exacte:
        ids = set(int(i) for i in (doar_ids or []))
        exacte = set(subgrupe_exacte or [])
        sel = [p for p in sel if int(p["id"]) in ids or (p.get("subgrupa") or "") in exacte]
    if subgrupe:
        frag = [s.lower() for s in subgrupe if s]
        sel = [p for p in sel if any(f in (p.get("subgrupa") or "").lower() or f in (p.get("grupa") or "").lower() for f in frag)]
    sortimente = OrderedDict()
    for p in sel:
        if p["categorie"] != "ecarisat":
            continue
        w, h = sorted((int(round(p["latime_mm"])), int(round(p["inaltime_mm"]))))
        cheie = (p["material"] or "(fără material)", w, h)
        s = sortimente.setdefault(cheie, {"material": cheie[0], "sectiune": f"{w} x {h}", "buc": 0, "lungimi": [],
                                          "net_mm": 0, "net_m3": 0.0, "nume": Counter(), "subgrupe": Counter()})
        s["buc"] += 1
        s["lungimi"].append(int(round(p["lungime_mm"])))
        s["net_mm"] += int(round(p["lungime_mm"]))
        s["net_m3"] += float(p["volum_m3"])
        s["nume"][p.get("nume") or "(fără nume)"] += 1
        s["subgrupe"][p.get("subgrupa") or ""] += 1
    rezultat = []
    tot_net_m3 = tot_com_m3 = tot_lung_m3 = 0.0
    for (mat, w, h), s in sorted(sortimente.items(), key=lambda kv: (kv[0][0], -kv[1]["net_m3"])):
        bare, pierdere, prea_lungi = croieste(s["lungimi"], lungimi_comerciale, adaos_mm)
        com_mm = sum(l * n for l, n in bare.items())
        com_m3 = com_mm / 1000 * (w / 1000) * (h / 1000)
        tot_lung_m3 += s["net_mm"] / 1000 * (w / 1000) * (h / 1000)     # lungimea netă × secțiunea plină (fără îmbinări)
        lung = Counter(s["lungimi"])
        rezultat.append({
            "material": mat, "sectiune": s["sectiune"], "latime_mm": w, "inaltime_mm": h, "buc": s["buc"],
            "net_m": round(s["net_mm"] / 1000, 2), "net_m3": round(s["net_m3"], 4),
            "lungimi_piese": OrderedDict(sorted(lung.items())),
            "bare": OrderedDict(sorted(bare.items())), "bare_total": sum(bare.values()),
            "comanda_m": round(com_mm / 1000, 2), "comanda_m3": round(com_m3, 4),
            "pierdere_pct": round(100 * (1 - (s["net_mm"] / com_mm)), 1) if com_mm else 0.0,
            "prea_lungi": prea_lungi, "nume": dict(s["nume"].most_common(3)), "subgrupe": len(s["subgrupe"]),
        })
        tot_net_m3 += s["net_m3"]
        tot_com_m3 += com_m3
    panouri = OrderedDict()
    for p in sel:
        if p["categorie"] != "panouri":
            continue
        gros = int(round(min(p["latime_mm"], p["inaltime_mm"], p["lungime_mm"])))
        cheie = (p["material"] or "(fără material)", gros)
        q = panouri.setdefault(cheie, {"material": cheie[0], "grosime_mm": gros, "buc": 0, "m2": 0.0, "m3": 0.0, "nume": Counter()})
        dims = sorted((p["latime_mm"], p["inaltime_mm"], p["lungime_mm"]))
        q["buc"] += 1
        q["m2"] += dims[1] * dims[2] / 1e6
        q["m3"] += float(p["volum_m3"])
        q["nume"][p.get("nume") or "(fără nume)"] += 1
    altele = Counter((p.get("nume") or "(fără nume)") for p in sel if p["categorie"] not in ("ecarisat", "panouri"))
    return {
        "cand": datetime.datetime.now().isoformat(timespec="minutes"),
        "piese_in_calcul": len(sel), "piese_total": len(piese),
        "lungimi_comerciale": [int(x) for x in lungimi_comerciale], "adaos_mm": adaos_mm,
        "filtru": {"subgrupe": subgrupe or [], "doar_ids": None if doar_ids is None else len(list(doar_ids)),
                   "pereti": sorted(subgrupe_exacte or [])},
        "ecarisat": rezultat, "ecarisat_net_m3": round(tot_net_m3, 3), "ecarisat_comanda_m3": round(tot_com_m3, 3),
        "ecarisat_lungimi_m3": round(tot_lung_m3, 3),
        "ecarisat_pierdere_pct": round(100 * (1 - tot_lung_m3 / tot_com_m3), 1) if tot_com_m3 else 0.0,
        "panouri": [{**q, "m2": round(q["m2"], 2), "m3": round(q["m3"], 4), "nume": dict(q["nume"].most_common(3))}
                    for q in panouri.values()],
        "altele": dict(altele.most_common(12)), "altele_total": sum(altele.values()),
    }


def formateaza(rez, model="", scurt=False):
    """Raportul de comandă, text. `scurt` = doar tabelul de comandă (fără lungimile pieselor)."""
    f = rez.get("filtru") or {}
    filtru = ""
    if f.get("subgrupe"):
        filtru = f" — doar subgrupele {', '.join(f['subgrupe'])}"
    elif f.get("pereti"):
        filtru = f" — doar selecția: {'peretele' if len(f['pereti']) == 1 else 'pereții'} {', '.join(f['pereti'])}" \
                 + (f" + {f['doar_ids']} piese alese" if f.get("doar_ids") else "")
    elif f.get("doar_ids") is not None:
        filtru = f" — doar selecția ({f['doar_ids']} {'piesă' if f['doar_ids'] == 1 else 'piese'})"
    linii = [f"LISTA DE COMANDĂ — {model or 'modelul deschis'}{filtru}",
             f"{rez['piese_in_calcul']} piese în calcul din {rez['piese_total']}; lungimi comerciale "
             f"{' / '.join(_m(l) for l in rez['lungimi_comerciale'])} m; adaos de tăiere {rez['adaos_mm']} mm/piesă; {rez['cand']}",
             ""]
    linii.append("LEMN ECARISAT ȘI ALTE BARE (de comandat pe lungimi comerciale):")
    linii.append(f"  {'material':<14} {'secțiune':<10} {'buc':>5} {'net m':>8} {'net m3':>8}  {'bare de comandat':<42} {'com. m3':>8} {'pierd.':>6}")
    for s in rez["ecarisat"]:
        bare = ", ".join(f"{n} × {_m(l)} m" for l, n in s["bare"].items()) or "—"
        linii.append(f"  {s['material'][:14]:<14} {s['sectiune']:<10} {s['buc']:>5} {s['net_m']:>8.2f} {s['net_m3']:>8.3f}  {bare:<42} "
                     f"{s['comanda_m3']:>8.3f} {s['pierdere_pct']:>5.1f}%")
        if s["prea_lungi"]:
            linii.append(f"      ! {len(s['prea_lungi'])} piese peste lungimea comercială maximă: {', '.join(_m(l) + ' m' for l in s['prea_lungi'][:6])}")
        if not scurt:
            lung = ", ".join(f"{_m(l)} ×{n}" for l, n in s["lungimi_piese"].items())
            nume = ", ".join(f"{k} ({v})" for k, v in s["nume"].items())
            linii.append(f"      piese: {lung}")
            linii.append(f"      ce sunt: {nume}; în {s['subgrupe']} subgrupe")
    linii.append(f"  TOTAL: de comandat {rez['ecarisat_comanda_m3']:.3f} m3 pe bare comerciale; lungimi nete × secțiune "
                 f"{rez['ecarisat_lungimi_m3']:.3f} m3 (pierdere la croit {rez['ecarisat_pierdere_pct']:.1f}%); "
                 f"volum net din model, cu îmbinările scăzute: {rez['ecarisat_net_m3']:.3f} m3")
    linii.append("")
    linii.append("PANOURI (de comandat în m², fără adaos):")
    if rez["panouri"]:
        for q in rez["panouri"]:
            nume = ", ".join(f"{k} ({v})" for k, v in q["nume"].items())
            linii.append(f"  {q['material'][:14]:<14} gros. {q['grosime_mm']:>4} mm {q['buc']:>5} buc {q['m2']:>8.2f} m2 {q['m3']:>8.3f} m3   {nume}")
    else:
        linii.append("  (niciun panou)")
    linii.append("")
    alt = ", ".join(f"{k} ({v})" for k, v in rez["altele"].items())
    linii.append(f"NU INTRĂ ÎN CANTITĂȚI ({rez['altele_total']} obiecte: goluri, învelișuri, ajutătoare): {alt or '—'}")
    linii.append("")
    linii.append("Cantitățile nete sunt din model (cu îmbinările scăzute). Croiala e o estimare first-fit pe lungimile comerciale date;"
                 " depozitul poate avea alte lungimi — schimbă lista și recalculează.")
    return "\n".join(linii)


def salveaza(rez, folder, model="", text=None):
    """Scrie raportul (.md) și tabelul de comandă (.csv, cu ; pentru Excel RO) în `folder`; întoarce (cale_md, cale_csv)."""
    os.makedirs(folder, exist_ok=True)
    baza = "".join(c if c.isalnum() or c in "-_" else "_" for c in (model or "model").rsplit(".", 1)[0])[:40]
    stampila = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    cale_md = os.path.join(folder, f"{baza}-comanda-{stampila}.md")
    cale_csv = os.path.join(folder, f"{baza}-comanda-{stampila}.csv")
    with open(cale_md, "w", encoding="utf-8") as f:
        f.write("```\n" + (text or formateaza(rez, model)) + "\n```\n")
    with open(cale_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["tip", "material", "sectiune / grosime", "lungime comerciala m", "bucati", "net m", "net m3", "comanda m3", "pierdere %"])
        for s in rez["ecarisat"]:
            for l, n in s["bare"].items():
                w.writerow(["ecarisat", s["material"], s["sectiune"], _m(l), n, "", "", "", ""])
            w.writerow(["ecarisat TOTAL", s["material"], s["sectiune"], "", s["buc"], f"{s['net_m']:.2f}".replace(".", ","),
                        f"{s['net_m3']:.3f}".replace(".", ","), f"{s['comanda_m3']:.3f}".replace(".", ","), f"{s['pierdere_pct']:.1f}".replace(".", ",")])
        for q in rez["panouri"]:
            w.writerow(["panou", q["material"], q["grosime_mm"], "", q["buc"], "", f"{q['m3']:.3f}".replace(".", ","), f"{q['m2']:.2f} m2".replace(".", ","), ""])
    return cale_md, cale_csv


def parseaza_lungimi(text):
    """„3,4,5,6” sau „3 4 5 6” sau „3000 4000” → mm."""
    if not text:
        return LUNGIMI_IMPLICITE
    out = []
    for tok in str(text).replace(";", ",").replace(" ", ",").split(","):
        tok = tok.strip().replace("m", "")
        if not tok:
            continue
        v = float(tok.replace(",", "."))
        out.append(int(round(v * 1000)) if v < 100 else int(round(v)))
    return tuple(sorted(set(out))) or LUNGIMI_IMPLICITE
