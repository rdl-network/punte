---
name: oferta-de-casa
description: Oferta de preț a atelierului pentru o casă / structură din lemn — din modelul deschis în cadwork 3D (prin `punte-cadwork`, unealta `cadwork_oferta`) sau, fără model, din cererea clientului și lista de prețuri a firmei. Folosește-o când omul cere „fă oferta”, „cât costă casa asta”, „scrie-i o ofertă lui X”, „refă oferta cu cantitățile din model”, „studiu de volum din schiță”.
---

# Oferta de casă

Sarcina 1 a programului „Claude în atelier” (Revista din Lemn / Hub-ul Lemnului), cea care convinge clientul. Scopul: din cererea
clientului (și din model, când există) iese, în ora aceea, oferta **în formatul atelierului**, cu fiecare cifră trasabilă la sursa ei și
cu golurile marcate, nu umplute. **Claude scrie, omul semnează.** Nimic nu pleacă la client fără semnătura lui.

## 1. Ce ai la îndemână și de unde

| Sursă | Unde e | La ce folosește |
|---|---|---|
| **Ofertele-model ale firmei** (două-trei oferte trimise, care i-au plăcut patronului) | Proiectul firmei din Claude Desktop | formatul, capitolele, tonul, ce include / ce exclude de obicei firma |
| **Lista de prețuri a firmei** | Proiectul firmei (sau fișierul CSV dat uneltei `cadwork_oferta`) | singurele prețuri pe care le folosești |
| **Cererea clientului** | `1-cerere/` din dosarul casei: emailul, schița, pozele, `cererea.md` | ce vrea, unde, când, bugetul dacă l-a spus |
| **Modelul cadwork**, când există | deschis în cadwork; `4-proiect/model.3d` | cantitățile reale (prin `cadwork_lista_comanda` / `cadwork_oferta`) |
| **Prețurile de referință din pachet** (`preturi-referinta.csv`) | lângă server | DOAR ca șablon de format sau ca reper, spus explicit „orientativ, din liste publice, cu data”; niciodată ca preț al firmei |

Dacă lipsește lista de prețuri a firmei, oferta e **orientativă** și scrie asta în titlu și în prima frază. Nu „estimezi” prețuri din memorie.

## 2. Două drumuri

**A. Din model (cadwork deschis, puntea vie pornită).**
1. `cadwork_stare` → modelul potrivit e deschis?
2. `cadwork_oferta(preturi_csv=<lista firmei>, lungimi_comerciale=<cum comandă el: „4,5,6”>, client=…, obiect=…, firma=…, dosar=<folderul casei>)`
   — face lista de comandă din model (sortimente, croială, bare, m³, panouri în m²) × prețuri → materiale, transport, manoperă, regie,
   TVA 21 %, total; scrie `2-oferta/oferta-<data>.md` și linia în `casa.md`. Pe un perete sau pe selecția omului: `subgrupe=` / `doar_selectia=True`.
3. Citești rezultatul **cu omul**: rândurile fără preț (apar, dar nu intră în total: manopera, tâmplăria, geamul…) sunt lista lui de
   completat; pierderea la croit; ce nu intră în cantități (goluri, învelișuri). Apoi îmbraci cifrele în formatul firmei (§3).

**B. Fără model (cerere, schiță, poze).** Nu inventezi cantități. Faci **studiul de volum**: din schiță și din ce a spus clientul scoți
suprafețele pe niveluri, înălțimile, forma acoperișului, sistemul constructiv potrivit (de ce), și **împarți clar ce e sigur de ce e
presupus**. Cantitățile ies ca intervale sau ca indici ai firmei (m³ de lemn / m² construit, din ofertele-model — doar dacă există acolo),
cu sursa fiecărui indice. Titlul: **„Studiu de volum și ofertă orientativă”**, niciodată „proiect” sau „ofertă fermă”. Golurile rămân
`[__]`, cu lista lor la final, pentru patron. Când vine modelul, oferta se reface pe drumul A, cu versiune nouă, datată.

## 3. Cum arată oferta (dacă firma n-are format, ăsta e cel implicit)

1. **Antet:** firma, clientul, obiectul (ce construim, unde), numărul lucrării (`AAAA-NNN`), data, valabilitatea ofertei.
2. **Ce cuprinde** — pe capitole, în ordinea construcției: structura (pe sortimente sau pe ansambluri: pereți, planșee, acoperiș), panouri și
   izolații, tâmplărie, învelitoare, montaj, transport. La fiecare capitol: cantitatea **cu sursa ei** („din model, 8 nov 2026” / „din schiță,
   estimat” / „de la client”), prețul unitar din lista firmei, valoarea.
3. **Ce NU cuprinde** — scris la fel de clar: fundația, racordurile, proiectul de arhitectură / structură, autorizațiile, finisajele… (ce
   exclude firma de obicei, din ofertele-model). Aici se pierd cei mai mulți bani la casele din lemn, deci capitolul ăsta nu lipsește niciodată.
4. **Total** fără TVA, TVA 21 %, total cu TVA. Dacă oferta e orientativă: intervalul și ce îl face să varieze.
5. **Termene și plată:** din ofertele-model; dacă nu sunt acolo, `[__]`.
6. **Ce urmează** — un singur pas concret pentru client (vizita pe teren, proiectul, avansul), cum face firma de obicei.
7. **Pentru patron, separat de ofertă:** lista golurilor `[__]` și a presupunerilor de verificat, numerotată, scurtă.

Numere cu virgulă zecimală (în română), prețurile pe unitatea reală (lei/m³, lei/m², lei/buc), unitățile scrise. Limba clientului (RO /
DE / FR / IT / EN, după cererea lui); termenii tehnici ai limbii lui, nu traduceri de dicționar. Tonul firmei (din ofertele-model), direct,
fără formule de marketing și fără adjective despre noi.

## 4. Verificări înainte s-o dai omului

- Fiecare cifră are sursă: model / listă de prețuri / client / estimare marcată. Una fără sursă = o scoți sau o marchezi `[__]`.
- Totalul e suma capitolelor; TVA 21 % (România, 2026). Ai verificat adunarea.
- Rândurile fără preț sunt vizibile și **nu** sunt în total; oferta o spune.
- Capitolul „ce nu cuprinde” există.
- Nicio promisiune de termen, certificare, performanță (nZEB, clasă energetică, rezistență la foc) pe care firma n-a făcut-o în scris.
- Nicio cifră despre alți clienți ai firmei.

## 5. Ce NU faci

- Nu inventezi prețuri, cantități, termene, certificări. Golul se marchează, nu se umple.
- Nu trimiți oferta: o scrii, o pui în `2-oferta/` (cu `dosar=`, sau îi dai textul omului să-l salveze acolo) și o citești cu patronul; **el
  semnează** și o trimite. Emailul care o însoțește e alt skill (emailul către client).
- Nu numești „proiect” ce a ieșit dintr-o schiță.
- Nu copiezi prețurile de referință din pachet ca și cum ar fi ale firmei.
- Nu schimbi modelul din cadwork pentru ofertă. Oferta citește.

## 6. În dosarul casei

Oferta intră în `2-oferta/oferta-<data>.md` (versiune nouă la fiecare refacere; nimic suprascris), studiul de volum în
`2-oferta/studiu-volum-<data>.md`, iar în `casa.md` linia etapei 2 spune: data, fișierul, totalul cu TVA, „de semnat de om înainte să plece”.
Răspunsul clientului, când vine, tot în `2-oferta/`, cu data, și o linie nouă în istoric. Când oferta e acceptată, etapa 3 (contractul) începe.

## 7. Exemplu (jurnalul de bord, 6–8 nov 2026, modelul-exemplu cadwork `Blockbau-Testdatei.3d`, prețuri ORIENTATIVE)

Peretele EG18, selectat de om în cadwork → `cadwork_oferta(doar_selectia=True, client="Proba")`: 25 de bârne în 4 sortimente pe bare de 4/5/6 m,
2,311 m³ de comandat, 7.394 lei materiale, **10.803 lei cu TVA**, pierdere la croit 13,9 % (pe un perete singur e mare; pe toată casa scade la
3–5 %). Toată casa: 323.403 lei materiale, 472.516 lei cu TVA, **4 materiale fără preț semnalate** (stejar, aluminiu, geam, manoperă) — lista
patronului de completat. Oferta a intrat în `2-oferta/oferta-2026-11-08.md`, cu linia în `casa.md`: „oferta orientativă din model pentru Proba,
total … lei cu TVA — de semnat de om înainte să plece”.
