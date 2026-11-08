---
name: raportul-de-santier
description: Raportul de șantier pentru client, o pagină, din pozele și notițele de pe telefon de la ultima vizită — ce s-a făcut, ce urmează, ce avem nevoie de la el. Folosește-o când omul cere „fă raportul de șantier”, „scrie-i clientului ce am făcut săptămâna asta”, „uite pozele de azi, ce-i trimitem”, „unde suntem cu montajul la X”.
---

# Raportul de șantier

Sarcina 5 a programului „Claude în atelier” (Revista din Lemn / Hub-ul Lemnului). Scopul: patronul se întoarce de pe șantier cu zece
poze și trei rânduri de notițe în telefon, și în cinci minute clientul are o pagină clară: ce s-a făcut, ce urmează, ce avem nevoie de la el.
Raportul regulat e ce deosebește un atelier serios de unul la care clientul sună ca să afle. **Claude scrie, omul semnează și trimite.**

## 1. Ce primești și de unde

| Ce | De unde |
|---|---|
| **Pozele** de la vizită (de pe telefon) | atașate în chat; apoi în `7-montaj/poze-<data>/` din dosarul casei |
| **Notițele** omului (text, voce transcrisă, două rânduri pe WhatsApp către el însuși) | atașate sau dictate în chat |
| **Raportul trecut** | `7-montaj/raport-santier-<data anterioară>.md` — ca să spui ce s-a mișcat de atunci și ce ai promis |
| **Termenele** | `3-contract/termene.md`, `casa.md` (următorul pas) — ca să spui „suntem în grafic” doar dacă e adevărat |
| **Cine era acolo, vremea, ora** | notițele; dacă lipsesc și contează, întrebi o dată |

## 2. Regula de aur: scrii ce se vede și ce s-a notat, nu ce presupui

- Din poze descrii **ce se vede**: „pereții parterului montați pe toate laturile, planșeul peste parter pus pe două treimi”. Nu dai verdicte
  tehnice pe care poza nu le poate susține („îmbinările sunt corecte”, „izolația e pusă bine”). Dacă omul vrea să spună asta, e cuvântul lui, în
  notițe, și îl scrii ca al firmei.
- **Niciun procent de progres inventat.** „Două treimi din planșeu” se vede; „65 % din lucrare” nu. Dacă firma lucrează cu etape (din contract), spui
  în ce etapă suntem și ce a rămas din ea.
- **Problemele, pe nume, fără vină și fără eufemisme:** „Ploaia de marți și miercuri a oprit montajul acoperișului două zile. Reluăm joi.”
  Nu „condițiile meteo nefavorabile au influențat graficul”.
- **Datele sunt ferme doar dacă vin de la om.** „Săptămâna viitoare montăm căpriorii” e în regulă dacă el a spus-o. Nu promiți în locul lui.
- **Ce avem nevoie de la client** are termen și consecință: „Alegerea culorii tâmplăriei până vineri 14, altfel comanda intră cu o săptămână mai târziu.”

## 3. Pagina (și nu mai mult)

1. **Antet:** casa (numărul lucrării, clientul, adresa șantierului), data vizitei, cine a fost pe șantier din partea firmei, ora, vremea dacă a contat.
2. **Ce s-a făcut de la raportul trecut** — 3–6 puncte, concret, cu trimitere la poze (`[foto 1]`, `[foto 2]`). Primul punct = ce contează cel mai mult pentru client.
3. **Unde suntem față de grafic** — o propoziție adevărată: în grafic / cu N zile înainte / cu N zile în urmă, și de ce, dacă e în urmă.
4. **Ce urmează** (săptămâna viitoare, sau până la următorul raport) — 2–4 puncte, cu zilele, așa cum le-a spus omul.
5. **Ce avem nevoie de la dumneavoastră** — fiecare cu termen. Dacă nu e nimic: „Nimic de la dumneavoastră săptămâna asta.”
6. **Pozele** — numerotate, fiecare cu o legendă de un rând (ce se vede, din ce direcție). Cele 4–8 care spun povestea, nu toate 30.
7. **Semnătura** omului (nume, funcție, telefon). Următorul raport: data.

Tonul firmei (din Proiectul firmei): direct, fără adjective despre noi, fără „suntem încântați să vă anunțăm”. Limba clientului.
„Dumneavoastră” dacă firul e pe „dumneavoastră”. O pagină înseamnă o pagină: dacă e mai mult, e pentru că omul a cerut.

## 4. Cum o faci

1. Citești raportul trecut și `casa.md`: ce ai promis atunci că urmează? Raportul nou începe de acolo, ca să nu dispară promisiunile.
2. Te uiți la poze pe rând și notezi ce se vede în fiecare (loc, element, stadiu, direcția din care e făcută). Alegi cele care spun povestea.
3. Iei notițele omului și le pui în cele trei coșuri: făcut / urmează / avem nevoie de la client. Ce nu intră nicăieri, îl întrebi.
4. Scrii pagina. Verifici: fiecare afirmație are o poză sau o notiță în spate; termenele sunt ale omului; nicio vină, niciun eufemism.
5. Îl arăți omului cu două rânduri deasupra: ce ai lăsat deoparte din poze / notițe (problemă văzută în poză, dar nepomenită în notițe: i-o spui
   lui, nu clientului) și ce ai dedus (ca să confirme). El corectează, semnează, trimite.
6. În dosar: `7-montaj/raport-santier-<data>.md`, pozele folosite în `7-montaj/poze-<data>/` cu numele din legende, și o linie în `casa.md`
   la etapa 7 („7 Montaj · 12 nov  raport 3: pereți parter montați, planșeu 2/3; în grafic; de la client: culoarea tâmplăriei până 14 nov”).
   Dacă ai unealta de fișiere, le scrii tu; dacă nu, îi dai textul și locul.

## 5. Ce NU faci

- Nu trimiți raportul. Omul semnează și trimite (emailul care îl însoțește: skill-ul „emailul către client”).
- Nu dai verdicte tehnice din poze (corect / incorect, conform / neconform). Descrii. Verdictul e al omului.
- Nu inventezi progres, date, cauze. Nu dai vina pe furnizori sau pe vreme fără faptele din notițe.
- Nu ascunzi o problemă vizibilă în poză; o spui **omului**, înainte de raport, și el decide cum intră.
- Nu pui toate pozele. Nu pui poze cu oameni identificabili fără acordul lor.
- Nu copiezi raportul trecut cu data schimbată.

## 6. Exemplu (format; numele sunt locuri goale)

> **Raport de șantier nr. 3 — casa [Nume], [localitate] (lucrarea 2026-014)**
> Vizita: miercuri 12 nov 2026, 9:00–11:30 · pe șantier: [Prenume Nume] și echipa de montaj (3 oameni) · vreme bună după două zile de ploaie
>
> **Ce s-a făcut de la raportul din 5 nov**
> - Pereții parterului montați pe toate cele patru laturi și fixați pe talpă `[foto 1, 2]`.
> - Planșeul peste parter pus pe două treimi (zona de zi și dormitoarele); a rămas zona scării `[foto 3]`.
> - Golurile ferestrelor verificate cu tâmplarul la fața locului; dimensiunile corespund comenzii.
> - Ploaia de luni și marți a oprit lucrul două zile; materialul a stat acoperit `[foto 4]`.
>
> **Față de grafic:** două zile în urmă, din ploaie. Le recuperăm săptămâna viitoare, cu echipa completă.
>
> **Ce urmează (13–19 nov)**
> - Joi–vineri: restul planșeului și scara.
> - Luni–miercuri: pereții mansardei.
> - Joi 19: încep căpriorii, dacă ajunge cheresteaua pentru acoperiș (comandată, confirmată pentru 17 nov).
>
> **Ce avem nevoie de la dumneavoastră**
> - Culoarea tâmplăriei, până vineri 14 nov; după această dată comanda intră cu o săptămână întârziere.
> - Confirmarea poziției sobei (planul atașat raportului trecut), până la începerea mansardei, luni 16.
>
> Poze: 1 — peretele de sud, dinspre stradă · 2 — colțul nord-est, fixarea pe talpă · 3 — planșeul, dinspre scară · 4 — materialul acoperit, marți.
> Următorul raport: miercuri 19 nov.
>
> [Prenume Nume] · [Firma] · [telefon]

Pentru patron: în `[foto 3]` se vede un gol fără contravântuire provizorie lângă scară; n-am scris nimic în raport, spune-mi dacă e intenționat.
