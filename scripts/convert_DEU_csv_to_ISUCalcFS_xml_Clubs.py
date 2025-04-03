import csv, codecs

csv_file_path = "masterData/csv/clubs-DEU.csv"
xml_output_file_path_FSM = "masterData/FSM/clubs-DEU.xml"

xml_content_FSM = "<Clubs>\n"

club_abbreviations = set()
err = False

with open(csv_file_path, 'r', encoding="utf-8") as fi:
    r = csv.DictReader(fi, delimiter=';')
    for row in r:
        id = str(row['ID'])
        name = str(row['Name'])
        abbr = str(row['Abk.'])
        region = str(row['Region'])
        if abbr in club_abbreviations:
            print("Error: no unique club abbreviation")
            err = True
            break
        else:
            club_abbreviations.add(abbr)

        if '"' in name:
            name = name.replace('"', '\'')

        if '&' in name:
            name = name.replace('&', 'und')

        xml_content_FSM += "    <Club " \
                           "CLUB_NAME=\"" + name + "\" " \
                           "CLUB_SHORT_NAME=\"" + abbr + "\" />\n"

if err:
    print("Errors while processing... No output files are generated.")
    exit(1)

xml_content_FSM += "</Clubs>\n"

with codecs.open(xml_output_file_path_FSM, 'w', 'utf-8') as fo:
    fo.write(xml_content_FSM)
