---
name: emailul-catre-client
description: Răspunsul atelierului la emailul unui client (sau primul email către el), în tonul firmei, pe firul lui, în limba lui — din firul de corespondență + ce vrea patronul să-i spună, în două propoziții. Folosește-o când omul cere „răspunde-i lui X”, „scrie-i clientului că…”, „trimite-i oferta”, „ce-i zic la întrebarea asta”, „a întârziat livrarea, cum îi spun”.
---

# Emailul către client

Sarcina 2 a programului „Claude în atelier” (Revista din Lemn / Hub-ul Lemnului). Scopul: patronul citește emailul clientului, îți spune în
două propoziții ce vrea să-i răspundă, și în două minute are răspunsul gata de trimis, în tonul lui, cu un singur pas clar la final.
**Claude scrie, omul trimite.** Niciun email nu pleacă din acest skill.

## 1. Ce primești și de unde

| Ce | De unde |
|---|---|
| **Firul de corespondență** cu clientul (tot, nu doar ultimul email) | atașat de om, sau `corespondenta/` din dosarul casei |
| **Ce vrea să-i spună**, în două propoziții, cu cuvintele lui | omul, în chat |
| **Tonul firmei** | Proiectul firmei: un email bun de-al patronului, ofertele-model; textul Proiectului („ton direct, tehnic, fără formule de marketing”) |
| **Faptele casei** | dosarul casei: `casa.md` (unde suntem), `2-oferta/` (ce i-am oferit), `3-contract/` (termene, plăți), `7-montaj/` (ultimul raport) |

Dacă lipsește firul, ceri firul. Dacă lipsesc „cele două propoziții”, întrebi o dată: „Ce vrei să-i spui, pe scurt?” Nu ghicești poziția firmei.

## 2. Regulile răspunsului (puține, ținute)

1. **Strict despre ce a scris el.** Răspunzi la emailul lui, la întrebările lui, în ordinea lui. Nu adaugi oferte, noutăți, „apropo”-uri, PS.
   Dacă patronul vrea să mai spună ceva ce nu are legătură, e alt email.
2. **Pe firul lui**, cu „Re:” la subiectul lui. Nu mesaj nou. Deschiderea arată că l-ai citit: reiei în câteva cuvinte ce a cerut sau ce a spus,
   nu „Vă mulțumim pentru mesaj”.
3. **Limba lui, termenii lui.** Clientul scrie în română / germană / franceză / italiană / engleză → răspunsul în aceeași limbă, cu termenii
   de meserie ai limbii lui (nu traduceri de dicționar). Pentru export, skill-ul „corespondența de export” are regulile tehnice.
4. **Un singur pas la final, de la el sau de la noi, cu dată.** „Vă propun să ne vedem pe teren joi sau vineri, spuneți-mi care vă convine.”
   Fără „nu e nicio grabă”, fără „rămân la dispoziție”, fără „cine decide la dumneavoastră”.
5. **Fapte, nu adjective.** Nimic despre „calitatea noastră”, „experiența noastră”, „pasiunea noastră”. Ce am făcut, ce facem, când.
6. **Nicio promisiune care nu e în dosar.** Termene, prețuri, certificări, performanțe: doar ce e scris în ofertă / contract. Dacă patronul
   promite ceva nou în cele două propoziții, îl întrebi dacă e sigur, apoi scrii.
7. **Lungimea cât trebuie.** Un răspuns la o întrebare simplă are trei rânduri. O explicație tehnică are cât are. Nu umpli, nu tai.
8. **Semnătura firmei**, cum o are el (nume, funcție, firmă, telefon). Persoana: „dumneavoastră” pentru clienți noi și persoane fizice,
   „tu” doar dacă firul e deja pe „tu”.
9. **Nume reale.** Numele clientului, al colegilor, al furnizorilor — doar cum apar în fir și în dosar. Nu inventezi și nu „corectezi” nume.

## 3. Cele cinci situații ale atelierului

| Situația | Ce conține răspunsul | Capcana |
|---|---|---|
| **Cerere nouă** (primul email al clientului) | ce ai înțeles că vrea (două rânduri); 2–3 întrebări precise care lipsesc pentru ofertă (teren, suprafață, termen, buget dacă nu l-a spus); pasul: o discuție / o vizită, cu zile propuse | să trimiți un chestionar de 12 întrebări; să vorbești despre firmă în loc de casa lui |
| **Trimiterea ofertei** | ce e în ofertă, în trei rânduri (obiectul, totalul cu TVA, valabilitatea); ce NU cuprinde (o propoziție); pasul: când vă putem vedea ca s-o parcurgem | să repeți oferta în email; să te scuzi pentru preț |
| **Obiecție la preț** | ce cuprinde prețul, concret (sistem, materiale, montaj); unde se poate ajusta REAL, din ce face firma (alt sistem, altă finisare, etapizare), fără reducere inventată; pasul | reducerea „din burtă”; comparația cu concurența |
| **Întârziere / problemă pe șantier** | adevărul, de la început (ce s-a întâmplat, de ce); data nouă, fermă, din dosar; ce facem noi până atunci; pasul | eufemisme; vina pe furnizor fără fapte; „ne cerem scuze pentru neplăcerile create” |
| **Client supărat** | recunoști problema lui cu cuvintele lui; faptele, fără apărare; ce facem și când; pasul: un telefon azi / mâine, cu ora | explicații lungi; „vă înțelegem frustrarea”; promisiuni ca să-l liniștești |

## 4. Cum o faci

1. Citești tot firul și `casa.md` (dacă există dosar). Notezi: la ce întrebări trebuie răspuns, în ce limbă, pe ce persoană („tu” / „dumneavoastră”).
2. Iei cele două propoziții ale patronului și le verifici cu dosarul: orice cifră, dată, promisiune are acoperire? Dacă nu, întrebi înainte să scrii.
3. Scrii răspunsul: deschiderea pe ce a scris el → răspunsurile, în ordinea lui → pasul următor cu dată → semnătura. Subiect: „Re: <al lui>”.
4. Îl arăți omului **cu două rânduri deasupra**: ce ai răspuns și ce ai lăsat deoparte (dacă a cerut ceva ce nu e în dosar). El corectează, el trimite.
5. În dosar: `corespondenta/<AAAA-LL-ZZ>-<subiect-scurt>.md` cu emailul primit și răspunsul trimis (versiunea finală, după corecturile lui), și o
   linie în `casa.md` la etapa curentă („2 Ofertă · 11 nov  răspuns la întrebările despre izolație; așteptăm vizita de joi”). Dacă ai unealta
   de fișiere, le scrii tu; dacă nu, îi dai textul și locul.

## 5. Ce NU faci

- Nu trimiți. Nu „programezi” trimiterea. Omul apasă.
- Nu scrii în numele firmei lucruri pe care firma nu le-a decis (reduceri, termene, garanții noi).
- Nu răspunzi la ce n-a întrebat și nu adaugi vânzare la un răspuns de serviciu.
- Nu copiezi formule: „Sperăm că acest email vă găsește bine”, „Nu ezitați să ne contactați”, „Rămânem la dispoziția dumneavoastră”.
- Nu inventezi nume, funcții sau istoric pe care nu le ai în fir.

## 6. Exemplu (cerere nouă, în română; numele sunt locuri goale, pentru format)

> **Re: casă din lemn la [localitate]**
>
> Bună ziua, domnule [Nume],
>
> am citit schița și pozele terenului: casă pe parter și mansardă, cam 120 m², cu acoperiș în două ape, pe un teren în pantă ușoară spre sud. E genul de casă pe care o facem prefabricat, în hală, și o montăm pe fundația gata în câteva zile.
>
> Ca să vă pot trimite o ofertă cu cifre, nu cu intervale, am nevoie de trei lucruri: dacă aveți ridicarea topografică a terenului sau măcar dimensiunile lui; dacă fundația o faceți dumneavoastră sau o cuprindem noi; și până când ați vrea să vă mutați.
>
> Vă propun să ne vedem pe teren săptămâna viitoare, joi 13 sau vineri 14, dimineața. Spuneți-mi care zi vă convine și la ce oră.
>
> [Prenume Nume]
> [Firma] · [localitatea firmei] · [telefon]

Pentru patron: am răspuns la cerere cu trei întrebări și vizita; n-am pomenit prețul (nu l-a întrebat) și nici sistemul exact (vine după vizită).
