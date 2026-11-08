# Punte — Claude lucrează în cadwork 3D, pe abonamentul tău

**Punte** leagă Claude (Claude Desktop sau Claude Code, pe contul tău) de modelul deschis în **cadwork 3D 2026**, pe calculatorul tău,
și pune deasupra câteva lucruri de meserie: lista de materiale gata de comandă, oferta de preț, verificările pe model.
Îi spui lui Claude „scoate-mi lista de comandă pentru peretele ăsta” și o ai în câteva secunde, din model, cu fișierul pentru depozit.

Un proiect al **[RDL.Network](https://rdl.network)** (Revista din Lemn · Holzindustrie Magazin · Rivista in Legno · European Wood Review),
întreținut de echipa noastră de AI. Independent de cadwork și de Anthropic. Licență MIT. [English](README.en.md) · [Deutsch](README.de.md) · [Italiano](README.it.md)

> **Stare: v0, 8 noiembrie 2026.** Testat viu pe un singur calculator (Windows 11, cadwork 3D 2026 build 385, Claude Desktop + Claude Code),
> pe modelele-exemplu livrate cu cadwork și pe modele mici. Nu l-am rulat încă pe proiectul real al unui birou. Dacă ești primul, spune-ne ce ai găsit.

## Ce poți cere

Cu cadwork deschis și puntea pornită, în Claude Desktop:

| Spui | Ce se întâmplă |
|---|---|
| „Ce e în modelul ăsta?” | Lista elementelor pe categorii: ecarisat, panouri, feronerie, altele; sortimente, lungimi, volume. |
| „Lista de comandă pentru toată casa, pe bare de 4, 5 și 6 m” | Sortimentele (material + secțiune), croiala pe lungimile depozitului tău, bare de comandat, m³, pierderea la croit, panourile în m². Fișier `.md` + `.csv` pentru Excel. |
| „Doar peretele pe care l-am selectat” | Selecția ta din cadwork e „degetul care arată”: un perete selectat ca obiect se desface singur în piesele lui. |
| „Fă-mi oferta pentru structura asta” | Lista de comandă × fișierul tău de prețuri → materiale, transport, manoperă, regie, TVA, total. Prețurile livrate cu pachetul sunt **orientative** (din liste publice, cu sursa și data pe fiecare rând); le înlocuiești cu ale tale. |
| „Verifică modelul: ce lipsește, ce nu se leagă?” | Lemn fără material / nume / perete, secțiuni rare la 1–5 mm de una standard, piese prea lungi, resturi uitate; dubluri exacte, piese care nu ating nimic, coliziuni. Pe trei niveluri: de corectat / de verificat / în regulă. |
| „Arată-mi dublurile în model” | Claude selectează piesele găsite în fereastra ta cadwork și face zoom pe ele — după ce apeși **Da** în cadwork. |
| „Ce am schimbat în model de azi-dimineață?” | Amprenta modelului salvată ca reper; diff-ul: creat / șters / modificat, câmp cu câmp, inclusiv mutările. |
| „Pune o grindă 120×240 de 4 m la cota…” | Claude scrie codul cwapi3d; cadwork îți arată un dialog **Da / Nu** cu descrierea; rulează doar la Da; intră în undo (Ctrl+Z). |

## Cum e gândită siguranța

Modelul e al tău. Puntea are **trei moduri**, într-un fișier text (`%USERPROFILE%\cadwork-punte\mod.txt`):

- **citire** — Claude doar citește. Codul trece printr-o gardă (fără create / set / delete), iar modelul e comparat înainte și după: orice schimbare e anulată.
- **întreabă** (implicit) — orice cod care poate modifica modelul deschide un dialog nativ Da / Nu în fereastra cadwork, cu descrierea jobului. Nimic nu rulează fără clickul tău.
- **liber** — rulează pe loc; fiecare job lasă un rând în bara cadwork.

Claude poate trece singur spre un mod **mai strict**; spre unul mai liber trece **doar cu Da-ul tău în cadwork**. Orice job se întoarce cu
„ce s-a schimbat în model” (creat / șters / modificat), elementele create intră în undo, iar ultimul job poate fi anulat dintr-o comandă.
Puntea ascultă doar pe calculatorul tău (`127.0.0.1`); nimic nu pleacă pe internet în afară de conversația ta cu Claude.

## Instalare (Windows, cadwork 3D 2026, ~10 minute)

Ai nevoie de: cadwork 3D 2026 instalat; [Claude Desktop](https://claude.ai/download) cu un abonament care permite conectori (Pro sau mai sus);
[Python 3.10+](https://www.python.org/downloads/) pentru server (cel încorporat în cadwork e folosit de pluginuri, nu trebuie să faci nimic cu el).

1. Descarcă pachetul (Code → Download ZIP) și dezarhivează-l într-un folder care rămâne pe loc, de exemplu `C:\Punte`.
2. În folderul acela: `python instaleaza.py`. Instalatorul copiază cele două pluginuri în profilul cadwork, pune pachetul Python `mcp`,
   înscrie serverul `punte-cadwork` în Claude Desktop (cu copie de siguranță a configurației) și în Claude Code, dacă îl ai.
3. Repornește Claude Desktop.
4. Deschide cadwork 3D cu modelul tău. În **Window → User Plugins** apasă o dată **`punte_viu_rdl`**: puntea e pornită cât e deschis modelul
   (în bara cadwork apare un rând). Fiecare fereastră cadwork = altă punte; apasă în fereastra modelului la care lucrezi.
5. În Claude Desktop: „Ce e în modelul din cadwork?”. Dacă răspunde cu lista, ești gata.

Fără puntea vie merge și **calea cu buton**: Claude scrie jobul, tu apeși `punte_rdl` în cadwork, rezultatul se întoarce. Dezinstalare: `python instaleaza.py --scoate`.

## Ce e în pachet

| Fișier | Ce e |
|---|---|
| `instaleaza.py` | instalatorul / dezinstalatorul |
| `server_punte_rdl.py` | serverul MCP `punte-cadwork` (Python 3.10+, pachetul `mcp`): uneltele pe care le vede Claude |
| `punte_viu_rdl.py` | pluginul rezident din cadwork (puntea vie): moduri, selecție, amprentă, joburi |
| `punte_rdl.py` | pluginul cu buton (rezerva) |
| `lista_comanda.py` · `oferta.py` · `verificari.py` | logica de meserie, funcții pure (merg și offline, pe un export al listei) |
| `preturi-referinta.csv` | prețuri orientative din liste publice (RO, noiembrie 2026), cu sursa și data pe rând; șablon pentru lista ta |
| `ruleaza_fisier.py` · `test_viu.py` | unelte de test: un fișier de cod prin punte; clientul de test al punții vii |
| `skills/` | skill-uri pentru Claude: cum se face lista de materiale, cum se citesc verificările pe model |

Cerințe: Windows 10/11, cadwork 3D 2026 (API cwapi3d; alte versiuni netestate), Python 3.10+ pentru server. Puntea folosește doar funcții documentate public în cwapi3d.

## Ce NU e

- **Nu e un produs cadwork** și nu e platforma Cadwork.ai / AiBridge a cadwork. E o punte independentă, mică, înlocuibilă; când platforma lor
  e disponibilă pe licența ta, folosește-o — skill-urile de meserie de aici merg peste orice punte.
- **Nu proiectează în locul tău.** Verificările spun ce e *neobișnuit* în model, nu ce e greșit în proiect. Dimensionarea, îmbinările,
  normativele rămân ale proiectantului. Oferta e o foaie de calcul, nu o promisiune.
- **Nu e asistență cu termen.** Suportul e public, pe GitHub (Issues), când putem.

## Programul „Claude în atelier”

Pachetul e gratuit și întreg. Pentru birourile care vor mai mult — o zi la firmă (instalare, cele cinci sarcini pe cazurile voastre, puntea după prânz),
apoi două săptămâni cu o oră online; skill-uri adaptate biroului; actualizări la fiecare versiune cadwork — există programul **„Claude în atelier”**,
al Revistei din Lemn. În România prin [Hub-ul Lemnului](https://hublemn.ro); în afară, direct: **dan.radu@rdl.network**.

## Mulțumiri și mărci

cadwork și cadwork 3D sunt mărci ale cadwork informatik CI AG; Claude e marcă a Anthropic, PBC. Mulțumim cadwork România pentru licența de testare
și echipei cadwork pentru documentația publică a API-ului (`cwapi3d`). Acest proiect nu e afiliat, susținut sau aprobat de cadwork ori de Anthropic.

Licență: [MIT](LICENSE). Istoricul versiunilor: [ISTORIC.md](ISTORIC.md).
