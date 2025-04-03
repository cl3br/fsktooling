import datetime
from enum import Enum, IntEnum
from typing import List, Optional

from .utils.common import normalize_string


class Club:
    def __init__(self) -> None:
        self.name = ''
        self.abbr = ''
        self.nation = ''

    def __init__(self, name: str, abbreviation: str, nation: str) -> None:
        self.name = name
        self.abbr = abbreviation
        self.nation = nation


class DataSource(IntEnum):
    FSM = 0
    CALC = 1
    ODF = 2
    DEU = 3


class DataEnum(Enum):
    @classmethod
    def from_value(cls, value, data_source: DataSource):
        cls.check_data_source(data_source)
        for member in cls.__members__.values():
            if member.value[data_source] == value:
                return member

    @staticmethod
    def check_data_source(data_source: DataSource):
        pass

    def __str__(self) -> str:
        return self.name.lower()

    def _get_value(self, data_source: DataSource):
        self.check_data_source(data_source)
        return self.value[data_source]

    def FSM(self) -> int:
        return self._get_value(DataSource.FSM)

    def CALC(self) -> str:
        return self._get_value(DataSource.CALC)

    def ODF(self) -> str:
        return self._get_value(DataSource.ODF)

    def DEU(self) -> str:
        return self._get_value(DataSource.DEU)


class Gender(DataEnum):
    MALE = (0, 'M', 'M')
    FEMALE = (1, 'F', 'W')
    TEAM = (2, 'T', 'X')

    @staticmethod
    def check_data_source(data_source: DataSource):
        if data_source == DataSource.DEU:
            raise Exception("Invalid input data source.")


class Person:
    def __init__(self) -> None:
        self.id = ''
        self.first_name = ''
        self.family_name = ''
        self.gender = Gender.FEMALE
        self.bday = datetime.date.today()
        self.club = Club()

    def __init__(self, id, family_name, first_name, gender: Gender, birthday: datetime.date, club: Club) -> None:
        self.id = id  # DEU ID or "Sportpassnummer"
        self.first_name = first_name
        self.family_name = family_name
        self.gender = gender
        self.bday = birthday
        self.club = club

    @property
    def name(self) -> str:
        names = [name for name in [self.first_name, self.family_name] if name]
        if names:
            return " ".join(names)
        else:
            return ""


class SegmentType(DataEnum):
    SP = (0, 'S', 'QUAL')
    FP = (1, 'F', 'FNL')
    PDK = (2, 'P', 'QUAL')  # pattern dance with key points
    PD = (3, 'P', 'QUAL')   # pettern dance witout key points

    @staticmethod
    def check_data_source(data_source: DataSource):
        if data_source == DataSource.DEU:
            raise Exception("Invalid input data source.")


class Segment:
    def __init__(self, name: str, abbreviation: str, type: SegmentType) -> None:
        self.name = name
        self.abbr = abbreviation
        self.type = type


class CategoryType(DataEnum):
    MEN = (0, 'S', 'SINGLES', 'Herren')
    WOMEN = (1, 'S', 'SINGLES', 'Damen')
    SINGLES = (None, 'S', 'SINGLES', 'Einzellaufen')
    PAIRS = (2, 'P', 'PAIRS', 'Paarlaufen')
    ICEDANCE = (3, 'D', 'ICEDANCE', 'Eistanzen')
    SYNCHRON = (4, 'T', 'SYNCHRON', 'Synchron')

    def to_gender(self):
        if self == CategoryType.WOMEN:
            return Gender.FEMALE
        elif self == CategoryType.MEN:
            return Gender.MALE
        elif self in [CategoryType.PAIRS, CategoryType.ICEDANCE, CategoryType.SYNCHRON]:
            return Gender.TEAM
        else:
            raise Exception(f"Unable to determine gender for category type '{self}'.")


class CategoryLevel(DataEnum):
    SENIOR = (0, 'S', '', 'Meisterklasse')
    JUNIOR = (1, 'J', 'JUNIOR', 'Juniorenklasse')
    JUGEND = (1, 'J', 'JUNIOR', 'Jugendklasse')
    NOVICE_ADVANCED = (3, 'V', 'ADVNOV', 'Nachwuchsklasse')
    NOVICE_INTERMEDIATE = (4, 'I', 'INTNOV', 'Nachwuchsklasse')
    NOVICE_BASIC = (2, 'R', 'BASNOV', 'Nachwuchsklasse')
    ADULT = (5, 'O', 'ADULT', 'Adult')
    NOTDEFINED = (None, 'O', '', 'nicht definiert')
    MIXEDAGE = (6, 'O', 'MIXAGE', 'nicht definiert')
    ELITE12 = (7, 'O', 'SENELI', 'Adult')
    MASTERS = (8, 'O', 'MASTER', 'Adult')
    OTHER = (None, 'O', '', 'Sonstige Wettbewerbe')

    def is_ISU_category(self) -> bool:
        return self.FSM() is not None


class Category:
    def __init__(self, name: str, category_type: CategoryType, category_level: CategoryLevel, gender: Optional[Gender], number: int = 0) -> None:
        self.name = name
        self.type = category_type
        self.level = category_level
        self.gender = gender if gender else category_type.to_gender()
        self.number = number
        self.segments = []

    def add_segment(self, segment: Segment):
        self.segments.append(segment)


class Couple:
    def __init__(self, partner_1: Person, partner_2: Person) -> None:
        self.partner_1 = partner_1
        self.partner_2 = partner_2


class Team:
    def __init__(self, id, name: str, club: Club, persons: List[Person] = []) -> None:
        self.id = id
        self.name = name  # could be sys team name or couple name
        self.club = club  # also holds the nation
        self.persons = persons  # for couples or SYS


class Role(DataEnum):
    ATHLETE = (None, None, "AA01", "TN")   # AA01 - accreditated athlete (from Olympia)
    CAPTAIN = (None, None, "AA01", "CP")
    JUDGE = (None, None, "JU", "PR")
    REFEREE = (None, None, "RE", "SR")
    TECHNICAL_SPECIALIST = (None, None, "TCH_SPC", "TS")
    TECHNICAL_CONTROLLER = (None, None, "TCH_CTR", "TC")
    TECHNICAL_CONTROLLER_ICE = (None, None, "TCH_CTR", "TI")
    DATA_OPERATOR = (None, None, "DOP", "DO")
    VIDEO_OPERATOR = (None, None, "DOP", "RO")

    @staticmethod
    def check_data_source(data_source: DataSource):
        if data_source == DataSource.FSM or \
                data_source == DataSource.CALC:
            raise Exception("Invalid input data source.")


class ParticipantBase:
    def __init__(self, category: Category, role=Role.ATHLETE, status=None, total_points=None) -> None:
        self.cat = category
        self.role = role
        self.status = status
        self.points = total_points

    def get_normalized_name(self) -> str:
        pass


class ParticipantSingle(ParticipantBase):
    def __init__(self, person: Person, category: Category, role=Role.ATHLETE, status=None, total_points=None) -> None:
        super().__init__(category, role, status, total_points)
        self.person = person

    def get_normalized_name(self) -> str:
        return normalize_string(self.person.first_name + self.person.family_name)


class ParticipantCouple(ParticipantBase):
    def __init__(self, couple: Couple, category: Category, role=Role.ATHLETE, status=None, total_points=None) -> None:
        super().__init__(category, role, status, total_points)
        self.couple = couple

    def get_normalized_name(self) -> str:
        name = "".join([
            p.first_name + p.family_name
            for p in [self.couple.partner_1, self.couple.partner_2]
        ])
        return normalize_string(name)


class ParticipantTeam(ParticipantBase):
    def __init__(self, team: Team, category: Category, role=Role.ATHLETE, status=None, total_points=None) -> None:
        super().__init__(category, role, status, total_points)
        self.team = team

    def get_normalized_name(self) -> str:
        return normalize_string(self.team.name)


class Competition:
    def __init__(self, name: str, organizer: str, place: str, start: datetime.date, end: datetime.date) -> None:
        self.name = name
        self.organizer = organizer
        self.place = place
        self.start = start
        self.end = end
        # self.categories = [] not yet used
        # self.participants [] not yet used


if __name__ == "__main__":
    print(Gender.MALE)
    g = Gender.from_value('F', DataSource.CALC)
    print(g)
    print(g.FSM())
    Gender.from_value('Herrn', DataSource.DEU)
