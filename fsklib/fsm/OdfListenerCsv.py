import xml.etree.ElementTree as ET
import csv
import pathlib

from fsklib.fsm.OdfListenerBase import OdfListener, run_server

host_name = "192.168.1.123"
server_port = 11111


class OdfParser:
    def __init__(self):
        self.current_competitor_id = -1
        self.competitor_has_changed = False
        self.competitor_dict = {}
        self.flag_dir = pathlib.Path("C:\\my\\flag\\dir")
        self.flag_extension = ".png"

    @staticmethod
    def write_csv(csv_path: str, data: list):
        if not csv_path or not data:
            return

        with open(csv_path, "w", encoding = "utf-8", newline="") as f:
            header = data[0].keys()
            w = csv.DictWriter(f, header)
            w.writeheader()
            w.writerows(data)

    def process_odf(self, odf: str):
        root = ET.fromstring(odf)
        doc_type = root.attrib["DocumentType"]
        if doc_type in ["DT_CLOCK", "DT_SCHEDULE"]:
            return

        if doc_type == "DT_CURRENT":
            competitor_elem = root.find("./Competition/Result/Competitor")

            if competitor_elem and \
                "Code" in competitor_elem.attrib and \
                self.current_competitor_id != competitor_elem.attrib["Code"]:
                self.current_competitor_id = competitor_elem.attrib["Code"]
                self.competitor_has_changed = True
            return

        print(doc_type)

        start_list_data = []
        result_data = []
        event_data = []

        # extract current event
        if doc_type == "DT_RESULT":
            sport_description = root.find("./Competition/ExtendedInfos/SportDescription")
            event_data.append({
                "KategorieName": sport_description.attrib["EventName"],
                "SegmentName": sport_description.attrib["SubEventName"]
            })

        result_elems = root.findall("./Competition/Result")
        for result_elem in result_elems:
            competitor_elem = result_elem.find("Competitor")
            name = ""

            athlete_desc = competitor_elem.find("./Composition/Athlete/Description")
            if competitor_elem.attrib["Type"] == "T":  # for teams
                name = competitor_elem.find("Description").attrib["TeamName"]
            else:
                name = str(athlete_desc.attrib["GivenName"]) + " " + str(athlete_desc.attrib["FamilyName"])

            self.competitor_dict[competitor_elem.get("Code")] = name
            nation = str(athlete_desc.attrib["Organisation"])
            if "Rank" in result_elem.attrib:  # extract final result
                result_data.append({
                    "FPl": str(result_elem.attrib["Rank"]),
                    "Name": name,
                    "Nation": nation,
                    "Pkt": str(result_elem.attrib["Result"]),
                    "KP" : "TODO",
                    "KR" : "TODO",
                    "FLG" : str(self.flag_dir / (nation + self.flag_extension))
                })
            else:  # extract start list
                start_list_data.append({
                    "StartNummer": str(result_elem.attrib["StartOrder"]),
                    "Name": name,
                    "Nation": str(athlete_desc.attrib["Organisation"]),
                    "FLG" : str(self.flag_dir / (nation + self.flag_extension))
                })

        print(result_data)
        print("Num results: " + str(len(result_elem)))

        start_list_data = sorted(start_list_data, key=lambda data: data["StartNumber"])

        print(start_list_data)
        print("Num starter: " + str(len(start_list_data)))

        self.write_csv("result.csv", result_data)
        self.write_csv("event.csv", event_data)
        self.write_csv("startlist.csv", start_list_data)


class OdfListenerCsv(OdfListener):
    def __init__(self):
        self.parser = OdfParser()

    def process_odf(self, odf: str):
        self.parser.process_odf(odf)


def main():
    run_server(OdfListenerCsv, host_name, server_port)

def test():
    folder = pathlib.Path("C:\\SwissTiming\\OVR\\FSManager\\Export\\GBB2022\\ODF\\Men\\Free Skating")

    parser = OdfParser()

    for file_path in folder.iterdir():
        with open(file_path, "r") as file:
            odf = file.read()
            parser.process_odf(odf)

if __name__ == "__main__":
    #main()
    test()
