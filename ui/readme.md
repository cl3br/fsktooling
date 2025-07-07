# DEUMeldeformularKonverter

## Zweck
Das Tool extrahiert Informationen aus der DEU-Meldeliste (xlsx-Format) und konvertiert diese Daten in verschiedene andere Formate, 
um manuelles Übertragen der Personen-Daten zu minimieren.

## Wettbewerbe
Für Wettbewerbe kann das Meldeformular nach [ODF](https://odf.olympictech.org/project.htm) konvertiert werden, 
welches vom FS Manager gelesen werden kann.

### Anleitung zum Erstellen eines Wettbewerbes
1. Im Excel-Meldeformular
    - ggf. Kategorien anpassen, wenn die Standard-DEU-Kategorien des Meldeformulars nicht ausreichen
    - in der Spalte "Kategorie" können die Namen der ISU-Kategorien (z.B. "Intermediate Novice") bzw. die maximal 6-stelligen Abkürzungen der ISU-Kategorien (z.B. "BASNOV" für "Basic Novice") eingetragen werden
    - für nutzerspezifische Kategorien
        * es kann ein beliebieger, maximal 6-stelliger Name (nur Großbuchstaben) angegeben werden
        * es ist eine Setup-Datei notwendig, um diese in FSM zu nutzen (siehe 3. Im FS Manager -> Kategorien einlesen)
2. Im DEUMeldeformularKonverter
    - Excel-Datei auswählen
    - auf konvertieren klicken
    - neben dem ausgewählten Meldeformular werden die ODF-Dateien `DT_PARTIC.xml` und `DT_PARTIC_TEAM.xml` generiert
3. Im FS Manager
    - neue Datenbank erstellen
    - Elemente aus FSM masterData einlesen
    - Nationen aus DEUMeldeformularKonverter einlesen
        * Nations > Import
        * `./masterData/FSM/nations-DEU-Landesverbaende.xml`
    - Clubs aus DEUMeldeformularKonverter einlesen
        * Clubs > Import
        * `./masterData/FSM/clubs-DEU.xml`
    - Kategorien einlesen
        * Time Schedule > "Import Categories / Segments"
        * erzeugte `DT_PARTIC.xml` auswählen
        * Hinweis: Kategorien für Synchron müssen von Hand angelegt werden (der Import wird aktuell nicht im FSM unterstützt)
        * Spezialfall: Custom Categories
            + Für nutzerspezifische Kategorien muss eine Setup-Datei (XML) für den Wettbewerb unter "Competition" importiert werden.
            + Dafür legt man am besten den Wettbewerb vor dem Import der Kategorien an:
                - für Competition-Code muss exakt der Name des Wettbewerbs aus dem Excel-Formular eingetragen werden, damit beim Import die Daten diesem Wettbewerb zugeordnet werden
                - für "Type of competition" muss etwas anderes als "International Competition" ausgewählt werden
                - Speichern
                - auf der rechten Seite über Custom Settings > Import > Custom Setup
                - anschließend auf der linken Seite im Wettbewerb > Custom Setup > wähle importiertes Parameter-Set aus
                - Speichern
            + mit dem Einlesen der Kategorien beginnen
    - Personen einlesen
        * People > Import > Initial Download (complete)
        * erzeugte `DT_PARTIC.xml` auswählen
    - Paare & Eistänzer einlesen
        * Couples > Import > Initial Download (complete)
        * erzeugte `DT_PARTIC_TEAMS.xml` auswählen
    - Synchron-Teams einlesen
        * Synchornized Teams > Import > Initial Download (complete)
        * erzeugte `DT_PARTIC_TEAMS.xml` auswählen
    - Offizielle aus DEUMeldeformularKonverter einlesen (falls nicht bereits vorhanden)
        * Time Schedule > "Import Categories / Segments"
        * `./masterData/FSM/officials-DEU.xml` auswählen
        * People > Import > Initial Download (complete)
        * `./masterData/FSM/officials-DEU.xml` auswählen
    - Aktiven Wettbewerb wechseln
        * Competition > Wettbewerb wählen > "Set as Current" aktivieren
    - relevante Preisrichter dem aktuellen Wettbewerb zuweisen
        * Officials > Wettbewerb auswählen > von "People" zu "Competition Officials" verschieben
        * Officials > Segment auswählen > Preisrichter den Funktionen zuordnen
4. im Datei-Explorer
    - Flaggen für FS Manager kopieren
        * `./masterData/FSM/flags/copyToFSM.bat` ausführen
        * alternativ können die Flaggen von Hand im FSM hinzufügt werden
    - Flaggen für Webseite kopieren
        * kopiere `./masterData/FSM/website/*.GIF` in den Ordner `flags` im Webseiten-Hauptordner 
    - leere PDF-Dateien kopieren, um falsch angezeigte Ergebnisse zu verhindern
        * während der Konvertierung des Meldeformulars wird neben der ausgewählten Excel-Datei der Ordner `website` erstellt
        * kopiere `website/*.pdf` neben die `index.html` des entsprechenden Wettbewerbs

### Anleitung zum Einlesen von PPC-Daten
1. Im FS Manager
    - DT_PARTIC-Datei exportieren
        * People > Export People
        * DT_PARTIC-Datei wird standardmäßig in folgendem Verzeichnis abgelegt:
            [FSM-Verzeichnis]/Export/[Competition-Name]/ODF/
2. Im DEUMeldeformularKonverter
    - Tab "PPC-Konverter" auswählen
    - Ordner mit PPC-PDF-Dateien auswählen
        - PDF-Formular: siehe `./masterData/PPC/`
    - Exportierte DT_PARTIC-Datei auswählen
    - "Konvertieren" drücken
3. Im FS Manager
    - DT_PARTIC-Datei importieren 
        * People > Import > Only Planned Elements (PPC)
        * Erzeugte `DT_PARTIC_with_ppc.xml` auswählen

### Anleitung zum Auslesen der Ergebnisse eines Wettbewerbes
1. Zum Tab "FSM-Datenbank auslesen" wechseln
2. Ausgabe-Datei auswählen
3. ggf. Standardeinstellungen für die Datenbankanbindung anpassen und auf "Aktualisieren" drücken, um die Verbindung zu testen
4. Datenbank und Wettbewerb auswählen
5. "Extrahieren" drücken
6. Erzeugte Excel-Datei öffnen und den Inhalt an die entsprechende Stelle im DEU-Meldeformular kopieren

### Einschränkungen
1. Kategorienamen können nicht importiert werden
2. Nachwuchsklasse wird "Advanced Novice" zugeordnet
    - "Basic Novice" -> beginnt der Kategoriename mit "Basic Novice"
    - "Intermediate Novice" -> beginnt der Kategoriename mit "Intermediate Novice"
    - alternativ kann die Spalte "Kategorie" wie oben unter "1. Im Excel-Meldeformular" beschrieben, angepasst werden
3. Jugendklasse wird der Juniorenklasse zugeordnet -> die Verifikation für das Kurzprogramm muss noch von Hand entfernt werden
4. Synchron-Kategorien werden aktuell nicht von FSM importiert und müssen von Hand angelegt werden
5. Synchronteams können keine Athleten zugeordnet werden
6. Gibt es zwei Kategorien mit exakt dem selben Namen im Wettbewerb (Unterschied ist beispielsweise nur durch das Segment erkennbar - z.B. Women Bronze I - Free Skating und Women Bronze I - Artistic Free Skating), dann wird nur das Ergebnis der Kategorie exportiert, welche als letztes durchgeführt wurde.
7. Das Einlesen von PPC-Daten für Paare, Eistänzer und Synchron-Teams wird aktuell noch nicht unterstützt.
