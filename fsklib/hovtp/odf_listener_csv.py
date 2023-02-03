import xml.etree.ElementTree as ET
import csv
import pathlib
import traceback

from fsklib.hovtp.base import OdfListener, run_server

host_name = "127.0.0.1"
server_port = 11111


class OdfParser:
    current_result_odf = None
    flag_dir = pathlib.Path("C:\\my\\flag\\dir")
    flag_extension = ".png"
    # self.current_competitor_id = -1
    # self.competitor_has_changed = False

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

    @staticmethod
    def get_flag(nation : str) -> str:
        return str(OdfParser.flag_dir / (nation + OdfParser.flag_extension)).replace("/", "\\")

    @staticmethod
    def get_current_result_entry(name="", nation="", element_score="", component_score="", deduction="", total_semgment_score="", total_score="", rank=""):
        return {
                    "Name": name,
                    "Nat": nation,
                    "Technical Score" : element_score,
                    "Program Score": component_score,
                    "Total Segment Score": total_semgment_score,
                    "Total Score": total_score,
                    "Total Rank": rank,
                    "Deductions": deduction,
                    "Flag": OdfParser.get_flag(nation)
                }

    @staticmethod
    def get_result_entry(rank="", name="", nation="", points="", kp="", kr=""):
        return {
                "--": "--",
                "FPl": rank,
                "Name": name,
                "Nat": nation,
                "Pkt": points,
                "KP": kp,
                "KR": kr,
                "Flag": OdfParser.get_flag(nation)
            }

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
        self.write_csv("event_name.csv", event_data)
        self.write_csv("resultl.csv", OdfParser.get_result_entry("","","","","",""))
        self.write_csv("pat_current.csv", OdfParser.get_result_entry("","","","","",""))
        self.write_csv("resultl.csv", OdfParser.get_result_entry("","","","","",""))

        start_list_data = []
        start_group_dict = {}
        result_elems = root.findall("./Competition/Result")
        for result_elem in result_elems:
            _, name, nation = self.get_name_nation_from_result(result_elem)
            if "StartOrder" not in result_elem.attrib:
                continue

            order_number = result_elem.attrib["StartOrder"]
            if "ResultType" in result_elem.attrib and result_elem.attrib["ResultType"] == "IRM" and "IRM" in result_elem.attrib:
                start_number = result_elem.attrib["IRM"]
            else:
                start_number = order_number

            def get_start_list_entry(order_number, start_number, name, nation, group_number):
                return {
                    "--": order_number,
                    "StN": start_number,
                    "Name": name,
                    "Nat": nation,
                    "Flag": OdfParser.get_flag(nation),
                    "Gruppe": group_number
                }

            group_number = 0
            eue_elem = result_elem.find('./Competitor/EventUnitEntry[@Pos="EUE"][@Code="GROUP"]')
            if eue_elem:
                group_number = int(eue_elem.attrib["Value"])
                if group_number not in start_group_dict:
                    start_group_dict[group_number] = []

            if "Rank" not in result_elem.attrib and "ResultType" not in result_elem.attrib:  # extract start list
                start_list_data.append(get_start_list_entry(order_number, start_number, name, nation, group_number))

            if group_number:
                start_group_dict[group_number].append(get_start_list_entry(order_number, start_number, name, nation, group_number))

        if start_list_data:
            current_group_number = start_list_data[0]["Gruppe"]
        else:
            # generate empty dict to clear csv file
            start_list_data.append(get_start_list_entry("", "", "", "", ""))
            current_group_number = 0
        start_list_data = sorted(start_list_data, key=lambda data: int(data["StN"]))

        # print(start_list_data)
        print("Num starter: " + str(len(start_list_data)))
        self.write_csv("startl.csv", start_list_data)
        self.write_csv("pat_name1.csv", list(start_list_data[0]))
        with open("pat_name.csv", "w", encoding="utf-8", newline="") as f:
            f.write("%s, %s, %s," % (
                start_list_data[0]["Name"],
                start_list_data[0]["Nat"],
                start_list_data[0]["Flag"])
            )

        for group_number in start_group_dict:
            start_group_dict[group_number].sort(key=lambda data: int(data['--']))
            self.write_csv(f"wg{str(group_number)}.csv", start_group_dict[group_number])

            if group_number == current_group_number:
                self.write_csv("wg.csv", start_group_dict[group_number])

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
                result_data.append(OdfParser.get_result_entry(str(result_elem.attrib[result_type]), name, nation, points, kp, kr))

                if code == current_competitor_code:
                    current_result_data.append(OdfParser.get_current_result_entry(name, nation, element_score, component_score, deduction, total_score, points, str(result_elem.attrib[result_type])))

        # print(result_data)
        print("Num results: " + str(len(result_data)))

        if not result_data:
            result_data.append(OdfParser.get_result_entry())
        if not current_result_data:
            current_result_data.append(OdfParser.get_current_result_entry())

        # print(current_result_data)

        if "Total Rank" in current_result_data[0]:
            previous_data = [data for data in result_data if str(int(data["FPl"]) - 1) == current_result_data[0]["Total Rank"]]
            current_data  = [data for data in result_data if data["FPl"]               == current_result_data[0]["Total Rank"]]
            next_data     = [data for data in result_data if str(int(data["FPl"]) + 1) == current_result_data[0]["Total Rank"]]

            intermediate_result = [previous_data, current_data, next_data]
            intermediate_result = list(map(lambda data: data if data else OdfParser.get_result_entry(), intermediate_result))
            intermediate_result = list(map(lambda data: data[1:3], intermediate_result))
            self.write_csv("act_pos.csv", intermediate_result)

        self.write_csv("resultl.csv", result_data)
        self.write_csv("pat_current.csv", current_result_data)


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
