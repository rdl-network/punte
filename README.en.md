# Punte — Claude works inside cadwork 3D, on your own subscription

**Punte** (Romanian for *bridge*) connects Claude (Claude Desktop or Claude Code, on your account) to the model open in **cadwork 3D 2026**
on your computer, and adds a few things from the trade on top: the order-ready material list, the price offer, the model checks.
You tell Claude "give me the order list for this wall" and you have it in seconds, from the model, with the file for your supplier.

A project by **[RDL.Network](https://rdl.network)** (Revista din Lemn · Holzindustrie Magazin · Rivista in Legno · European Wood Review),
maintained by our AI team. Independent of cadwork and of Anthropic. MIT license. [Română](README.md) · [Deutsch](README.de.md) · [Italiano](README.it.md)

> **Status: v0, 8 November 2026.** Tested live on a single machine (Windows 11, cadwork 3D 2026 build 385, Claude Desktop + Claude Code),
> on the sample models shipped with cadwork and on small models. Not yet run on a real office project. If you are the first, tell us what you found.
> Documentation in Romanian, English, German and Italian.

## What you can ask

With cadwork open and the bridge started, in Claude Desktop:

| You say | What happens |
|---|---|
| "What is in this model?" | Elements by category: solid timber, panels, hardware, other; sorts, lengths, volumes. |
| "Order list for the whole house, on 4, 5 and 6 m bars" | Sorts (material + section), cutting on your supplier's stock lengths, bars to order, m³, cutting loss, panels in m². A `.md` + a `.csv` for Excel. |
| "Only the wall I selected" | Your selection in cadwork is the pointing finger: a wall selected as an object unfolds into its pieces. |
| "Make me the offer for this structure" | Order list × your price file → materials, transport, labour, overhead, VAT, total. The prices shipped with the package are **indicative** (public lists, with source and date on every row); replace them with yours. |
| "Check the model: what is missing, what does not connect?" | Timber without material / name / wall, rare sections 1–5 mm off a standard one, over-length pieces, forgotten offcuts; exact duplicates, pieces touching nothing, collisions. Three levels: to fix / to check / fine. |
| "Show me the duplicates in the model" | Claude selects the found pieces in your cadwork window and zooms on them — after you press **Yes** in cadwork. |
| "What did I change in the model since this morning?" | A model fingerprint saved as a reference; the diff: created / deleted / modified, field by field, moves included. |
| "Put a 120×240 beam, 4 m long, at…" | Claude writes the cwapi3d code; cadwork shows you a native **Yes / No** dialog with the description; it runs only on Yes; it goes into undo (Ctrl+Z). |

## The house file: one folder per job

Everything the tools produce can go straight into the **house file** (*dosarul casei*): one folder per job, same structure everywhere, plain files.
"Make the file for the Popescu house" → `cadwork_dosar_nou` creates `1-cerere/ 2-oferta/ 3-contract/ 4-proiect/ 5-comenzi/ 6-productie/
7-montaj/ 8-receptie/ corespondenta/` (request, offer, contract, design, orders, production, assembly, hand-over, correspondence) + `casa.md`
("where we are": client, what we build, stage by stage, next step). Then, with `dosar=<folder>`, the order list goes to `5-comenzi/`, the offer
to `2-oferta/`, the model checks to `4-proiect/`, each dated and each with a line at its stage in `casa.md`. Nothing is overwritten (a second
version on the same day gets the time). "Where are we with the Popescu house?" → Claude reads `casa.md`. Today the folder sits on your machine;
tomorrow it can sit on a shared folder, with nothing to change. The rule across all stages: Claude writes, the person signs.

## How safety is designed

The model is yours. The bridge has **three modes**, in a text file (`%USERPROFILE%\cadwork-punte\mod.txt`):

- **citire** (read) — Claude only reads. The code passes a guard (no create / set / delete) and the model is compared before and after: any change is reverted.
- **intreaba** (ask, default) — any code that may modify the model opens a native Yes / No dialog in the cadwork window, with the job description. Nothing runs without your click.
- **liber** (free) — runs at once; every job leaves a line in the cadwork status bar.

Claude may switch itself to a **stricter** mode on its own; to a freer one **only with your Yes in cadwork**. Every job comes back with
"what changed in the model" (created / deleted / modified), created elements go into undo, and the last job can be reverted with one command.
The bridge listens only on your machine (`127.0.0.1`); nothing leaves your computer except your conversation with Claude.

## Install (Windows, cadwork 3D 2026, ~10 minutes)

You need: cadwork 3D 2026 installed; [Claude Desktop](https://claude.ai/download) on a plan that allows connectors (Pro or above);
[Python 3.10+](https://www.python.org/downloads/) for the server (the Python embedded in cadwork is used by the plugins; nothing to do there).

1. Download the package (Code → Download ZIP) and unzip it into a folder that stays put, e.g. `C:\Punte`.
2. In that folder: `python instaleaza.py`. The installer copies the two plugins into the cadwork profile, installs the Python package `mcp`,
   registers the `punte-cadwork` server in Claude Desktop (backing up your config first) and in Claude Code if present.
3. Restart Claude Desktop.
4. Open cadwork 3D with your model. In **Window → User Plugins** click **`punte_viu_rdl`** once: the bridge is alive while the model is open
   (a line appears in the cadwork status bar). Each cadwork window is its own bridge; click in the window of the model you work on.
5. In Claude Desktop: "What is in the cadwork model?". If it answers with the list, you are set.

Without the live bridge there is also the **button path**: Claude writes the job, you click `punte_rdl` in cadwork, the result comes back. Uninstall: `python instaleaza.py --scoate`.

## What is in the package

| File | What it is |
|---|---|
| `instaleaza.py` | installer / uninstaller |
| `server_punte_rdl.py` | the `punte-cadwork` MCP server (Python 3.10+, package `mcp`): the tools Claude sees |
| `punte_viu_rdl.py` | the resident cadwork plugin (live bridge): modes, selection, fingerprint, jobs |
| `punte_rdl.py` | the button plugin (fallback) |
| `lista_comanda.py` · `oferta.py` · `verificari.py` | the trade logic, pure functions (they also work offline, on an exported list) |
| `preturi-referinta.csv` | indicative prices from public lists (Romania, November 2026), source and date per row; a template for your own list |
| `ruleaza_fisier.py` · `test_viu.py` | test tools: a code file through the bridge; the live bridge test client |
| `skills/` | skills for Claude: how to build the material list, how to read the model checks, how to write the house offer (from the model or from the request, gaps marked) (Romanian) |

Requirements: Windows 10/11, cadwork 3D 2026 (cwapi3d API; other versions untested), Python 3.10+ for the server. The bridge uses only publicly documented cwapi3d functions.
Tool names and messages are in Romanian in v0; Claude answers you in your language regardless.

## What it is NOT

- **Not a cadwork product**, and not cadwork's Cadwork.ai / AiBridge platform. It is an independent bridge, small and replaceable; when their
  platform is available on your license, use it — the trade skills here work over any bridge.
- **It does not design for you.** The checks say what is *unusual* in the model, not what is wrong in the design. Sizing, joints,
  codes stay with the designer. The offer is a spreadsheet, not a promise.
- **No support with deadlines.** Support is public, on GitHub (Issues), when we can.

## The "Claude in the workshop" programme

The package is free and complete. For offices that want more — a day at your company (install, the five tasks on your own cases, the bridge
after lunch), then two weeks with an hour online; skills adapted to the office; updates at every cadwork version — there is the
**"Claude în atelier"** programme of Revista din Lemn. Contact: **dan.radu@rdl.network**.

## Credits and trademarks

cadwork and cadwork 3D are trademarks of cadwork informatik CI AG; Claude is a trademark of Anthropic, PBC. Thanks to cadwork Romania for the test
license and to the cadwork team for the public API documentation (`cwapi3d`). This project is not affiliated with, endorsed or supported by cadwork or Anthropic.

License: [MIT](LICENSE). Version history: [ISTORIC.md](ISTORIC.md) (Romanian).
