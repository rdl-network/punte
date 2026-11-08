---
name: lista-de-materiale
description: Lista de materiale pe sortimente, gata de comandă, din modelul deschis în cadwork 3D (prin puntea cu buton `punte-cadwork`) sau din lista de elemente exportată din cadwork. Folosește-o când omul cere „lista de materiale”, „cantitățile”, „necesarul de lemn”, „ce comand pentru casa asta”.
---

# Lista de materiale din cadwork

Prima dintre cele cinci sarcini ale programului „Claude în atelier” (Revista din Lemn / Hub-ul Lemnului).
Scopul: din modelul 3D al constructorului iese, în două minute, lista pe sortimente pe care o pune în comandă sau în ofertă.
Skill-ul **citește**; nu schimbă modelul.

## 1. De unde iei datele

**A. Cu puntea (uneltele `punte-cadwork` sunt în listă):**

1. `cadwork_stare` — dacă cadwork 3D nu e pornit sau nu e deschis modelul potrivit, spune-i omului să-l deschidă; nu trimite job.
2. `cadwork_lista_elemente` — scrie jobul. Apoi spune-i omului, într-o singură propoziție: „Apasă butonul **punte_rdl** în cadwork
   (Window → User Plugins) și spune-mi «gata».” Nu trimite al doilea job; nu presupune că a apăsat.
3. `cadwork_rezultat` — citești `raspuns.piese`: o listă de piese cu `nume`, `categorie` (ecarisat / panouri / feronerie / altele),
   `material`, `latime_mm`, `inaltime_mm`, `lungime_mm`, `volum_m3`, `grupa`, `subgrupa`, `id`, plus `raspuns.model` (numele fișierului).
   Dacă răspunsul spune că jobul nu a fost rulat, repeți rugămintea de la pasul 2, fără job nou.

**B. Fără punte:** omul atașează lista de elemente exportată din cadwork (CSV / Excel). Cauți coloanele echivalente
(nume, material, lățime, înălțime, lungime, volum, tip / grupă). Dacă unitățile nu sunt clare, întrebi o dată (cadwork lucrează în mm).

## 2. Cum faci lista

1. **Filtru pe tip.** În cantități intră doar `ecarisat`, `panouri`, `feronerie`. Piesele `altele` (cadrele de vedere „Vederi”,
   casetele de detaliu „Det.”, auxiliarele, corpurile de export) se pomenesc într-un rând „excluse”, cu numele lor, și atât.
   Un model nou de cadwork are mereu două asemenea obiecte; nu sunt lemn.
2. **Sortimentul.** Ecarisat: material + secțiune (lățime × înălțime, în mm). Panouri: material + grosime (+ suprafața, în m²).
   Feronerie: tip + dimensiune. Aceeași secțiune cu material diferit = sortimente diferite (C24 și GL24h vin de la furnizori diferiți).
3. **Pe fiecare sortiment:** bucăți; lungimile grupate (ex. „2,70 ×4, 4,24 ×2”); lungimea totală (m); volumul net (m³, din model).
4. **Lungimea de comandă: nu inventezi reguli.** Dacă omul nu a spus cum comandă, întrebi o singură dată, la sfârșit:
   (a) lungimi fixe de la depozit (de obicei 3 / 4 / 5 / 6 m) sau tăiat la lungime; (b) adaosul de prelucrare și pierderi (%).
   Până atunci dai cantitățile **nete** și scrii că sunt nete. Orice adaos apare pe rând separat, niciodată amestecat în cifrele din model.
5. **Ordinea:** lemn masiv ecarisat (pe clase: C24, C18…), lemn lamelar încleiat (GL24h, GL28h…), panouri (OSB, placaj, CLT…), feronerie.
6. **Prezentarea:** un tabel pe categorie (sortiment · buc · lungimi · total m · m³), un rând de total pe categorie, rândul „excluse”,
   numele modelului și data. Numere cu virgulă zecimală (în română), 2 zecimale la metri, 4 la metri cubi. Limba omului (RO / DE / FR / IT / EN,
   după cum scrie el); termenii tehnici ai limbii lui (nu traduceri de dicționar).
7. **Verificarea, înainte de a trimite:** suma volumelor pe sortimente = totalul; lungime × secțiune ≈ volum pe fiecare sortiment
   (abaterile mari înseamnă prelucrări: le spui); „(fără material)” la o piesă de lemn = întrebi ce material e, nu presupui.

## 3. Ce NU faci

- Nu pui prețuri și nu estimezi costuri. Lista e pentru comandă și ofertă; prețurile vin din lista de prețuri a omului (alt skill: oferta de casă).
- Nu rotunjești în tăcere și nu adaugi pierderi nescrise.
- Nu modifici modelul. Dacă omul cere schimbări (altă secțiune, alt material), e alt job, pe care îl aprobă el prin buton.
- Nu numeri cadrele de vedere, auxiliarele, corpurile de export, cotele.

## 4. Exemplu (jurnalul de bord, 5 nov 2026, model `untitled1.3d`)

| Sortiment | Buc | Lungimi (m) | Total (m) | Volum (m³) |
|---|---|---|---|---|
| C24 80 × 160 mm | 4 | 2,31 ×4 | 9,24 | 0,1182 |
| C24 120 × 120 mm | 4 | 2,70 ×4 | 10,80 | 0,1555 |
| C24 120 × 240 mm | 2 | 4,24 ×2 | 8,48 | 0,2442 |
| GL24h 100 × 200 mm | 1 | 3,24 ×1 | 3,24 | 0,0648 |
| **Total ecarisat** | **11** | | **31,76** | **0,5828** |

Panouri: niciunul. Feronerie: niciuna. Excluse (nu sunt lemn): Vederi, Det. 01.
Cantitățile sunt nete, din model. Cum comanzi: lungimi fixe de la depozit sau la lungime? Ce adaos pentru prelucrare și pierderi?
