# DEUMeldeformularKonverter

## Zweck
Das Tool extrahiert Informationen aus der DEU-Meldeliste (xlsx-Format) und konvertiert diese Daten in verschiedene andere Formate, 
um manuelles Übertragen der Personen-Daten zu minimieren.

## Wettbewerbe
Für Wettbewerbe kann das Meldeformular nach [ODF](https://odf.olympictech.org/project.htm) konvertiert werden, 
welches vom FS Manager gelesen werden kann.

### Anleitung zum Erstellen eines Wettbewerbes
1. Im DEUMeldeformularKonverter
    - Excel-Datei auswählen
    - auf konvertieren klicken
    - neben dem ausgewählten Meldeformular werden die ODF-Dateien `DT_PARTIC.xml` und `DT_PARTIC_TEAM.xml` generiert 
2. Im FS Manager
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
        * erzeugte `DT_PARTIC_TEAMS.xml` auswählen
        * Kategorien für Synchron müssen von Hand angelegt werden (der Import wird aktuell nicht im FSM unterstützt)
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
3. im Datei-Explorer
    - Flaggen für FS Manager kopieren
        * `./masterData/FSM/flags/copyToFSM.bat` ausführen
        * alternativ können die Flaggen von Hand im FSM hinzufügt werden
    - Flaggen für Webseite kopieren
        * kopiere `./masterData/FSM/website/*.GIF` in den Ordner `flags` im Webseiten-Hauptordner 
    - leere PDF-Dateien kopieren, um falsch angezeigte Ergebnisse zu verhindern
        * während der Konvertierung des Meldeformulars wird neben der ausgewählten Excel-Datei der Ordner `website` erstellt
        * kopiere `website/*.pdf` neben die `index.html` des entsprechenden Wettbewerbs

### Anleitung zum Auslesen der Ergebnisse eines Wettbewerbes
1. Zum Tab "FSM-Datenbank auslesen" wechseln
2. Ausgabe-Datei auswählen
3. ggf. Standardeinstellungen für die Datenbankanbindung anpassen und auf "Aktualisieren" drücken, um die Verbindung zu testen
4. Datenbank und Wettbewerb auswählen
5. "Extrahieren" drücken
6. Erzeugte Excel-Datei öffnen und den Inhalt an die entsprechende Stelle im DEU-Meldeformular kopieren

### Einschränkungen
1. Kategorienamen können nicht importiert werden
2. Non-ISU-Kategorien werden als "Advanced Novice"-Kategorie angelegt
3. alle Nachwuchskategorien werden "Advanced Novice" zugeordnet
    - "Basic Novice" -> beginnt der Kategoriename mit "Basic Novice"
    - "Intermediate Novice" -> beginnt der Kategoriename mit "Intermediate Novice"
4. Jugendklasse wird der Juniorenklasse zugeordnet
5. Synchronteams können keine Athleten zugeordnet werden
