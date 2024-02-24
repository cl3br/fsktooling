import xml.etree.ElementTree as ET
import csv
from pathlib import Path
import traceback

from fsklib.hovtp.base import OdfListener, run_server
from fsklib.hovtp import parameter

class OdfParser:
    current_result_odf = None
    current_event_name = ""
    leader_result_data = None
    flag_dir = parameter.flag_folder
    flag_extension = parameter.flag_extension
    csv_dir = parameter.csv_folder
    # self.current_competitor_id = -1
    # self.competitor_has_changed = False

    @staticmethod
    def write_csv(csv_file_name: str, data: list, write_header=True):
        if not csv_file_name or not data:
            return

        if not OdfParser.csv_dir.is_dir():
            OdfParser.csv_dir.mkdir()

        with open(OdfParser.csv_dir / csv_file_name, "w", encoding="utf-8", newline="") as f:
            header = data[0].keys()
            w = csv.DictWriter(f, header)
            if write_header:
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
                self.process_current(root)
                if "SCORE_DONE" in odf:
                    result_elem = root.find("./Competition/Result")
                    if result_elem is not None:
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
            if composition is not None:  # for couples
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
        if not nation:
            return ""
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

    def process_current(self, root: ET.Element):
        # read live score (technial value only)
        live_score = root.find('./Competition/Result/ExtendedResults/ExtendedResult[@Code="ELEMENT"][@Pos="TOT"]')
        live_score_value = ""
        if live_score is not None:
            live_score_value = live_score.attrib["Value"]
        live_score_base = root.find('./Competition/Result/ExtendedResults/ExtendedResult/Extension[@Code="BASE_TOT"]')
        live_score_base_value = ""
        if live_score_base is not None:
            live_score_base_value = live_score_base.attrib["Value"]

        # convert GOE based on total base value and current score to color
        color = ""
        if len(live_score_value) > 0 and len(live_score_base_value) > 0:
            score = float(live_score_value)
            base = float(live_score_base_value)
            diff = score - base
            if abs(diff) < parameter.color_threshold * base:
                color = "yellow" # almost same as base
            elif diff > 0:
                color = "green"
            else:
                color = "red"

        # not useful -> follwoing code gives the total combined score (instead of technical score) of current leader
        # read the best score so far
        # to_beat = root.find(
        #     './Competition/ExtendedInfos/ExtendedInfo[@Type="DISPLAY"]/Extension[@Code="TO_BEAT"][@Pos="1"]')
        # to_beat_value = ""
        # if to_beat is not None:
        #     to_beat_value = to_beat.attrib["Value"]

        if live_score_value:
            live_score = {
                "LiveScore": live_score_value,
                "LiveScoreBase": live_score_base_value,
                "GOEColor": color,
                "GOEColorFile": OdfParser.flag_dir / (color + ".png"),
                "ElementName": "",
                "ElementAbbr": "",
                "ElementPoints": "",
                "LeaderRank": "",
                "LeaderScore": "",
                "LeaderName": "",
                "LeaderNat": "",
                "LeaderFlag": "" 
            }
            
            max_element = 0
            for element_score in root.findall('./Competition/Result/ExtendedResults/ExtendedResult[@Code="ELEMENT"]'):
                try:
                    max_element = max(max_element, int(element_score.attrib["Pos"]))
                except:
                    continue

            if max_element > 0:
                element_score = root.find(f'./Competition/Result/ExtendedResults/ExtendedResult[@Code="ELEMENT"][@Pos="{max_element}"]')
                live_score.update({
                    "ElementName": element_score.find('./Extension[@Code="ELEMENT_DESC"]').attrib["Value"],
                    "ElementAbbr": element_score.find('./Extension[@Code="ELEMENT_CODE"]').attrib["Value"],
                    "ElementPoints": element_score.attrib["Value"]
                })
                
            if OdfParser.leader_result_data and OdfParser.leader_result_data["Name"]:
                live_score.update({
                    "LeaderRank": "1",
                    "LeaderScore": OdfParser.leader_result_data["Technical Score"],
                    "LeaderName": OdfParser.leader_result_data["Name"],
                    "LeaderNat": OdfParser.leader_result_data["Nat"],
                    "LeaderFlag": OdfParser.leader_result_data["Flag"]
                })
            self.write_csv("live_score.csv", [live_score])
        return

    def process_result(self, root: ET.Element):
        event_data = []
        sport_description = root.find("./Competition/ExtendedInfos/SportDescription")
        #event_data.append({
        #    "KategorieName": sport_description.attrib["EventName"],
        #    "SegmentName": sport_description.attrib["SubEventName"]
        #})

        event_name = sport_description.attrib["EventName"] + " - " + sport_description.attrib["SubEventName"]
        event_data.append({"--" : "--",
                           "Event_name" : event_name })
        self.write_csv("event_name.csv", event_data)
        with open(OdfParser.csv_dir / "event.csv", "w", encoding="utf-8", newline="") as f:
            f.write(sport_description.attrib["EventName"] + " " + sport_description.attrib["SubEventName"])
        # self.write_csv("resultl.csv", [OdfParser.get_result_entry("","","","","","")])
        # self.write_csv("pat_current.csv", [OdfParser.get_result_entry("","","","","","")])

        # reset because of new event
        if OdfParser.current_event_name != event_name:
            OdfParser.leader_result_data = OdfParser.get_current_result_entry()

        OdfParser.current_event_name = event_name

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
            eue_elem = result_elem.find('./Competitor//EventUnitEntry[@Type="EUE"][@Code="GROUP"]')
            if eue_elem is not None:
                group_number = int(eue_elem.attrib["Value"])
                if group_number not in start_group_dict:
                    start_group_dict[group_number] = []

            if "Rank" not in result_elem.attrib and "ResultType" not in result_elem.attrib:  # extract start list
                start_list_data.append(get_start_list_entry(order_number, start_number, name, nation, group_number))

            if group_number:
                start_group_dict[group_number].append(get_start_list_entry(order_number, start_number, name, nation, group_number))

        if start_list_data:
            start_list_data = sorted(start_list_data, key=lambda data: int(data["StN"]))
            current_group_number = start_list_data[0]["Gruppe"]
        else:
            current_group_number = 0

        for i in range(len(start_list_data), parameter.max_category_lenght):
            # fill csv with empty lines
            start_list_data.append(get_start_list_entry("", "", "", "", ""))

        print("Num starter: " + str(len(start_list_data)))
        # print(start_list_data)
        self.write_csv("startl.csv", start_list_data)
        self.write_csv("pat_name1.csv", list(start_list_data[0:1]))
        with open(OdfParser.csv_dir / "pat_name.csv", "w", encoding="utf-8", newline="") as f:
            f.write("%s,%s,%s," % (
                start_list_data[0]["Name"],
                start_list_data[0]["Nat"],
                start_list_data[0]["Flag"])
            )

        for group_number in start_group_dict:
            start_group_dict[group_number].sort(key=lambda data: int(data['--']))

            for i in range(len(start_group_dict[group_number]), parameter.max_group_length):
                start_group_dict[group_number].append(get_start_list_entry("", "", "", "", ""))

            self.write_csv(f"wg{str(group_number)}-startl.csv", start_group_dict[group_number], False)

            if group_number == current_group_number:
                self.write_csv("wg-startl.csv", start_group_dict[group_number], False)

    def process_cumulative_result(self, root: ET.Element):
        current_competitor_code = None
        if OdfParser.current_result_odf:
            root2 = ET.fromstring(OdfParser.current_result_odf)
            competitor = root2.find("./Competition/Result/Competitor")
            if competitor is not None:
                current_competitor_code = competitor.attrib["Code"]
            result = root2.find("./Competition/Result")
            if result:
                def get_score(result: ET.Element, code) -> str:
                    score = result.find(f'./ExtendedResults/ExtendedResult[@Code="{code}"][@Pos="TOT"]')
                    return score.attrib["Value"] if score is not None else ""

                total_score = result.attrib["Result"] if "Result" in result.attrib else ""
                element_score = get_score(result, "ELEMENT")
                component_score = get_score(result, "COMPONENT")
                deduction = get_score(result, "DEDUCTION")
                OdfParser.current_result_odf = None

        current_result_data = []
        result_data = []
        result_elems = root.findall("./Competition/Result")
        current_rank = 0
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
                
                rank = str(result_elem.attrib[result_type])
                result_data.append(OdfParser.get_result_entry(rank, name, nation, points, kp, kr))

                if code == current_competitor_code:
                    current_result = OdfParser.get_current_result_entry(name, nation, element_score, component_score, deduction, total_score, points, rank)
                    current_result_data.append(current_result)
                    
                    try:
                        current_rank = int(rank)
                    except:
                        current_rank = 0

                    if current_rank == 1:
                        OdfParser.leader_result_data = current_result

        print("Num results: " + str(len(result_data)))
        # print(result_data)

        for i in range(len(result_data), parameter.max_category_lenght):
            result_data.append(OdfParser.get_result_entry())
        if not current_result_data:
            current_result_data.append(OdfParser.get_current_result_entry())

        # print(current_result_data)

        if current_rank:
            intermediate_result = []
            for rank in range(current_rank-1, current_rank+2):
                intermediate_result.append(next(filter(lambda data: data["FPl"] == str(rank), result_data), self.get_result_entry()))

            #intermediate_result = list(map(lambda data: data[1:3], intermediate_result))
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
    run_server(OdfListenerCsv, parameter.host_name, parameter.server_port)


def test():
    folder = Path("C:\\SwissTiming\\OVR\\FSManager\\Export\\GBB2022\\ODF\\Men\\Free Skating")

    parser = OdfParser()

    for file_path in folder.iterdir():
        with open(file_path, "r") as file:
            odf = file.read()
            parser.process_odf(odf)


if __name__ == "__main__":
    main()
    # test()
