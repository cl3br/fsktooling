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

        return Category(cat_name, cat_type, CategoryLevel.NOTDEFINED, cat_gender, 0)

    @staticmethod
    def _guess_club(club_name) -> Club:
        return Club(club_name, "TODO", "TODO")


class PdfParserFunctionDeu(PdfParserFunctionBase):
    def __call__(self, fields: Optional[Dict[str, Any]], fake_id=False):
        cat = self._guess_category_from_name(fields["Kategorie"]["/V"])
        club = self._guess_club(fields["Verein"]["/V"])
        if fake_id:
            id = 0
        else:
            id = int(fields["ID"])

        participant: ParticipantBase
        if cat.type is CategoryType.SYNCHRON:
            team_name = fields["Vorname"]["/V"] if fields["Vorname"]["/V"] else fields["Name"]["/V"]
            team = Team(id, team_name, club)
            participant = ParticipantTeam(team, cat)
        else:
            person = Person(id, fields["Name"]["/V"], fields["Vorname"]["/V"], cat.gender, datetime.time(), club)
            if cat.type in (CategoryType.WOMEN, CategoryType.MEN, CategoryType.SINGLES):
                participant = ParticipantSingle(person, cat)
            elif cat.type in (CategoryType.PAIRS, CategoryType.ICEDANCE):
                partner_club = self._guess_club(fields["Partner-Verein"]["/V"])
                partner = Person(
                    0 if fake_id else fields["Partner-ID"]["/V"],
                    fields["Partner-Name"]["/V"],
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

        return PPC(participant, elements_short, elements_long)


class PdfParserFunctionBev(PdfParserFunctionDeu):
    def __call__(self, fields: Optional[Dict[str, Any]], fake_id=True):
        return super().__call__(fields, fake_id)


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
            return self.function(fields)
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

    def update(self, ppcs: List[PPC]) -> None:
        ppc_map: Dict[str, PPC] = {ppc.participant.get_normalized_name(): ppc for ppc in ppcs}
        count = 0
        if not self.root:
            return

        for par in self.root.findall(".//Participant"):
            name = par.attrib["PrintName"]
            sname = normalize_string(name)
            if sname not in ppc_map:
                print(f"Unable to find PPC for: {name}")
                continue

            print(f"Found PPC for: {name}")
            count += 1

            event = par.find(".//RegisteredEvent")
            if event is not None:
                ppc = ppc_map[sname]
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


if __name__ == '__main__':
    top_dir = Path('./BM24/PPCS/all/')
    parser = PdfParser(PdfParserFunctionBev())
    ppcs_list = parser.ppcs_parse_dir(top_dir, recursive=True)

    odf_file_name = Path("BM24/DT_PARTIC.xml")
    with PpcOdfUpdater(odf_file_name) as updater:
        updater.update(ppcs_list)
