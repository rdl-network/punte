# -*- coding: utf-8 -*-
"""verificari — VERIFICĂRILE PE MODEL: „ce lipsește / ce nu se leagă” (a treia facilitate a nișei, 8 nov 2026).

Două straturi, amândouă doar citire:
  1. Pe lista de piese (fără geometrie, merge și offline pe un JSON al punții): lemn fără material, fără nume, fără subgrupă
     (nu aparține niciunui perete), secțiuni „rare” lângă o secțiune des folosită (greșeală probabilă de dimensiune: 167 × 175
     ×3 lângă 168 × 175 ×40), piese peste lungimea comercială maximă, piese degenerate (prea scurte / prea subțiri / fără volum),
     aceeași secțiune cu materiale diferite, panouri fără material.
  2. Pe geometrie, prin punte, cu un job «citire» (COD_GEOMETRIE): piese dublate exact (check_element_duplicates), piese care nu
     ating nimic (fără contact și fără coliziune: „plutesc”), piese care se întrepătrund (coliziuni), gabaritul modelului.
     Jobul are buget de timp: spune câte piese a apucat să verifice.

Funcții pure: verifica_lista(piese, …) → dict; verifica_geometrie(raspuns_job) → dict; formateaza(rez, model) → text;
salveaza(text, folder, model) → cale .md. Piesele au forma dată de puntea vie (op `lista` / `selectie`).
"""
import os
import datetime
from collections import Counter, OrderedDict, defaultdict

LUNGIME_MAX_IMPLICITA = 13000      # mm — peste atât nu se găsește bară comercială (vezi lista_comanda)
MATERIALE_LIPSA = {"", "(fara material)", "(fără material)", "non-defined", "undefined", "-"}
NUME_LIPSA = {"", "(fara nume)", "(fără nume)"}
EXEMPLE = 8                        # câte piese arătăm pe fiecare constatare


def _m(mm):
    return f"{mm / 1000:.2f}".replace(".", ",")


def _fisa(p):
    sg = f" [{p.get('subgrupa')}]" if p.get("subgrupa") else ""
    return (f"#{p['id']} {p.get('nume') or '(fără nume)'} {p.get('material') or '(fără material)'} "
            f"{int(round(p['latime_mm']))} x {int(round(p['inaltime_mm']))} L {_m(p['lungime_mm'])} m{sg}")


def filtreaza(piese, subgrupe=None, doar_ids=None, subgrupe_exacte=None):
    """Același filtru ca la lista de comandă: fragmente de subgrupă / grupă, ID-uri alese, subgrupe exacte (peretele selectat)."""
    sel = list(piese)
    if doar_ids is not None or subgrupe_exacte:
        ids = set(int(i) for i in (doar_ids or []))
        exacte = set(subgrupe_exacte or [])
        sel = [p for p in sel if int(p["id"]) in ids or (p.get("subgrupa") or "") in exacte]
    if subgrupe:
        frag = [s.lower() for s in subgrupe if s]
        sel = [p for p in sel if any(f in (p.get("subgrupa") or "").lower() or f in (p.get("grupa") or "").lower() for f in frag)]
    return sel


def verifica_lista(piese, lungime_max_mm=LUNGIME_MAX_IMPLICITA, subgrupe=None, doar_ids=None, subgrupe_exacte=None):
    """Constatările din lista de piese. Întoarce dict cu `constatari` (listă ordonată: corectat / verificat / ok) + numărători."""
    sel = filtreaza(piese, subgrupe, doar_ids, subgrupe_exacte)
    lemn = [p for p in sel if p["categorie"] in ("ecarisat", "panouri")]
    ecarisat = [p for p in lemn if p["categorie"] == "ecarisat"]
    panouri = [p for p in lemn if p["categorie"] == "panouri"]
    altele = Counter(p.get("nume") or "(fără nume)" for p in sel if p["categorie"] not in ("ecarisat", "panouri"))
    c = []

    def adauga(nivel, cheie, titlu, piese_gasite, sfat="", detalii=None):
        c.append({"nivel": nivel, "cheie": cheie, "titlu": titlu, "n": len(piese_gasite),
                  "exemple": [_fisa(p) for p in piese_gasite[:EXEMPLE]], "ids": [int(p["id"]) for p in piese_gasite],
                  "sfat": sfat, "detalii": detalii or []})

    # 1. material
    fara_mat = [p for p in lemn if (p.get("material") or "").strip().lower() in MATERIALE_LIPSA]
    if fara_mat:
        adauga("corectat", "fara_material", "lemn fără material", fara_mat,
               "fără material nu intră corect în lista de comandă și în ofertă; pune-l din Modify → Material (sau cere-mi să-l pun eu).")
    else:
        adauga("ok", "fara_material", "toate piesele de lemn au material", [])

    # 2. subgrupă (apartenența la un perete / ansamblu)
    cu_sg = [p for p in lemn if p.get("subgrupa")]
    fara_sg = [p for p in lemn if not p.get("subgrupa")]
    if cu_sg and fara_sg:
        adauga("corectat", "fara_subgrupa", "lemn fără subgrupă (nu aparține niciunui perete / ansamblu)", fara_sg,
               "restul modelului e pe subgrupe; piesele astea nu vor apărea în listele pe perete și nici în selecția „peretele întreg”.")
    elif not cu_sg and lemn:
        adauga("verificat", "fara_subgrupa", "modelul nu folosește subgrupe deloc", [],
               "listele pe perete și selecția „peretele întreg” nu vor merge; e în regulă pentru un model mic.")
    else:
        adauga("ok", "fara_subgrupa", "toate piesele de lemn sunt pe subgrupe (pereți / ansambluri)", [])

    # 3. nume
    fara_nume = [p for p in lemn if (p.get("nume") or "").strip().lower() in NUME_LIPSA]
    if fara_nume:
        pe_sg = Counter(p.get("subgrupa") or "(fără subgrupă)" for p in fara_nume)
        adauga("verificat", "fara_nume", "lemn fără nume", fara_nume,
               "lista de comandă merge pe secțiuni, dar în listele de producție și pe etichete piesele astea apar goale.",
               [f"pe subgrupe: " + ", ".join(f"{k} ({v})" for k, v in pe_sg.most_common(10)) + (" …" if len(pe_sg) > 10 else "")])
        c[-1]["exemple"] = []            # distribuția pe subgrupe ajunge; 8 fișe identice nu spun nimic
    else:
        adauga("ok", "fara_nume", "toate piesele de lemn au nume", [])

    # 4. secțiuni rare lângă secțiuni des folosite (greșeală probabilă de dimensiune)
    sort = OrderedDict()
    for p in ecarisat:
        w, h = sorted((int(round(p["latime_mm"])), int(round(p["inaltime_mm"]))))
        sort.setdefault((p.get("material") or "", w, h), []).append(p)
    suspecte, detalii = [], []
    for (mat, w, h), lista in sort.items():
        if len(lista) > 3:
            continue
        vecin = None
        for (mat2, w2, h2), lista2 in sort.items():
            if mat2 != mat or (w2, h2) == (w, h) or len(lista2) < 5 or len(lista2) < 3 * len(lista):
                continue
            if abs(w2 - w) <= 5 and abs(h2 - h) <= 5:
                if vecin is None or len(lista2) > len(vecin[1]):
                    vecin = ((w2, h2), lista2)
        if vecin:
            suspecte += lista
            detalii.append(f"{w} x {h} ×{len(lista)} lângă {vecin[0][0]} x {vecin[0][1]} ×{len(vecin[1])} ({mat or 'fără material'})")
    if suspecte:
        adauga("verificat", "sectiuni_rare", "secțiuni rare la 1–5 mm de o secțiune des folosită (dimensiune greșită?)", suspecte,
               "dacă e aceeași bară, pune-i secțiunea corectă; dacă e intenționat (rindeluit, bârnă de capăt), lasă așa.", detalii)
    else:
        adauga("ok", "sectiuni_rare", "nicio secțiune rară suspectă lângă una des folosită", [])

    # 5. prea lungi
    prea_lungi = [p for p in ecarisat if p["lungime_mm"] > lungime_max_mm]
    if prea_lungi:
        adauga("corectat", "prea_lungi", f"piese peste lungimea comercială maximă ({_m(lungime_max_mm)} m)", prea_lungi,
               "nu se găsesc ca bară întreagă: le îmbini (nădire) sau comanzi lamelar la lungime, cu preț pe comandă.")
    else:
        adauga("ok", "prea_lungi", f"nicio piesă peste {_m(lungime_max_mm)} m", [])

    # 6. degenerate
    degenerate = [p for p in ecarisat if p["lungime_mm"] < 100 or min(p["latime_mm"], p["inaltime_mm"]) < 10 or float(p.get("volum_m3") or 0) <= 0]
    degenerate += [p for p in panouri if min(p["latime_mm"], p["inaltime_mm"], p["lungime_mm"]) < 3 or float(p.get("volum_m3") or 0) <= 0]
    if degenerate:
        adauga("corectat", "degenerate", "piese degenerate (sub 10 cm lungime, sub 1 cm grosime sau fără volum)", degenerate,
               "de obicei resturi de la tăieri sau copii uitate; șterge-le sau cere-mi să le selectez ca să le vezi.")
    else:
        adauga("ok", "degenerate", "nicio piesă degenerată", [])

    # 7. aceeași secțiune, materiale diferite (informativ)
    pe_sectiune = defaultdict(Counter)
    for (mat, w, h), lista in sort.items():
        pe_sectiune[(w, h)][mat or "(fără material)"] += len(lista)
    amestec = [(s, m) for s, m in pe_sectiune.items() if len(m) > 1]
    if amestec:
        det = [f"{w} x {h}: " + ", ".join(f"{k} ×{v}" for k, v in m.most_common()) for (w, h), m in sorted(amestec)]
        adauga("verificat", "material_amestecat", "aceeași secțiune cu materiale diferite", [],
               "e corect dacă e intenționat (C24 pentru montanți, GL24h pentru grinzi); dacă nu, uniformizează materialul.", det)
    else:
        adauga("ok", "material_amestecat", "fiecare secțiune are un singur material", [])

    ordine = {"corectat": 0, "verificat": 1, "ok": 2}
    c.sort(key=lambda x: ordine[x["nivel"]])
    return {
        "cand": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "lungime_max_mm": lungime_max_mm,
        "filtru": {"subgrupe": subgrupe or [], "doar_ids": len(doar_ids) if doar_ids is not None else None,
                   "pereti": list(subgrupe_exacte or [])},
        "piese_total": len(piese), "in_filtru": len(sel), "lemn": len(lemn), "ecarisat": len(ecarisat), "panouri": len(panouri),
        "altele": dict(altele.most_common(8)), "altele_total": sum(altele.values()),
        "ids_lemn": [int(p["id"]) for p in lemn],
        "constatari": c,
        "geometrie": None,
    }


# ---------------------------------------------------------------- geometria, prin punte (job «citire»)

COD_GEOMETRIE = r'''
# verificari pe geometrie (doar citire): dubluri exacte, piese care nu ating nimic, coliziuni, gabarit. Buget de timp.
import datetime
IDS = __IDS__
LEMN = __LEMN__           # tot lemnul din model: partenerii de contact / coliziune, si cand verificam doar un perete
BUGET_S = __BUGET__
t0 = datetime.datetime.now()
def gata():
    return (datetime.datetime.now() - t0).total_seconds() > BUGET_S
in_model = set(ec.get_all_identifiable_element_ids())
ids = [i for i in IDS if i in in_model]
lemn = set(i for i in (LEMN or IDS) if i in in_model)   # doar intre piese de lemn: invelisurile peretilor (Hüllen) le cuprind pe toate, prin constructie
raspuns["lipsa_din_model"] = len(IDS) - len(ids)
dup_tot = set()
try:
    dup_tot = set(int(i) for i in ec.check_element_duplicates(sorted(lemn)))   # pe tot lemnul: geamanul unei piese selectate poate fi in afara selectiei
except Exception as e:
    raspuns["duplicate_eroare"] = str(e)
idset = set(ids)
try:
    v = ec.get_bounding_box_vertices_global(ids) if ids else []
    if v:
        xs = [p.x for p in v]; ys = [p.y for p in v]; zs = [p.z for p in v]
        raspuns["gabarit_mm"] = [round(max(xs) - min(xs)), round(max(ys) - min(ys)), round(max(zs) - min(zs))]
except Exception as e:
    raspuns["gabarit_eroare"] = str(e)
izolate, coliziuni, verificate = [], set(), 0
for eid in ids:
    if gata():
        break
    try:
        contact = [c for c in ec.get_elements_in_contact(eid) if int(c) in lemn]
        colid = [c for c in ec.get_elements_in_collision(eid) if int(c) in lemn]
    except Exception as e:
        raspuns.setdefault("erori", []).append([int(eid), str(e)])
        continue
    verificate += 1
    for c in colid:
        a, b = sorted((int(eid), int(c)))
        coliziuni.add((a, b))
    if not contact and not colid:
        izolate.append(int(eid))
raspuns["izolate"] = izolate
# dublurile raportate: piesele verificate care sunt dubluri, plus piesele verificate care se ciocnesc cu o dublura (perechea lor)
dubluri = {i for i in ids if i in dup_tot}
for a, b in coliziuni:
    if a in dup_tot or b in dup_tot:
        dubluri |= {x for x in (a, b) if x in idset}
raspuns["duplicate"] = sorted(dubluri)
raspuns["coliziuni"] = sorted(list(p) for p in coliziuni)
raspuns["verificate"] = verificate
raspuns["din"] = len(ids)
raspuns["timp_s"] = round((datetime.datetime.now() - t0).total_seconds(), 1)
raspuns["buget_atins"] = verificate < len(ids)
print(f"geometrie: {verificate}/{len(ids)} piese in {raspuns['timp_s']} s; dubluri {len(raspuns.get('duplicate', []))}, izolate {len(izolate)}, coliziuni {len(coliziuni)}")
'''


def cod_geometrie(ids, buget_s=60, lemn_toate=None):
    """`ids` = piesele de verificat (filtrate); `lemn_toate` = tot lemnul din model, ca partenerii de contact să fie și cei din
    pereții vecini (altfel bârna de colț ar părea izolată când verificăm un singur perete)."""
    return (COD_GEOMETRIE.replace("__IDS__", repr([int(i) for i in ids])).replace("__BUGET__", repr(float(buget_s)))
            .replace("__LEMN__", repr([int(i) for i in (lemn_toate or [])])))


COD_SELECTEAZA = r'''
# selecteaza in fereastra cadwork piesele cu probleme gasite de verificari (nu schimba modelul)
import visualization_controller
IDS = __IDS__
in_model = set(ec.get_all_identifiable_element_ids())
ids = [i for i in IDS if i in in_model]
active = list(ec.get_active_identifiable_element_ids())
if active:
    visualization_controller.set_inactive(active)
if ids:
    visualization_controller.set_active(ids)
    visualization_controller.zoom_active_elements()
raspuns["selectate"] = len(ids)
print(f"selectate {len(ids)} piese in cadwork (zoom pe ele); cele {len(IDS) - len(ids)} lipsa nu mai sunt in model")
'''


def cod_selecteaza(ids):
    return COD_SELECTEAZA.replace("__IDS__", repr([int(i) for i in ids]))


def verifica_geometrie(raspuns, piese_dupa_id=None):
    """Constatările din răspunsul jobului COD_GEOMETRIE. `piese_dupa_id` = {id: piesa} pentru fișe în loc de ID-uri goale."""
    piese_dupa_id = piese_dupa_id or {}
    c = []

    def fise(ids):
        return [_fisa(piese_dupa_id[i]) if i in piese_dupa_id else f"#{i}" for i in ids[:EXEMPLE]]

    dup = [int(i) for i in (raspuns.get("duplicate") or [])]
    dup_set = set(dup)
    col_toate = [[int(a), int(b)] for a, b in (raspuns.get("coliziuni") or [])]
    col_dubluri = [pereche for pereche in col_toate if pereche[0] in dup_set or pereche[1] in dup_set]
    col = [pereche for pereche in col_toate if pereche[0] not in dup_set and pereche[1] not in dup_set]

    def pe_subgrupe(ids):
        c_sg = Counter((piese_dupa_id.get(i) or {}).get("subgrupa") or "(fără subgrupă)" for i in ids)
        return ", ".join(f"{k} ({v})" for k, v in c_sg.most_common(8)) + (" …" if len(c_sg) > 8 else "")

    if raspuns.get("duplicate_eroare"):
        c.append({"nivel": "verificat", "cheie": "duplicate", "titlu": "dublurile n-au putut fi verificate", "n": 0, "exemple": [],
                  "ids": [], "sfat": raspuns["duplicate_eroare"], "detalii": []})
    elif dup:
        c_sg = Counter((piese_dupa_id.get(i) or {}).get("subgrupa") or "(fără subgrupă)" for i in dup)
        det = ["pe subgrupe: " + pe_subgrupe(dup)]
        pereti_dublati = [k for k, v in c_sg.items() if v >= 10]
        if pereti_dublati:
            det.append(f"la {', '.join(pereti_dublati)} sunt zeci de dubluri: probabil peretele întreg a fost copiat de două ori, una peste alta")
        if col_dubluri:
            det.append(f"{len(col_dubluri)} dintre coliziuni sunt chiar dublurile astea (nu le mai număr mai jos)")
        c.append({"nivel": "corectat", "cheie": "duplicate", "titlu": "piese dublate exact (aceeași piesă de două ori, una peste alta)",
                  "n": len(dup), "exemple": fise(dup), "ids": dup,
                  "sfat": "se numără de două ori în liste și în ofertă; șterge dublura (cadwork: Modify → Check duplicates face același lucru).",
                  "detalii": det})
    else:
        c.append({"nivel": "ok", "cheie": "duplicate", "titlu": "nicio piesă dublată", "n": 0, "exemple": [], "ids": [], "sfat": "", "detalii": []})

    izo = raspuns.get("izolate") or []
    if izo:
        c.append({"nivel": "corectat", "cheie": "izolate", "titlu": "piese care nu ating nimic (plutesc, nu se leagă de structură)",
                  "n": len(izo), "exemple": fise(izo), "ids": izo,
                  "sfat": "ori sunt la distanță de restul (mutate / uitate), ori lipsește piesa de legătură; uită-te la ele în model.",
                  "detalii": []})
    else:
        c.append({"nivel": "ok", "cheie": "izolate", "titlu": "fiecare piesă verificată atinge cel puțin o alta", "n": 0, "exemple": [],
                  "ids": [], "sfat": "", "detalii": []})

    if col:
        ids = sorted({i for pereche in col for i in pereche})
        det = ["pe subgrupe: " + pe_subgrupe(ids)]
        det += [f"#{a} ↔ #{b}" + (f"  ({piese_dupa_id[a].get('nume')} / {piese_dupa_id[b].get('nume')})" if a in piese_dupa_id and b in piese_dupa_id else "")
                for a, b in col[:EXEMPLE]]
        c.append({"nivel": "verificat", "cheie": "coliziuni", "titlu": f"piese care se întrepătrund ({len(col)} {'pereche' if len(col) == 1 else 'perechi'} în coliziune)",
                  "n": len(ids), "exemple": fise(ids), "ids": ids,
                  "sfat": "la bârne și grinzi înseamnă de obicei o îmbinare netăiată sau o piesă nepoziționată; la izolație poate fi intenționat.",
                  "detalii": det + ([f"… încă {len(col) - EXEMPLE} perechi"] if len(col) > EXEMPLE else [])})
    else:
        c.append({"nivel": "ok", "cheie": "coliziuni", "titlu": "nicio coliziune între piesele verificate" + (" (în afara dublurilor)" if col_dubluri else ""),
                  "n": 0, "exemple": [], "ids": [], "sfat": "", "detalii": []})

    g = raspuns.get("gabarit_mm")
    return {"constatari": c, "gabarit_mm": g, "verificate": raspuns.get("verificate", 0), "din": raspuns.get("din", 0),
            "timp_s": raspuns.get("timp_s"), "buget_atins": bool(raspuns.get("buget_atins")),
            "lipsa_din_model": raspuns.get("lipsa_din_model", 0), "erori": raspuns.get("erori") or []}


def combina(rez_lista, rez_geo):
    """Pune constatările geometrice lângă cele din listă, ordonate corectat / verificat / ok."""
    rez = dict(rez_lista)
    rez["geometrie"] = rez_geo
    ordine = {"corectat": 0, "verificat": 1, "ok": 2}
    rez["constatari"] = sorted(rez_lista["constatari"] + (rez_geo["constatari"] if rez_geo else []), key=lambda x: ordine[x["nivel"]])
    return rez


def ids_probleme(rez, niveluri=("corectat",)):
    """ID-urile din constatările de nivelul dat (implicit doar «de corectat»), pentru selecția în cadwork. Cele «de verificat»
    se selectează pe nume (ex. „sectiuni_rare”), ca să nu selectăm 900 de piese fără nume."""
    out = []
    for c in rez["constatari"]:
        if c["nivel"] in niveluri:
            out += c["ids"]
    return sorted(set(out))


# ---------------------------------------------------------------- textul

def formateaza(rez, model=""):
    f = rez.get("filtru") or {}
    filtru = ""
    if f.get("subgrupe"):
        filtru = f" — doar subgrupele {', '.join(f['subgrupe'])}"
    elif f.get("pereti"):
        filtru = f" — doar selecția: {'peretele' if len(f['pereti']) == 1 else 'pereții'} {', '.join(f['pereti'])}" \
                 + (f" + {f['doar_ids']} piese alese" if f.get("doar_ids") else "")
    elif f.get("doar_ids") is not None:
        filtru = f" — doar selecția ({f['doar_ids']} {'piesă' if f['doar_ids'] == 1 else 'piese'})"
    g = rez.get("geometrie")
    linii = [f"VERIFICĂRI PE MODEL — {model or 'modelul deschis'}{filtru}",
             f"{rez['lemn']} piese de lemn verificate (ecarisat {rez['ecarisat']}, panouri {rez['panouri']}) din {rez['in_filtru']} elemente"
             + (f" ({rez['piese_total']} în tot modelul)" if rez['in_filtru'] != rez['piese_total'] else "") + f"; {rez['cand']}"]
    if g and g.get("gabarit_mm"):
        gx, gy, gz = g["gabarit_mm"]
        linii.append(f"Gabaritul pieselor verificate: {_m(gx)} × {_m(gy)} × {_m(gz)} m (lungime × lățime × înălțime, pe axele modelului)")
    linii.append("")
    etichete = {"corectat": "DE CORECTAT", "verificat": "DE VERIFICAT (poate fi intenționat)", "ok": "ÎN REGULĂ"}
    semne = {"corectat": "!!", "verificat": " ?", "ok": " ✓"}
    for nivel in ("corectat", "verificat", "ok"):
        grup = [c for c in rez["constatari"] if c["nivel"] == nivel]
        if not grup:
            continue
        linii.append(f"{etichete[nivel]}:")
        for c in grup:
            n = f" — {c['n']} {'piesă' if c['n'] == 1 else 'piese'}" if c["n"] else ""
            linii.append(f"  {semne[nivel]} {c['titlu']}{n}")
            if nivel != "ok":
                for d in c["detalii"]:
                    linii.append(f"       {d}")
                for e in c["exemple"]:
                    linii.append(f"       {e}")
                if c["exemple"] and c["n"] > len(c["exemple"]):
                    linii.append(f"       … încă {c['n'] - len(c['exemple'])}")
                if c["sfat"]:
                    linii.append(f"       → {c['sfat']}")
        linii.append("")
    if g:
        acoperire = f"Geometria: {g['verificate']} din {g['din']} piese verificate la contact și coliziune în {g['timp_s']} s"
        if g["buget_atins"]:
            acoperire += " — BUGETUL DE TIMP s-a terminat înainte de capăt; restul pieselor nu sunt verificate (cere din nou cu buget mai mare)."
        else:
            acoperire += " (toate)."
        if g.get("lipsa_din_model"):
            acoperire += f" {g['lipsa_din_model']} ID-uri din listă nu mai erau în model."
        if g.get("erori"):
            acoperire += f" {len(g['erori'])} piese au dat eroare la citire."
        linii.append(acoperire)
    else:
        linii.append("Geometria (dubluri, piese care nu ating nimic, coliziuni) NU a fost verificată — doar lista de piese.")
    if rez.get("altele_total"):
        alt = ", ".join(f"{k} ({v})" for k, v in rez["altele"].items())
        linii.append(f"Neverificate (nu sunt lemn: goluri, învelișuri, ajutătoare): {rez['altele_total']} — {alt}")
    linii.append("")
    linii.append("Verificările sunt mecanice: spun ce e neobișnuit în model, nu ce e greșit în proiect. Deciziile rămân ale proiectantului.")
    return "\n".join(linii)


def salveaza(text, folder, model=""):
    os.makedirs(folder, exist_ok=True)
    baza = "".join(c if c.isalnum() or c in "-_" else "_" for c in (model or "model").rsplit(".", 1)[0])[:40]
    cale = os.path.join(folder, f"{baza}-verificari-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.md")
    with open(cale, "w", encoding="utf-8") as f:
        f.write("```\n" + text + "\n```\n")
    return cale
