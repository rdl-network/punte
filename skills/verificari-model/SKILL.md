---
name: verificari-model
description: Verificările pe modelul deschis în cadwork 3D — „ce lipsește / ce nu se leagă” — prin puntea vie `punte-cadwork` (uneltele `cadwork_verificari` + `cadwork_selecteaza`). Folosește-o când omul cere „verifică modelul”, „ce-i în neregulă aici”, „sunt dubluri?”, „lipsește ceva?”, „ce nu se leagă”, „controlează peretele ăsta” sau înainte de lista de comandă / ofertă pe un model la care n-a mai lucrat nimeni azi.
---

# Verificările pe model din cadwork

A treia facilitate a programului „Claude în atelier” (Revista din Lemn / Hub-ul Lemnului), făcută și testată viu pe 8 nov 2026.
Scopul: înainte să plece lista de comandă sau oferta, constructorul află în două minute ce e neobișnuit în model, cu piesele
arătate în fereastra lui. Skill-ul **citește**; singurul lucru pe care îl schimbă, cu Da-ul omului, e selecția din fereastră.

## 1. Ce verifică

**Pe lista de piese (instant):**
- lemn fără material, fără nume, fără subgrupă (nu aparține niciunui perete / ansamblu);
- secțiuni rare (≤3 piese) la 1–5 mm de o secțiune des folosită (≥5 piese, de ≥3 ori mai multe) — dimensiune greșită probabilă;
- piese peste lungimea comercială maximă (implicit 13 m; omul o poate schimba);
- piese degenerate: sub 10 cm lungime, sub 1 cm grosime, fără volum (resturi de la tăieri, copii uitate);
- aceeași secțiune cu materiale diferite (poate fi intenționat).

**Pe geometrie, în cadwork (job «citire», cu buget de timp):**
- piese dublate exact (aceeași piesă de două ori, una peste alta) — se numără dublu în liste și în ofertă;
- piese care nu ating nimic („plutesc”, nu se leagă de structură);
- piese care se întrepătrund (coliziuni) — la bârne și grinzi: îmbinare netăiată sau piesă nepoziționată; la izolație poate fi intenționat;
- gabaritul pieselor verificate.

Toate judecate doar între piese de lemn: învelișurile pereților (obiectele „perete”) ating și cuprind toate piesele lor prin construcție.

## 2. Cum o faci

1. `cadwork_stare` — cadwork pornit, puntea vie răspunde, ce model e deschis. Fără puntea vie, verificările nu merg: omul apasă o dată
   **punte_viu_rdl** în cadwork (Window → User Plugins).
2. **Alege întinderea cu omul, din ce a cerut:** tot modelul, un perete (`subgrupe="EG16"`) sau ce a selectat el (`doar_selectia=True`;
   un perete selectat ca obiect se desface singur în piesele lui).
3. **Spune-i cât durează înainte să pornești geometria:** ~0,35 s pe piesă. Un perete de 40 de piese = 15 s; o casă de 2.000 de piese
   = ~12 minute (cere cu `buget_s=900` și anunță-l). Pe un model mare, întâi `geometrie=False` (instant), apoi geometria pe peretele
   care îl interesează. Cât rulează jobul, puntea e ocupată: nu trimite altceva.
4. `cadwork_verificari(...)` — raportul vine pe trei niveluri: **DE CORECTAT** (sigur greșit: dubluri, piese care plutesc, degenerate,
   fără material), **DE VERIFICAT** (poate fi intenționat: coliziuni, secțiuni rare, fără nume, materiale amestecate), **ÎN REGULĂ**.
   Fiecare constatare are fișele pieselor (ID, nume, material, secțiune, lungime, perete) și un sfat scurt. Raportul `.md` rămâne în
   `cadwork-punte/liste/`.
5. **Arată-i în model ce ai găsit:** `cadwork_selecteaza("duplicate")` (sau „izolate”, „coliziuni”, „degenerate”, „sectiuni_rare”,
   „probleme” = tot ce e DE CORECTAT). În modul «întreabă» omul primește un dialog Da/Nu în cadwork: spune-i că apare și să răspundă acolo.
   Selecția lui de dinainte e înlocuită; modelul nu se schimbă.
6. **Citește raportul împreună cu el, nu i-l arunci.** Pe fiecare constatare: ce înseamnă pentru comandă / ofertă / producție și ce ar
   face în cadwork (șterge dublura, pune materialul, corectează secțiunea). Dacă vrea ca tu să corectezi, e alt job, cu Da-ul lui.

## 3. Ce NU faci

- Nu declari „greșit” ce e DE VERIFICAT: coliziunile la izolație, secțiunile rindeluite, bârnele de capăt pot fi intenționate. Întrebi.
- Nu modifici modelul din acest skill (nici ștergerea dublurilor). Verificarea = citire; corectura = alt job, aprobat de om.
- Nu rulezi geometria pe toată casa fără să-i spui cât durează.
- Nu confunzi „ce e neobișnuit în model” cu „ce e greșit în proiect”: dimensionarea, îmbinările, normativele rămân ale proiectantului.

## 4. Exemplu (jurnalul de bord, 8 nov 2026, modelul-exemplu cadwork `Blockbau-Testdatei.3d`, 2.329 elemente)

DE CORECTAT: 78 de piese dublate exact, toate în pereții EG16 (43) și EG05 (35) — doi pereți copiați de două ori, una peste alta;
o scândură de 2 cm lungime uitată în BB211. DE VERIFICAT: 76 de perechi în coliziune (EG20, EG24); 3 secțiuni la 1 mm de cele standard
(117×125 ×2 lângă 118×125 ×215); 916 piese fără nume. ÎN REGULĂ: material, subgrupe, lungimi, nimic nu plutește. Geometria: 2.083 piese
în 604 s. Apoi `cadwork_selecteaza("duplicate")` → Da-ul omului → cele 78 de dubluri selectate și cu zoom în fereastra lui.
