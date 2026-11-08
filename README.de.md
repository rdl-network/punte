# Punte — Claude arbeitet in cadwork 3D, auf Ihrem eigenen Abo

**Punte** (rumänisch für *Brücke*) verbindet Claude (Claude Desktop oder Claude Code, auf Ihrem Konto) mit dem in **cadwork 3D 2026**
geöffneten Modell auf Ihrem Rechner und legt ein paar Dinge aus dem Handwerk darüber: die bestellfertige Materialliste, das Preisangebot,
die Modellprüfung. Sie sagen Claude „gib mir die Bestellliste für diese Wand“ und haben sie in Sekunden, aus dem Modell, mit der Datei für den Händler.

Ein Projekt von **[RDL.Network](https://rdl.network)** (Holzindustrie Magazin · Revista din Lemn · Rivista in Legno · European Wood Review),
gepflegt von unserem KI-Team. Unabhängig von cadwork und von Anthropic. MIT-Lizenz. [English](README.en.md) · [Română](README.md)

> **Stand: v0, 8. November 2026.** Live getestet auf einem einzigen Rechner (Windows 11, cadwork 3D 2026 Build 385, Claude Desktop + Claude Code),
> an den mit cadwork gelieferten Beispielmodellen und an kleinen Modellen. Noch nicht an einem echten Büroprojekt. Wenn Sie der Erste sind, sagen Sie uns, was Sie gefunden haben.
> Werkzeugnamen und Meldungen sind in v0 rumänisch; Claude antwortet Ihnen trotzdem in Ihrer Sprache.

## Was Sie fragen können

Mit geöffnetem cadwork und gestarteter Brücke, in Claude Desktop:

| Sie sagen | Was passiert |
|---|---|
| „Was ist in diesem Modell?“ | Elemente nach Kategorie: Schnittholz, Platten, Verbindungsmittel, Sonstiges; Sortimente, Längen, Volumen. |
| „Bestellliste für das ganze Haus, auf 4-, 5- und 6-m-Stangen“ | Sortimente (Material + Querschnitt), Zuschnitt auf die Lagerlängen Ihres Händlers, zu bestellende Stangen, m³, Verschnitt, Platten in m². Eine `.md` + eine `.csv` für Excel. |
| „Nur die Wand, die ich markiert habe“ | Ihre Auswahl in cadwork ist der zeigende Finger: eine als Objekt markierte Wand zerfällt von selbst in ihre Teile. |
| „Mach mir das Angebot für dieses Tragwerk“ | Bestellliste × Ihre Preisdatei → Material, Transport, Lohn, Gemeinkosten, MwSt., Summe. Die mitgelieferten Preise sind **Richtwerte** (öffentliche Listen, Quelle und Datum in jeder Zeile); ersetzen Sie sie durch Ihre. |
| „Prüf das Modell: was fehlt, was hängt nicht zusammen?“ | Holz ohne Material / Name / Wand, seltene Querschnitte 1–5 mm neben einem Standard, Überlängen, vergessene Reststücke; exakte Dubletten, Teile ohne Kontakt, Kollisionen. Drei Stufen: zu korrigieren / zu prüfen / in Ordnung. |
| „Zeig mir die Dubletten im Modell“ | Claude markiert die gefundenen Teile in Ihrem cadwork-Fenster und zoomt darauf — nachdem Sie in cadwork **Ja** gedrückt haben. |
| „Was habe ich seit heute Morgen am Modell geändert?“ | Ein Fingerabdruck des Modells als Referenz; der Diff: erstellt / gelöscht / geändert, Feld für Feld, Verschiebungen inklusive. |
| „Setz einen Balken 120×240, 4 m, bei …“ | Claude schreibt den cwapi3d-Code; cadwork zeigt Ihnen einen nativen **Ja / Nein**-Dialog mit der Beschreibung; läuft nur bei Ja; landet im Undo (Strg+Z). |

## Die Hausakte: ein Ordner pro Auftrag

Alles, was die Werkzeuge erzeugen, kann direkt in die **Hausakte** (*dosarul casei*): ein Ordner pro Auftrag, überall gleich aufgebaut, einfache Dateien.
`cadwork_dosar_nou` legt `1-cerere/ 2-oferta/ 3-contract/ 4-proiect/ 5-comenzi/ 6-productie/ 7-montaj/ 8-receptie/ corespondenta/` an (Anfrage, Angebot,
Vertrag, Planung, Bestellungen, Produktion, Montage, Abnahme, Schriftverkehr) plus `casa.md` („wo wir stehen“: Kunde, was wir bauen, Stand je Phase, nächster
Schritt). Mit `dosar=<Ordner>` landen Bestellliste, Angebot und Modellprüfung datiert in ihrer Phase, jeweils mit einer Zeile in `casa.md`. Nichts wird
überschrieben. Heute liegt der Ordner auf Ihrem Rechner, morgen kann er auf einem gemeinsamen Laufwerk liegen, ohne dass sich etwas ändert. Die Regel
in allen Phasen: Claude schreibt, der Mensch unterschreibt.

## Wie die Sicherheit gedacht ist

Das Modell gehört Ihnen. Die Brücke hat **drei Modi**, in einer Textdatei (`%USERPROFILE%\cadwork-punte\mod.txt`):

- **citire** (lesen) — Claude liest nur. Der Code geht durch eine Sperre (kein create / set / delete), das Modell wird vorher und nachher verglichen: jede Änderung wird zurückgenommen.
- **intreaba** (fragen, Standard) — jeder Code, der das Modell ändern könnte, öffnet einen nativen Ja / Nein-Dialog im cadwork-Fenster, mit der Beschreibung des Jobs. Ohne Ihren Klick läuft nichts.
- **liber** (frei) — läuft sofort; jeder Job hinterlässt eine Zeile in der cadwork-Statusleiste.

Claude darf sich selbst in einen **strengeren** Modus schalten; in einen freieren **nur mit Ihrem Ja in cadwork**. Jeder Job kommt mit
„was sich am Modell geändert hat“ zurück (erstellt / gelöscht / geändert), erstellte Elemente landen im Undo, der letzte Job lässt sich mit einem Befehl zurücknehmen.
Die Brücke hört nur auf Ihrem Rechner (`127.0.0.1`); außer Ihrem Gespräch mit Claude verlässt nichts den Computer.

## Installation (Windows, cadwork 3D 2026, ~10 Minuten)

Sie brauchen: cadwork 3D 2026 installiert; [Claude Desktop](https://claude.ai/download) in einem Plan mit Konnektoren (Pro oder höher);
[Python 3.10+](https://www.python.org/downloads/) für den Server (das in cadwork eingebettete Python nutzen die Plugins; dort ist nichts zu tun).

1. Paket herunterladen (Code → Download ZIP) und in einen Ordner entpacken, der bleibt, z. B. `C:\Punte`.
2. In diesem Ordner: `python instaleaza.py`. Der Installer kopiert die zwei Plugins ins cadwork-Profil, installiert das Python-Paket `mcp`,
   trägt den Server `punte-cadwork` in Claude Desktop ein (mit Sicherung Ihrer Konfiguration) und in Claude Code, falls vorhanden.
3. Claude Desktop neu starten.
4. cadwork 3D mit Ihrem Modell öffnen. Unter **Window → User Plugins** einmal **`punte_viu_rdl`** klicken: die Brücke lebt, solange das Modell offen ist
   (in der cadwork-Statusleiste erscheint eine Zeile). Jedes cadwork-Fenster ist eine eigene Brücke; klicken Sie im Fenster des Modells, an dem Sie arbeiten.
5. In Claude Desktop: „Was ist im cadwork-Modell?“. Antwortet es mit der Liste, sind Sie fertig.

Ohne die lebende Brücke gibt es auch den **Knopf-Weg**: Claude schreibt den Job, Sie klicken `punte_rdl` in cadwork, das Ergebnis kommt zurück. Deinstallation: `python instaleaza.py --scoate`.

## Was im Paket ist

| Datei | Was es ist |
|---|---|
| `instaleaza.py` | Installer / Deinstaller |
| `server_punte_rdl.py` | der MCP-Server `punte-cadwork` (Python 3.10+, Paket `mcp`): die Werkzeuge, die Claude sieht |
| `punte_viu_rdl.py` | das residente cadwork-Plugin (lebende Brücke): Modi, Auswahl, Fingerabdruck, Jobs |
| `punte_rdl.py` | das Knopf-Plugin (Reserve) |
| `lista_comanda.py` · `oferta.py` · `verificari.py` | die Handwerkslogik, reine Funktionen (laufen auch offline, auf einer exportierten Liste) |
| `preturi-referinta.csv` | Richtpreise aus öffentlichen Listen (Rumänien, November 2026), Quelle und Datum je Zeile; Vorlage für Ihre eigene Liste |
| `ruleaza_fisier.py` · `test_viu.py` | Testwerkzeuge: eine Codedatei durch die Brücke; der Testclient der lebenden Brücke |
| `skills/` | Skills für Claude: wie die Materialliste entsteht, wie die Modellprüfung gelesen wird, wie das Hausangebot geschrieben wird (aus dem Modell oder aus der Anfrage, Lücken markiert), wie die E-Mail eines Kunden beantwortet wird (im selben Thread, strikt zu seiner Frage, ein nächster Schritt), wie der Baustellenbericht entsteht (eine Seite aus Fotos und Notizen: erledigt / als Nächstes / vom Kunden benötigt), wie Export-Korrespondenz beantwortet wird (DE / FR / IT / EN, korrekte Fachbegriffe, Rückübersetzung für den Inhaber) (rumänisch) |

Voraussetzungen: Windows 10/11, cadwork 3D 2026 (cwapi3d-API; andere Versionen ungetestet), Python 3.10+ für den Server. Die Brücke nutzt nur öffentlich dokumentierte cwapi3d-Funktionen.

## Was es NICHT ist

- **Kein cadwork-Produkt** und nicht die Plattform Cadwork.ai / AiBridge von cadwork. Eine unabhängige Brücke, klein und ersetzbar; sobald deren
  Plattform auf Ihrer Lizenz verfügbar ist, nutzen Sie sie — die Handwerks-Skills hier laufen über jede Brücke.
- **Es plant nicht für Sie.** Die Prüfungen sagen, was im Modell *ungewöhnlich* ist, nicht, was im Entwurf falsch ist. Bemessung, Verbindungen,
  Normen bleiben beim Planer. Das Angebot ist eine Tabelle, kein Versprechen.
- **Kein Support mit Fristen.** Support ist öffentlich, auf GitHub (Issues), wenn wir können.

## Das Programm „Claude în atelier“ (Claude in der Werkstatt)

Das Paket ist kostenlos und vollständig. Für Büros, die mehr wollen — ein Tag in Ihrer Firma (Installation, die fünf Aufgaben an Ihren Fällen, die Brücke
nach dem Mittag), dann zwei Wochen mit einer Stunde online; auf das Büro zugeschnittene Skills; Updates bei jeder cadwork-Version — gibt es das
Programm **„Claude în atelier“** der Revista din Lemn. Für den deutschsprachigen Raum: **dan.radu@rdl.network** (Englisch oder Deutsch).

## Dank und Marken

cadwork und cadwork 3D sind Marken der cadwork informatik CI AG; Claude ist eine Marke von Anthropic, PBC. Dank an cadwork Rumänien für die Testlizenz
und an das cadwork-Team für die öffentliche API-Dokumentation (`cwapi3d`). Dieses Projekt ist weder mit cadwork noch mit Anthropic verbunden, noch von ihnen unterstützt oder gebilligt.

Lizenz: [MIT](LICENSE). Versionsgeschichte: [ISTORIC.md](ISTORIC.md) (rumänisch).
