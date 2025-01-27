from dataclasses import dataclass
import datetime
from pathlib import Path
import traceback
from typing import Any, Dict, List, Optional
import xml.etree.ElementTree as ET

from pypdf import PdfReader

from fsklib.model import (
    Gender, Club, Person, Couple, Team,
    Category, CategoryType, CategoryLevel,
    ParticipantBase, ParticipantSingle, ParticipantCouple, ParticipantTeam
)
from fsklib.odf.xml import OdfUpdater
from fsklib.utils.common import normalize_string


@dataclass
class PPC:
    participant: ParticipantBase
    elements_short: List[str]
    elements_long: List[str]
    path: Path


class PdfParserFunctionBase:
    def __call__(self, fields: Optional[Dict[str, Any]]):
        pass

    @staticmethod
    def _guess_category_from_name(cat_name: str) -> Category:
        @dataclass
        class CategoryHints:
            type: CategoryType
            hints: List[str]

        cat_hints = [
            CategoryHints(CategoryType.SYNCHRON, ["sys", "synch"]),
            CategoryHints(CategoryType.PAIRS, ["pair", "paar"]),
            CategoryHints(CategoryType.ICEDANCE, ["dance", "tanz"]),
            CategoryHints(CategoryType.WOMEN, ["girl", "ladies", "women" "mädchen", "damen", "frauen"]),
            CategoryHints(CategoryType.MEN, ["boy", "gents", "gentlemen", " men", "jungen", "männer", "herren"]),
                 ]

        def contains_any_hint(cat_hints: CategoryHints) -> bool:
            return any([hint in cat_name.casefold() for hint in cat_hints.hints])

        for cat_hint in cat_hints:
            if contains_any_hint(cat_hint):
                cat_type = cat_hint.type
                cat_gender = cat_type.to_gender()
            else:
                cat_type = CategoryType.SINGLES
                cat_gender = Gender.FEMALE

        return Category(cat_name, cat_type, CategoryLevel.NOTDEFINED, cat_gender, number=0)

    @staticmethod
    def is_field_valid(name: str, fields) -> bool:
        if isinstance(fields, dict) and name in fields and isinstance(fields[name], dict) and "/V" in fields[name] and fields[name]["/V"]:
            return True
        return False

    @staticmethod
    def get_field_value(name: str, fields, default_value=None) -> Optional[Any]:
        if PdfParserFunctionBase.is_field_valid(name, fields):
            return fields[name]["/V"]
        return default_value

    @staticmethod
    def _guess_club(name: str, fields) -> Club:
        return Club(PdfParserFunctionBase.get_field_value(name, fields, ""), "TODO", "TODO")


class PdfParserFunctionDeu(PdfParserFunctionBase):
    def __call__(self, path: Path, fields: Optional[Dict[str, Any]], fake_id=False):
        cat = Category("Dummy", CategoryType.SINGLES, CategoryLevel.SENIOR, Gender.FEMALE)
        if self.is_field_valid("Kategorie", fields):
            cat = self._guess_category_from_name(self.get_field_value("Kategorie", fields))
        club = self._guess_club("Verein", fields)
        if fake_id:
            id = "0"
        else:
            id = self.get_field_value("ID", fields, "0")

        participant: ParticipantBase
        if cat.type is CategoryType.SYNCHRON:
            team_name = fields["Vorname"]["/V"] if fields["Vorname"]["/V"] else fields["Nachname"]["/V"]
            team = Team(id, team_name, club)
            participant = ParticipantTeam(team, cat)
        else:
            person = Person(id, fields["Vorname"]["/V"], fields["Nachname"]["/V"], cat.gender, datetime.date.today(), club)
            if cat.type in (CategoryType.WOMEN, CategoryType.MEN, CategoryType.SINGLES):
                participant = ParticipantSingle(cat, person)
            elif cat.type in (CategoryType.PAIRS, CategoryType.ICEDANCE):
                partner_club = self._guess_club("Partner-Verein", fields)
                partner = Person(
                    0 if fake_id else fields["Partner-ID"]["/V"],
                    fields["Partner-Nachname"]["/V"],
                    fields["Partner-Vorname"]["/V"],
                    cat.gender, datetime.time(), partner_club)
                # fix gender
                person.gender = Gender.FEMALE
                participant = ParticipantCouple(Couple(person, partner), cat)

        elements_short: List[str] = []
        elements_long: List[str] = []
        for segment, element_list in zip(['KP', 'KR'], [elements_short, elements_long]):
            for i in range(1, 17):
                field_name = f"{segment}{i}"
                if field_name not in fields:
                    continue
                if "/V" not in fields[field_name]:
                    continue

                element = str(fields[field_name]["/V"]).strip()
                if element:
                    element_list.append(element)

        return PPC(participant, elements_short, elements_long, path)


class PdfParserFunctionBev(PdfParserFunctionDeu):
    def __call__(self, path: Path, fields: Optional[Dict[str, Any]], fake_id=True):
        return super().__call__(path, fields, fake_id)


class PdfParser:
    def __init__(self, func: PdfParserFunctionBase) -> None:
        self.function = func

    def parse(self, file_path: Path) -> Optional[PPC]:
        try:
            reader = PdfReader(file_path)
        except Exception:
            print(f"Error while reading pdf file: {file_path}")
            traceback.print_exc()
            print()
            return None

        fields = reader.get_fields()
        try:
            return self.function(file_path, fields)
        except Exception:
            print(f"Error while parsing file: {file_path}")
            traceback.print_exc()
            print()

        return None

    def parse_multiple(self, file_paths: List[Path]) -> List[PPC]:
        ppcs: List[PPC] = []

        for file_path in file_paths:
            ppc = self.parse(file_path)
            if ppc is None:
                continue
            ppcs.append(ppc)

        return ppcs

    def ppcs_parse_dir(self, directory: Path, recursive=False) -> List[PPC]:
        if not directory.is_dir():
            return []

        if recursive:
            glop_paths = directory.rglob("*.pdf")
        else:
            glop_paths = directory.glob("*.pdf")

        file_paths = sorted(filter(Path.is_file, glop_paths))
        return self.parse_multiple(file_paths)


class PpcOdfUpdater(OdfUpdater):
    def __init__(self, odf_xml_path: Path,
                 output_path: Optional[Path] = None,
                 suffix="_with_ppc",
                 override=False) -> None:
        super().__init__(odf_xml_path, output_path, suffix, override)

    def find_singles_ppcs(self, ppcs: List[PPC], id: str, participant: ET.Element) -> List[PPC]:
        xml_sname = normalize_string(participant.attrib["PrintName"])
        find_result = []
        for ppc in ppcs:
            if not isinstance(ppc.participant, ParticipantSingle):
                continue
            par: ParticipantSingle = ppc.participant
            if id and id == par.person.id:
                find_result.append(ppc)
            elif xml_sname == par.get_normalized_name():
                find_result.append(ppc)
        return find_result

    def find_couples_ppcs(self, ppcs: List[PPC], id: str, participant: ET.Element) -> List[PPC]:
        # TODO
        return []

    def find_sys_ppcs(self, ppcs: List[PPC], id: str, participant: ET.Element) -> List[PPC]:
        # TODO
        return []

    def update(self, ppcs: List[PPC]) -> None:
        if not self.root:
            print("Read xml file before updating it. Use `read_xml()` or `with Updater`")
            return

        # check Odf document type to find relevant ppc files
        if "DocumentType" not in self.root.attrib:
            print("No ODF document type found. -> Invalid odf input format.")
            return

        is_teams = self.root.attrib["DocumentType"].startswith("DT_PARTIC_TEAMS")
        is_singles = not is_teams
        par_type = "Team" if is_teams else "Participant"
        used_ppcs = []

        for par in self.root.findall(f".//{par_type}"):
            discipline = par.find("./Discipline")
            events = par.findall(".//RegisteredEvent")
            name = par.attrib["PrintName"]
            # if discipline is None or not events:
                # print(f"Skip participant {name}. Not registered in any event.")
            for event in events:
                xml_id = discipline.attrib["IFId"].strip()
                name = xml_id + " - " + name
                rsc = event.attrib["Event"]
                has_ppc = event.find("./EventEntry[@Code='ELEMENT_CODE_FREE']") is not None
                # print(f"Has ppc: {name}")

                if is_singles:
                    if CategoryType.SINGLES.ODF() not in rsc:
                        continue
                    find_ppcs = self.find_singles_ppcs
                elif CategoryType.SYNCHRON in rsc:
                    find_ppcs = self.find_sys_ppcs
                else:
                    find_ppcs = self.find_couples_ppcs

                relevant_ppcs = find_ppcs(ppcs, xml_id, par)

                if not relevant_ppcs:
                    if not has_ppc:
                        print(f"Unable to find PPC for: {name}")
                    continue

                if len(relevant_ppcs) > 1:
                    if not has_ppc:
                        print(f"Ambiguous ppcs found for: {name}")
                        for ppc in relevant_ppcs:
                            print(ppc.path)
                    continue

                assert len(relevant_ppcs) == 1

                # print(f"Found PPC for: {name}")

                ppc = relevant_ppcs[0]
                for element_list, odf_segment_name in zip(
                            [ppc.elements_short, ppc.elements_long],
                            ['ELEMENT_CODE_SHORT', 'ELEMENT_CODE_FREE']
                        ):

                    for i, element in enumerate(element_list, 1):
                        value = element.replace(" ", "").replace("-", "+")
                        attrib = {
                            "Type": "ER_EXTENDED",
                            "Code": odf_segment_name,
                            "Pos": str(i),
                            "Value": value}

                        ET.SubElement(event, "EventEntry", attrib)

                used_ppcs.append(ppc)

        # check for unused ppcs
        unused_ppcs = {ppc.path for ppc in ppcs} - {ppc.path for ppc in used_ppcs}
        print("Unused files:")
        for ppc in unused_ppcs:
            print(ppc.name)


if __name__ == '__main__':
    top_dir = Path('./BM25/PPC/')
    parser = PdfParser(PdfParserFunctionDeu())
    ppcs_list = parser.ppcs_parse_dir(top_dir, recursive=True)

    odf_file_name = Path("BM25/DT_PARTIC.xml")
    with PpcOdfUpdater(odf_file_name) as updater:
        updater.update(ppcs_list)
