import xml.etree.ElementTree as ET
import csv
import pathlib
import traceback

from fsklib.hovtp.base import OdfListener, run_server

host_name = "127.0.0.1"
server_port = 11111


class OdfParser:
    current_result_odf = None

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

        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            header = data[0].keys()
            w = csv.DictWriter(f, header)
            w.writeheader()
            w.writerows(data)

    def process_odf(self, odf: str):
        root = ET.fromstring(odf)
        doc_type = root.attrib["DocumentType"]
        if doc_type in ["DT_CLOCK", "DT_SCHEDULE", "DT_SCHEDULE_UPDATE"]:
            return

        # print(doc_type)
        # print(odf)

        if doc_type == "DT_CURRENT":
            # store current result
            try:
                if "SCORE_DONE" in odf:
                    result_elem = root.find("./Competition/Result")
                    if result_elem:
                        # must be stored in class scope (or global) because object instances do not survive multiple cycles
                        OdfParser.current_result_odf = odf
            except:
                traceback.print_exc()
                print(odf)
        elif doc_type == "DT_RESULT":
            # extract current event and start list
            try:
                self.process_result(root)
            except:
                traceback.print_exc()
                print(odf)
        elif doc_type == "DT_CUMULATIVE_RESULT":
            # extract current result and result list
            try:
                self.process_cumulative_result(root)
            except:
                traceback.print_exc()
                print(odf)

    @staticmethod
    def get_name_nation_from_result(elem: ET.Element):
        competitor_elem = elem.find("Competitor")

        composition = competitor_elem.find("./Composition")
        # athlete_desc = competitor_elem.find("./Composition/Athlete/Description")
        # if athlete_desc is None:
        #     return

        if competitor_elem.attrib["Type"] == "T":
            if composition:  # for couples
                nations = []
                name = ""
                for athlete in composition.findall("./Athlete/Description"):
                    if name:
                        name += " / "
                    name += str(athlete.attrib["GivenName"]) + " " + str(athlete.attrib["FamilyName"])
                    nations.append(athlete.attrib["Organisation"])
                nation = nations[0] if len(set(nations)) == 1 else " / ".join(nations)
            else:  # for teams
                name = competitor_elem.find("Description").attrib["TeamName"]
                nation = competitor_elem.attrib["Organisation"]
        else:
            athlete = composition.find("./Athlete/Description")
            name = str(athlete.attrib["GivenName"]) + " " + str(athlete.attrib["FamilyName"])
            nation = str(athlete.attrib["Organisation"])
        return competitor_elem.attrib["Code"], name, nation

    # def process_current(self, root: ET.Element):
    #     # competitor_elem = root.find("./Competition/Result/Competitor")
    #
    #     # if competitor_elem and \
    #     #     "Code" in competitor_elem.attrib and \
    #     #     self.current_competitor_id != competitor_elem.attrib["Code"]:
    #     #     self.current_competitor_id = competitor_elem.attrib["Code"]
    #     #     self.competitor_has_changed = True
    #
    #     # score is done
    #     score_done_elem = root.find(
    #         "./Competition/ExtendedInfos/ExtendedInfo[@Type='DISPLAY']/Extension[@Code='SCORE_DONE']")
    #     if not score_done_elem:
    #         return
    #
    #     result_elem = root.find("./Competition/Result")
    #     if result_elem:
    #         self.current_result_elem = result_elem

        return

    def process_result(self, root: ET.Element):
        event_data = []
        sport_description = root.find("./Competition/ExtendedInfos/SportDescription")
        event_data.append({
            "KategorieName": sport_description.attrib["EventName"],
            "SegmentName": sport_description.attrib["SubEventName"]
        })
        self.write_csv("event.csv", event_data)

        start_list_data = []
        result_elems = root.findall("./Competition/Result")
        for result_elem in result_elems:
            _, name, nation = self.get_name_nation_from_result(result_elem)
            if "StartOrder" in result_elem.attrib and "Rank" not in result_elem.attrib and "ResultType" not in result_elem.attrib:  # extract start list
                start_list_data.append({
                    "StartNummer": str(result_elem.attrib["StartOrder"]),
                    "Name": name,
                    "Nation": nation,
                    "FLG": str(self.flag_dir / (nation + self.flag_extension))
                })

        start_list_data = sorted(start_list_data, key=lambda data: int(data["StartNummer"]))

        # print(start_list_data)
        print("Num starter: " + str(len(start_list_data)))
        self.write_csv("startlist.csv", start_list_data)

    def process_cumulative_result(self, root: ET.Element):
        current_competitor_code = None
        if OdfParser.current_result_odf:
            root2 = ET.fromstring(OdfParser.current_result_odf)
            competitor = root2.find("./Competition/Result/Competitor")
            if competitor:
                current_competitor_code = competitor.attrib["Code"]
            result = root2.find("./Competition/Result")
            if result:
                def get_score(result: ET.Element, code) -> str:
                    score = result.find(f'./ExtendedResults/ExtendedResult[@Code="{code}"][@Pos="TOT"]')
                    return score.attrib["Value"] if score is not None else ""

                total_score = get_score(result, "LIVE_SCORE")
                element_score = get_score(result, "ELEMENT")
                component_score = get_score(result, "COMPONENT")
                deduction = get_score(result, "DEDUCTION")
                OdfParser.current_result_odf = None

        current_result_data = []
        result_data = []
        result_elems = root.findall("./Competition/Result")
        for result_elem in result_elems:
            code, name, nation = self.get_name_nation_from_result(result_elem)
            if "Rank" in result_elem.attrib or "IRM" in result_elem.attrib:  # extract final result
                if "Rank" in result_elem.attrib:
                    result_type = "Rank"
                    points = str(result_elem.attrib["Result"])
                else:
                    result_type = "IRM"
                    points = ""

                kp = ""
                kr = ""
                for result_item in result_elem.findall("./ResultItems/ResultItem"):
                    if "QUAL" in result_item.attrib["Unit"]:
                        result = result_item.find("./Result")
                        if "Rank" in result.attrib:
                            kp = result.attrib["Rank"]
                        else:
                            kp = "WD"
                    if "FNL" in result_item.attrib["Unit"]:
                        result = result_item.find("./Result")
                        if "Rank" in result.attrib:
                            kr = result.attrib["Rank"]
                        else:
                            kr = "WD"
                result_data.append({
                    "FPl": str(result_elem.attrib[result_type]),
                    "Name": name,
                    "Nation": nation,
                    "Pkt": points,
                    "KP": kp,
                    "KR": kr,
                    "FLG": str(self.flag_dir / (nation + self.flag_extension))
                })

                if code == current_competitor_code:
                    current_result_data.append({
                        "FPl": str(result_elem.attrib[result_type]),
                        "Name": name,
                        "Nation": nation,
                        "Total": total_score,
                        "Elements" : element_score,
                        "Components": component_score,
                        "Deductions": deduction,
                        "FLG": str(self.flag_dir / (nation + self.flag_extension))
                    })

        print(result_data)
        print("Num results: " + str(len(result_data)))

        print(current_result_data)

        self.write_csv("result.csv", result_data)
        self.write_csv("current_result.csv", current_result_data)


class OdfListenerCsv(OdfListener):
    def __init__(self, request, client_address, server):
        self.parser = OdfParser()
        super().__init__(request, client_address, server)

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
    main()
    # test()
