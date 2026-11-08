# Istoric

Versiunile pachetului „Punte”. Datele sunt ale zilelor în care fiecare lucru a fost **testat viu**, cu cadwork 3D deschis și un om la tastatură.

## v0 — 8 noiembrie 2026 (prima asamblare publică)

Testat pe Windows 11, cadwork 3D 2026 (33, build 385 raportat prin API), Python 3.14 încorporat în cadwork, Python 3.12 pentru server, Claude Desktop și Claude Code.

- **Puntea vie** (`punte_viu_rdl`): pluginul rămâne în cadwork după un click și execută cererile lui Claude pe loc. Moduri de permisiune
  în `mod.txt`: *citire* (doar citește, orice schimbare e anulată), *întreabă* (implicit; orice modificare cere un Da în fereastra cadwork),
  *liber*. Claude se poate restrânge singur; se eliberează doar cu Da-ul omului. Orice job se întoarce cu „ce s-a schimbat în model”.
- **Puntea cu buton** (`punte_rdl`): rezerva — Claude scrie jobul, omul apasă, rezultatul se întoarce.
- **Selecția din chat**: ce selectează omul în cadwork e „degetul care arată”; în codul rulat prin punte, lista `SELECTIE`.
- **Amprenta și diff-ul modelului**: „ce ai schimbat tu în model de la reperul X?”
- **Lista de materiale gata de comandă**: sortimente, croială pe lungimi comerciale, bare de comandat, m³, pierdere la croit, panouri în m²; `.md` + `.csv`.
- **Oferta de preț**: lista de comandă × fișierul de prețuri (prețurile livrate sunt orientative, din liste publice, cu sursa și data pe rând; rândurile fără preț nu intră în total).
- **Verificările pe model**: ce lipsește (material, nume, subgrupă, secțiuni rare, piese prea lungi, degenerate) și ce nu se leagă
  (dubluri exacte, piese care nu ating nimic, coliziuni) — doar între piese de lemn; piesele găsite pot fi selectate în cadwork cu Da-ul omului.
- **Instalatorul** (`instaleaza.py`) pentru un calculator Windows cu cadwork 2026 și Claude Desktop.
- **Skill-uri** pentru Claude: lista de materiale, verificările pe model.

Ce nu e încă aici: emailul către client din ofertă, corespondența de export, raportul de șantier; documentația în germană și italiană.
