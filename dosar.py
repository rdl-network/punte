# -*- coding: utf-8 -*-
"""dosar — forma standard a „dosarului casei” (un folder pe lucrare), v0, 8 nov 2026. Foaia: docs/claude-in-atelier/dosarul-casei.md.

Două lucruri știe modulul ăsta și nimic altceva:
  1. forma folderului: opt etape numerotate + corespondența + `casa.md` („unde suntem”);
  2. cum se pune un fișier în etapa lui, cu data în nume, și cum se scrie o linie în `casa.md` la etapa potrivită.

Funcții pure, fără cadwork: creeaza(cale) · verifica(cale) · cale_fisier(dosar, etapa, baza, ext) · noteaza(dosar, etapa, text).
Reguli ținute aici: nu șterge și nu suprascrie niciodată (a doua versiune în aceeași zi primește ora în nume); scrie doar în folderul dat.
"""
import os
import re
import datetime

ETAPE = (
    ("1-cerere", "1 Cerere"),
    ("2-oferta", "2 Ofertă"),
    ("3-contract", "3 Contract"),
    ("4-proiect", "4 Proiect"),
    ("5-comenzi", "5 Comenzi"),
    ("6-productie", "6 Producție"),
    ("7-montaj", "7 Montaj"),
    ("8-receptie", "8 Recepție"),
)
FOLDERE = tuple(f for f, _ in ETAPE) + ("corespondenta",)
ETICHETA = dict(ETAPE)
CASA = "casa.md"
LUNI = ("ian", "feb", "mar", "apr", "mai", "iun", "iul", "aug", "sept", "oct", "nov", "dec")

SABLON_CASA = """# {nume}

Client: {client}
Ce construim: {ce}
Sursa:

## Stadiul
{stadiu}

## Următorul pas


## Istoric
"""


def _azi():
    return datetime.date.today()


def _data_scurta(d=None):
    d = d or _azi()
    return f"{d.day} {LUNI[d.month - 1]}"


def creeaza(cale, client="", ce=""):
    """Face folderul casei cu toate etapele și `casa.md` de completat. Nu atinge ce există deja. Întoarce lista a ce a creat."""
    cale = os.path.abspath(cale)
    create = []
    if not os.path.isdir(cale):
        os.makedirs(cale)
        create.append(cale)
    for f in FOLDERE:
        p = os.path.join(cale, f)
        if not os.path.isdir(p):
            os.makedirs(p)
            create.append(p)
    casa = os.path.join(cale, CASA)
    if not os.path.exists(casa):
        stadiu = "\n".join(f"- {et:<12} ·" for _, et in ETAPE)
        with open(casa, "w", encoding="utf-8") as fh:
            fh.write(SABLON_CASA.format(nume=os.path.basename(cale), client=client, ce=ce, stadiu=stadiu))
        create.append(casa)
    return create


def verifica(cale):
    """Întoarce (ok, mesaj): e folderul ăsta un dosar al casei? (există, are casa.md sau măcar etapele)."""
    if not cale:
        return False, "nu e dat niciun dosar"
    cale = os.path.abspath(cale)
    if not os.path.isdir(cale):
        return False, f"folderul nu există: {cale} (îl faci cu cadwork_dosar_nou sau îl creezi tu, cu structura din dosarul-casei.md)"
    are_casa = os.path.exists(os.path.join(cale, CASA))
    are_etape = any(os.path.isdir(os.path.join(cale, f)) for f, _ in ETAPE)
    if not (are_casa or are_etape):
        return False, f"{cale} nu arată a dosar al casei (nu are casa.md și nici etapele 1-cerere … 8-receptie); cadwork_dosar_nou îl pune în formă"
    return True, cale


def cale_fisier(dosar, etapa, baza, ext, cand=None):
    """Calea unui fișier nou în etapa lui: <dosar>/<etapa>/<baza>-<AAAA-LL-ZZ>.<ext>; dacă există deja azi, adaugă ora (nu suprascrie)."""
    if etapa not in FOLDERE:
        raise ValueError(f"etapă necunoscută «{etapa}»; etapele: {', '.join(FOLDERE)}")
    cand = cand or datetime.datetime.now()
    folder = os.path.join(os.path.abspath(dosar), etapa)
    os.makedirs(folder, exist_ok=True)
    ext = ext.lstrip(".")
    p = os.path.join(folder, f"{baza}-{cand:%Y-%m-%d}.{ext}")
    if os.path.exists(p):
        p = os.path.join(folder, f"{baza}-{cand:%Y-%m-%d}-{cand:%H%M}.{ext}")
    n = 2
    while os.path.exists(p):
        p = os.path.join(folder, f"{baza}-{cand:%Y-%m-%d}-{cand:%H%M}-{n}.{ext}")
        n += 1
    return p


def noteaza(dosar, etapa, text, cand=None, bifa=True):
    """Scrie în casa.md: linia etapei din «Stadiul» devine «✓ <data>  <text>» (sau «· <data>  <text>» fără bifă) și o linie datată intră
    în «Istoric». Dacă casa.md lipsește, îl creează. Întoarce calea lui casa.md."""
    cand = cand or datetime.datetime.now()
    dosar = os.path.abspath(dosar)
    casa = os.path.join(dosar, CASA)
    if not os.path.exists(casa):
        creeaza(dosar)
    s = open(casa, encoding="utf-8").read()
    eticheta = ETICHETA.get(etapa, etapa)
    semn = "✓" if bifa else "·"
    linie_noua = f"- {eticheta:<12} {semn} {_data_scurta(cand.date()):<8} {text}"
    tipar = re.compile(r"^- " + re.escape(eticheta) + r"\b.*$", re.MULTILINE)
    if tipar.search(s):
        s = tipar.sub(lambda m: linie_noua, s, count=1)
    elif "## Stadiul" in s:
        s = s.replace("## Stadiul\n", "## Stadiul\n" + linie_noua + "\n", 1)
    else:
        s = s.rstrip("\n") + "\n\n## Stadiul\n" + linie_noua + "\n"
    istoric = f"- {cand:%Y-%m-%d %H:%M} · {eticheta}: {text}"
    if "## Istoric" in s:
        s = s.rstrip("\n") + "\n" + istoric + "\n"
    else:
        s = s.rstrip("\n") + "\n\n## Istoric\n" + istoric + "\n"
    with open(casa, "w", encoding="utf-8") as fh:
        fh.write(s)
    return casa


def stadiul(dosar):
    """Textul lui casa.md (ce citește Claude la „unde suntem cu casa asta?”)."""
    casa = os.path.join(os.path.abspath(dosar), CASA)
    if not os.path.exists(casa):
        return None
    return open(casa, encoding="utf-8").read()
