import xml.etree.ElementTree as ET
from pathlib import Path

input_path = Path("C:\SwissTiming\OVR\FSManager\Export\TEST\ODF\DT_PARTIC_UPDATE.xml")

tree = ET.parse(input_path)
root = tree.getroot()

print("PPC missing for:")
for par in root.findall(".//Participant"):
    if par.find(".//EventEntry[@Code='ELEMENT_CODE_FREE']") is not None:
        continue

    event = par.find(".//RegisteredEvent")
    if event is None or event.attrib["Event"].startswith("FSKX"):
        continue
    
    print(f"{par.attrib['GivenName']} {par.attrib['FamilyName']}")