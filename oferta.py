# -*- coding: utf-8 -*-
"""oferta — oferta de casă din lista de comandă × prețuri (sarcina 1 din program, 6 nov 2026).

Intrarea: rezultatul `lista_comanda.calculeaza(...)` + un fișier de prețuri (CSV cu `;`, vezi `preturi-referinta.csv`):
  tip (ecarisat / panou / transport / manopera / marja / tva); material; unitate; pret_lei_fara_tva; sursa; data; nota.
Prețul lemnului ecarisat e pe m3 DE COMANDAT (bare comerciale, nu net); panourile pe m2 (grosimea se scalează din 120 mm dacă
rândul e „m2/120mm”). Un preț 0 = DE COMPLETAT: rândul apare în ofertă, dar nu intră în total, iar oferta o spune în clar.
Funcții pure: incarca_preturi(cale) → dict; calculeaza_oferta(rez, preturi) → dict; formateaza_oferta(of, …) → text.
"""
import os
import csv
import datetime


def incarca_preturi(cale):
    """CSV → {"ecarisat": {material: rând}, "panou": {material: rând}, "transport": rând, "manopera": rând, "marja": rând, "tva": rând}."""
    pr = {"ecarisat": {}, "panou": {}, "transport": None, "manopera": None, "marja": None, "tva": None, "cale": cale}
    with open(cale, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f, delimiter=";"):
            tip = (r.get("tip") or "").strip().lower()
            try:
                r["pret"] = float((r.get("pret_lei_fara_tva") or "0").replace(",", "."))
            except ValueError:
                r["pret"] = 0.0
            mat = (r.get("material") or "").strip()
            if tip in ("ecarisat", "panou"):
                pr[tip][mat.lower()] = r
            elif tip in ("transport", "manopera", "marja", "tva"):
                pr[tip] = r
    return pr


def _pret_material(pr, tip, material, grosime_mm=None):
    """Rândul de preț pentru un material: potrivire exactă, apoi pe prefix/fragment; pentru panouri și regula pe grosime."""
    m = (material or "").lower().strip()
    tabel = pr[tip]
    if tip == "panou" and grosime_mm:
        r = tabel.get(f"{m} {grosime_mm}")
        if r:
            return r, r["pret"]
    r = tabel.get(m)
    if r is None:
        for k, v in tabel.items():
            if k and (m.startswith(k) or k in m):
                r = v
                break
    if r is None:
        return None, 0.0
    pret = r["pret"]
    if tip == "panou" and grosime_mm and (r.get("unitate") or "").replace(" ", "").lower() == "m2/120mm":
        pret = pret * grosime_mm / 120.0
    return r, pret


def calculeaza_oferta(rez, pr):
    linii = []
    lipsa = []
    materiale = 0.0
    for s in rez["ecarisat"]:
        r, pret = _pret_material(pr, "ecarisat", s["material"])
        val = s["comanda_m3"] * pret
        linii.append({"capitol": "lemn", "ce": f"{s['material']} {s['sectiune']} mm", "cantitate": s["comanda_m3"], "unitate": "m3",
                      "bare": ", ".join(f"{n} × {l / 1000:g} m" for l, n in s["bare"].items()), "pret": pret, "valoare": val,
                      "sursa": (r or {}).get("sursa", ""), "data": (r or {}).get("data", ""), "lipsa": pret <= 0})
        if pret <= 0:
            lipsa.append(s["material"])
        materiale += val
    for q in rez["panouri"]:
        r, pret = _pret_material(pr, "panou", q["material"], q["grosime_mm"])
        val = q["m2"] * pret
        linii.append({"capitol": "panouri", "ce": f"{q['material']} {q['grosime_mm']} mm", "cantitate": q["m2"], "unitate": "m2",
                      "bare": f"{q['buc']} buc", "pret": pret, "valoare": val,
                      "sursa": (r or {}).get("sursa", ""), "data": (r or {}).get("data", ""), "lipsa": pret <= 0})
        if pret <= 0:
            lipsa.append(f"{q['material']} {q['grosime_mm']} mm")
        materiale += val
    transport_pct = (pr["transport"] or {}).get("pret", 0.0) if pr["transport"] else 0.0
    transport = materiale * transport_pct / 100
    m3_structura = rez["ecarisat_comanda_m3"]
    manopera_unit = (pr["manopera"] or {}).get("pret", 0.0) if pr["manopera"] else 0.0
    manopera = m3_structura * manopera_unit
    baza = materiale + transport + manopera
    marja_pct = (pr["marja"] or {}).get("pret", 0.0) if pr["marja"] else 0.0
    marja = baza * marja_pct / 100
    fara_tva = baza + marja
    tva_pct = (pr["tva"] or {}).get("pret", 21.0) if pr["tva"] else 21.0
    tva = fara_tva * tva_pct / 100
    return {"linii": linii, "materiale": materiale, "transport": transport, "transport_pct": transport_pct,
            "manopera": manopera, "manopera_unit": manopera_unit, "m3_structura": m3_structura,
            "marja": marja, "marja_pct": marja_pct, "fara_tva": fara_tva, "tva": tva, "tva_pct": tva_pct, "total": fara_tva + tva,
            "lipsa": sorted(set(lipsa)), "preturi_cale": pr.get("cale", ""),
            "cand": datetime.datetime.now().strftime("%d.%m.%Y")}


def _lei(v):
    s = f"{v:,.0f}".replace(",", ".")
    return s + " lei"


def formateaza_oferta(of, rez, model="", client="", obiect="", firma=""):
    f = rez.get("filtru") or {}
    ce = obiect or ("structura de lemn — " + (model or "modelul deschis"))
    if f.get("pereti"):
        ce += f" (doar {'peretele' if len(f['pereti']) == 1 else 'pereții'} {', '.join(f['pereti'])})"
    elif f.get("subgrupe"):
        ce += f" (doar subgrupele {', '.join(f['subgrupe'])})"
    L = [f"OFERTĂ DE PREȚ — {ce}", f"{firma + ' — ' if firma else ''}{of['cand']}" + (f" — pentru {client}" if client else ""), ""]
    L.append("Cantitățile sunt cele de comandat (bare comerciale "
             + " / ".join(f"{l / 1000:g}" for l in rez["lungimi_comerciale"]) + " m, adaos de tăiere "
             + f"{rez['adaos_mm']} mm/piesă), scoase din modelul cadwork; prețurile sunt fără TVA.")
    L.append("")
    L.append(f"  {'nr':>3}  {'ce':<34} {'cantitate':>12}  {'preț unitar':>12}  {'valoare':>14}")
    n = 0
    for cap, titlu in (("lemn", "LEMN DE STRUCTURĂ"), ("panouri", "PANOURI ȘI PLĂCI")):
        randuri = [l for l in of["linii"] if l["capitol"] == cap]
        if not randuri:
            continue
        L.append(f"  {titlu}")
        for l in randuri:
            n += 1
            cant = f"{l['cantitate']:.3f} {l['unitate']}" if l["unitate"] == "m3" else f"{l['cantitate']:.2f} {l['unitate']}"
            pret = f"{l['pret']:,.0f} lei/{l['unitate']}".replace(",", ".") if not l["lipsa"] else "DE COMPLETAT"
            val = _lei(l["valoare"]) if not l["lipsa"] else "—"
            L.append(f"  {n:>3}  {l['ce']:<34} {cant:>12}  {pret:>12}  {val:>14}")
            L.append(f"       {l['bare']}")
    L.append("")
    L.append(f"  {'Materiale':<52} {_lei(of['materiale']):>14}")
    L.append(f"  {'Transport (' + f'{of['transport_pct']:g}' + ' % din materiale)':<52} {_lei(of['transport']):>14}")
    man = f"Manoperă structură ({of['m3_structura']:.3f} m3 × {of['manopera_unit']:,.0f} lei/m3)".replace(",", ".")
    L.append(f"  {man:<52} {_lei(of['manopera']) if of['manopera_unit'] > 0 else 'DE COMPLETAT':>14}")
    L.append(f"  {'Regie și profit (' + f'{of['marja_pct']:g}' + ' %)':<52} {_lei(of['marja']):>14}")
    L.append(f"  {'TOTAL fără TVA':<52} {_lei(of['fara_tva']):>14}")
    L.append(f"  {'TVA ' + f'{of['tva_pct']:g}' + ' %':<52} {_lei(of['tva']):>14}")
    L.append(f"  {'TOTAL DE PLATĂ':<52} {_lei(of['total']):>14}")
    L.append("")
    note = []
    if of["lipsa"]:
        note.append("Fără preț (NU intră în total): " + ", ".join(of["lipsa"]) + ". Completează-le în fișierul de prețuri și regenerează.")
    if of["manopera_unit"] <= 0:
        note.append("Manopera e 0: oferta e DOAR materiale până completezi rândul «manopera» din fișierul de prețuri.")
    surse = sorted({(l["sursa"], l["data"]) for l in of["linii"] if l["sursa"]})
    if surse:
        note.append("Prețurile de referință sunt ORIENTATIVE, din liste publice: " + "; ".join(f"{s} ({d})" for s, d in surse) + ".")
    note.append("Nu cuprinde: fundația, învelitoarea, tâmplăria, instalațiile, finisajele, proiectarea, decât dacă sunt rânduri în fișierul de prețuri.")
    note.append(f"Fișierul de prețuri: {of['preturi_cale']}")
    L.append("NOTE:")
    for t in note:
        L.append("  - " + t)
    return "\n".join(L)


def salveaza_oferta(text, folder, model=""):
    os.makedirs(folder, exist_ok=True)
    baza = "".join(c if c.isalnum() or c in "-_" else "_" for c in (model or "model").rsplit(".", 1)[0])[:40]
    cale = os.path.join(folder, f"{baza}-oferta-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.md")
    with open(cale, "w", encoding="utf-8") as f:
        f.write("```\n" + text + "\n```\n")
    return cale
