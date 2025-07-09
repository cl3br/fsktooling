# Export
Vereine und Landesverbaende sind aus dem DEU-Datenassistenten extrahiert.
Die Daten wurden aus dem Browser kopiert, in eine Exel-Liste eingefügt und als CSV exportiert.

# Stand
Aktueller Stand extrahiert am:
- 7.7.2025 - 8 Uhr

# Zusätzliche Vereine hinzufügen
Für Interclub-Wettbewerbe kann es notwendig sein noch weitere Vereine von anderen ISU-Mitgliedern hinzuzufügen.
Dies ist über eine separate club-csv-Datei möglich.

## Konventionen beim Hinzufügen von weiteren Vereinsdaten
### Dateiname
Folgende Dateien werden in Betracht gezogen:
`masterData/csv/club*.csv`
(* kann durch beliebig viele Zeichen ersetzt werden)

### CSV-Trennzeichen
Semikolon (`;`)

### Spaltenname
Damit die zusätzlichen Vereine eingelesen werden können, müssen die Spalten in der ersten Zeile der CSV-Datei wie folgt benannt sein:
`Name;Abk.;Region`
