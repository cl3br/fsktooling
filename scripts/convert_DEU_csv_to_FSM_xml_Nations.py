import codecs
import csv

csv_file_path = "masterData/csv/nations-DEU-Landesverbaende.csv"
xml_output_file_path = "masterData/FSM/nations-DEU-Landesverbaende.xml"

xml_content = "<ISUCalcFS>\n"\
              "  <Nation_List>\n"

with open(csv_file_path, 'r') as fi:
    r = csv.DictReader(fi, delimiter=';')
    for row in r:
        id = row['ID']
        abb = row['Abk.']
        name = row['Name']
        xml_content += "    <Nation " \
                       "NAT_ID=\"%s\" " \
                       "NAT_ISU=\"%s\" " \
                       "NAT_SORT=\"%s\" " \
                       "NAT_NAME=\"%s\" " \
                       "NAT_TV=\"%s\" " \
                       "NAT_LOGO=\"\" />\n" \
                       % (id, abb, abb, name, abb)

xml_content += "  </Nation_List>\n" \
               "</ISUCalcFS>\n"

with codecs.open(xml_output_file_path, 'w', "utf-8") as fo:
    fo.write(xml_content)
