# Punte — Claude lavora dentro cadwork 3D, sul tuo abbonamento

**Punte** (in romeno *ponte*) collega Claude (Claude Desktop o Claude Code, sul tuo account) al modello aperto in **cadwork 3D 2026**
sul tuo computer, e ci mette sopra qualche cosa del mestiere: la lista materiali pronta per l'ordine, l'offerta di prezzo, le verifiche sul modello.
Dici a Claude «dammi la lista d'ordine per questa parete» e ce l'hai in pochi secondi, dal modello, con il file per il fornitore.

Un progetto di **[RDL.Network](https://rdl.network)** (Rivista in Legno · Revista din Lemn · Holzindustrie Magazin · European Wood Review),
mantenuto dal nostro team AI. Indipendente da cadwork e da Anthropic. Licenza MIT. [English](README.en.md) · [Română](README.md)

> **Stato: v0, 8 novembre 2026.** Provato dal vivo su un solo computer (Windows 11, cadwork 3D 2026 build 385, Claude Desktop + Claude Code),
> sui modelli di esempio forniti con cadwork e su modelli piccoli. Non ancora su un progetto vero di studio. Se sei il primo, dicci cosa hai trovato.
> I nomi degli strumenti e i messaggi in v0 sono in romeno; Claude ti risponde comunque nella tua lingua.

## Cosa puoi chiedere

Con cadwork aperto e il ponte avviato, in Claude Desktop:

| Dici | Cosa succede |
|---|---|
| «Cosa c'è in questo modello?» | Gli elementi per categoria: legno squadrato, pannelli, ferramenta, altro; assortimenti, lunghezze, volumi. |
| «Lista d'ordine per tutta la casa, su barre da 4, 5 e 6 m» | Assortimenti (materiale + sezione), taglio sulle lunghezze di magazzino del tuo fornitore, barre da ordinare, m³, sfrido, pannelli in m². Un `.md` + un `.csv` per Excel. |
| «Solo la parete che ho selezionato» | La tua selezione in cadwork è il dito che indica: una parete selezionata come oggetto si scompone da sola nei suoi pezzi. |
| «Fammi l'offerta per questa struttura» | Lista d'ordine × il tuo file prezzi → materiali, trasporto, manodopera, spese generali, IVA, totale. I prezzi forniti con il pacchetto sono **indicativi** (listini pubblici, con fonte e data su ogni riga); sostituiscili con i tuoi. |
| «Verifica il modello: cosa manca, cosa non si lega?» | Legno senza materiale / nome / parete, sezioni rare a 1–5 mm da una standard, pezzi troppo lunghi, ritagli dimenticati; duplicati esatti, pezzi che non toccano nulla, collisioni. Tre livelli: da correggere / da verificare / a posto. |
| «Mostrami i duplicati nel modello» | Claude seleziona i pezzi trovati nella tua finestra cadwork e ci fa zoom — dopo che premi **Sì** in cadwork. |
| «Cosa ho cambiato nel modello da stamattina?» | Un'impronta del modello salvata come riferimento; il diff: creato / cancellato / modificato, campo per campo, spostamenti compresi. |
| «Metti una trave 120×240 da 4 m a quota…» | Claude scrive il codice cwapi3d; cadwork ti mostra una finestra nativa **Sì / No** con la descrizione; gira solo al Sì; entra nell'undo (Ctrl+Z). |

## Il fascicolo della casa: una cartella per commessa

Tutto quello che esce dagli strumenti può entrare direttamente nel **fascicolo della casa** (*dosarul casei*): una cartella per commessa, stessa struttura
ovunque, file semplici. `cadwork_dosar_nou` crea `1-cerere/ 2-oferta/ 3-contract/ 4-proiect/ 5-comenzi/ 6-productie/ 7-montaj/ 8-receptie/ corespondenta/`
(richiesta, offerta, contratto, progetto, ordini, produzione, montaggio, consegna, corrispondenza) più `casa.md` («a che punto siamo»: cliente, cosa
costruiamo, stato per fase, prossimo passo). Con `dosar=<cartella>`, lista d'ordine, offerta e verifiche finiscono datate nella loro fase, ciascuna con
una riga in `casa.md`. Nulla viene sovrascritto. Oggi la cartella sta sul tuo computer, domani può stare su una cartella condivisa senza cambiare nulla.
La regola in tutte le fasi: Claude scrive, la persona firma.

## Com'è pensata la sicurezza

Il modello è tuo. Il ponte ha **tre modalità**, in un file di testo (`%USERPROFILE%\cadwork-punte\mod.txt`):

- **citire** (lettura) — Claude legge soltanto. Il codice passa una guardia (niente create / set / delete) e il modello è confrontato prima e dopo: ogni cambiamento è annullato.
- **intreaba** (chiedi, predefinita) — ogni codice che può modificare il modello apre una finestra nativa Sì / No in cadwork, con la descrizione del lavoro. Senza il tuo clic non gira nulla.
- **liber** (libero) — gira subito; ogni lavoro lascia una riga nella barra di stato di cadwork.

Claude può passare da solo a una modalità **più stretta**; a una più libera **solo con il tuo Sì in cadwork**. Ogni lavoro torna con
«cosa è cambiato nel modello» (creato / cancellato / modificato), gli elementi creati entrano nell'undo e l'ultimo lavoro si annulla con un comando.
Il ponte ascolta solo sul tuo computer (`127.0.0.1`); nulla esce dal computer tranne la tua conversazione con Claude.

## Installazione (Windows, cadwork 3D 2026, ~10 minuti)

Ti servono: cadwork 3D 2026 installato; [Claude Desktop](https://claude.ai/download) con un piano che permette i connettori (Pro o superiore);
[Python 3.10+](https://www.python.org/downloads/) per il server (il Python incorporato in cadwork lo usano i plugin; lì non devi fare nulla).

1. Scarica il pacchetto (Code → Download ZIP) e scompattalo in una cartella che resta ferma, per esempio `C:\Punte`.
2. In quella cartella: `python instaleaza.py`. L'installatore copia i due plugin nel profilo cadwork, installa il pacchetto Python `mcp`,
   registra il server `punte-cadwork` in Claude Desktop (con copia di sicurezza della configurazione) e in Claude Code, se c'è.
3. Riavvia Claude Desktop.
4. Apri cadwork 3D con il tuo modello. In **Window → User Plugins** premi una volta **`punte_viu_rdl`**: il ponte è vivo finché il modello è aperto
   (nella barra di cadwork compare una riga). Ogni finestra cadwork è un ponte a sé; premi nella finestra del modello su cui lavori.
5. In Claude Desktop: «Cosa c'è nel modello di cadwork?». Se risponde con la lista, sei pronto.

Senza il ponte vivo c'è anche la **via col pulsante**: Claude scrive il lavoro, tu premi `punte_rdl` in cadwork, il risultato torna. Disinstallazione: `python instaleaza.py --scoate`.

## Cosa c'è nel pacchetto

| File | Cos'è |
|---|---|
| `instaleaza.py` | installatore / disinstallatore |
| `server_punte_rdl.py` | il server MCP `punte-cadwork` (Python 3.10+, pacchetto `mcp`): gli strumenti che Claude vede |
| `punte_viu_rdl.py` | il plugin residente in cadwork (ponte vivo): modalità, selezione, impronta, lavori |
| `punte_rdl.py` | il plugin col pulsante (riserva) |
| `lista_comanda.py` · `oferta.py` · `verificari.py` | la logica del mestiere, funzioni pure (girano anche offline, su una lista esportata) |
| `preturi-referinta.csv` | prezzi indicativi da listini pubblici (Romania, novembre 2026), fonte e data per riga; modello per la tua lista |
| `ruleaza_fisier.py` · `test_viu.py` | strumenti di prova: un file di codice attraverso il ponte; il client di prova del ponte vivo |
| `skills/` | skill per Claude: come si fa la lista materiali, come si leggono le verifiche sul modello, come si scrive l'offerta della casa (dal modello o dalla richiesta, con i vuoti segnati), come si risponde all'email di un cliente (nel suo thread, solo su ciò che ha scritto, un passo successivo), come si scrive il rapporto di cantiere (una pagina da foto e appunti: fatto / prossimo / serve dal cliente), come si risponde alla corrispondenza estera (DE / FR / IT / EN, termini tecnici corretti, ritraduzione per il titolare) (romeno) |

Requisiti: Windows 10/11, cadwork 3D 2026 (API cwapi3d; altre versioni non provate), Python 3.10+ per il server. Il ponte usa solo funzioni cwapi3d documentate pubblicamente.

## Cosa NON è

- **Non è un prodotto cadwork** e non è la piattaforma Cadwork.ai / AiBridge di cadwork. È un ponte indipendente, piccolo e sostituibile; quando la loro
  piattaforma è disponibile sulla tua licenza, usala — gli skill del mestiere qui funzionano sopra qualunque ponte.
- **Non progetta al posto tuo.** Le verifiche dicono cosa è *insolito* nel modello, non cosa è sbagliato nel progetto. Dimensionamento, giunti,
  normative restano del progettista. L'offerta è un foglio di calcolo, non una promessa.
- **Niente assistenza con scadenze.** Il supporto è pubblico, su GitHub (Issues), quando possiamo.

## Il programma «Claude în atelier» (Claude in officina)

Il pacchetto è gratuito e completo. Per gli studi che vogliono di più — una giornata in azienda (installazione, i cinque compiti sui vostri casi, il ponte
dopo pranzo), poi due settimane con un'ora online; skill adattati allo studio; aggiornamenti a ogni versione cadwork — c'è il programma
**«Claude în atelier»** della Revista din Lemn. Per l'Italia: **dan.radu@rdl.network** (italiano o inglese).

## Ringraziamenti e marchi

cadwork e cadwork 3D sono marchi di cadwork informatik CI AG; Claude è un marchio di Anthropic, PBC. Grazie a cadwork Romania per la licenza di prova
e al team cadwork per la documentazione pubblica dell'API (`cwapi3d`). Questo progetto non è affiliato, sostenuto o approvato da cadwork né da Anthropic.

Licenza: [MIT](LICENSE). Storia delle versioni: [ISTORIC.md](ISTORIC.md) (romeno).
