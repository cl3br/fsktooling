import datetime
from enum import Enum, IntEnum
from typing import List, Union

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
    FSM =  0
    CALC = 1
    ODF =  2
    DEU =  3
    ISU =  4


class DataEnum(Enum):
    @classmethod
    def from_value(cls, value, data_source: DataSource):
        cls.check_data_source(data_source)
        for member in cls.__members__.values():
            if member.value[data_source] == value:
                return member
        return None

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
    def ISU(self) -> str:
        return self._get_value(DataSource.ISU)

class Gender(DataEnum):
    MALE = (0, 'M', 'M')
    FEMALE = (1, 'F', 'W')
    TEAM = (2, 'T', 'X')

    @staticmethod
    def check_data_source(data_source: DataSource):
        if data_source in [DataSource.DEU, DataSource.ISU]:
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

class SegmentType(DataEnum):
    SP = (0, 'S', 'QUAL')
    FP = (1, 'F', 'FNL')
    PDK = (2, 'P', 'QUAL') # pattern dance with key points
    PD = (3, 'P', 'QUAL') # pettern dance witout key points

    @staticmethod
    def check_data_source(data_source: DataSource):
        if data_source in [DataSource.DEU, DataSource.ISU]:
            raise Exception("Invalid input data source.")

class Segment:
    def __init__(self, name: str, abbreviation: str, type: SegmentType) -> None:
        self.name = name
        self.abbr = abbreviation
        self.type = type

class CategoryType(DataEnum):
    MEN = (0, 'S', 'SINGLES', 'Herren', 'Men')
    WOMEN = (1, 'S', 'SINGLES', 'Damen', 'Women')
    SINGLES = (None, 'S', 'SINGLES', 'Einzellaufen', 'Single Skating')
    PAIRS = (2, 'P', 'PAIRS', 'Paarlaufen', 'Pair Skating')
    ICEDANCE = (3, 'D', 'ICEDANCE', 'Eistanzen', 'Ice Dance')
    SYNCHRON = (4, 'T', 'SYNCHRON', 'Synchron', 'Synchronized Skating')

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
    SENIOR = (0, 'S', '', 'Meisterklasse', 'Senior')
    JUNIOR = (1, 'J', 'JUNIOR', 'Juniorenklasse', 'Junior')
    JUGEND = (1, 'J', 'JUNIOR', 'Jugendklasse', None)
    NOVICE_ADVANCED = (3, 'V', 'ADVNOV', 'Nachwuchsklasse', 'Advanced Novice')
    NOVICE_INTERMEDIATE = (4, 'I', 'INTNOV', 'Nachwuchsklasse', 'Intermediate Novice')
    NOVICE_BASIC = (2, 'R', 'BASNOV', 'Nachwuchsklasse', 'Basic Novice')
    ADULT = (5, 'O', 'ADULT', 'Adult', 'Adult')
    NOTDEFINED = (None, 'O', '', 'nicht definiert', None)
    MIXEDAGE = (6, 'O', 'MIXAGE', 'nicht definiert', 'Mixed Age')
    ELITE12 = (7, 'O', 'SENELI', 'Adult', 'Elite Masters')
    MASTERS = (8, 'O', 'MASTER', 'Adult', 'Masters')
    OTHER = (None, 'O', '', 'Sonstige Wettbewerbe', None)

    def is_ISU_category(self) -> bool:
        return self.ISU() is not None

class Category:
    def __init__(self, name: str, category_type: CategoryType, category_level: Union[CategoryLevel,str], gender: Gender, number: int) -> None:
        self.name = name
        self.type = category_type
        self.level = category_level
        self.gender = gender
        self.number = number
        self.segments = []

    def add_segment(self, segment: Segment):
        self.segments.append(segment)

class Couple:
    def __init__(self, partner_1: Person, partner_2: Person) -> None:
        self.partner_1 = partner_1
        self.partner_2 = partner_2
class Team:
    def __init__(self, id, name: str, club: Club, persons: List[Person]) -> None:
        self.id = id
        self.name = name # could be sys team name or couple name
        self.club = club # also holds the nation
        self.persons = persons # for couples or SYS


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
    def __init__(self, category: Category, role = None, status = None, total_points = None) -> None:
        self.cat = category
        self.role = role
        self.status = status
        self.points = total_points

class ParticipantSingle(ParticipantBase):
    def __init__(self, person: Person, category: Category, role = None, status = None, total_points = None) -> None:
        super().__init__(category, role, status, total_points)
        self.person = person

class ParticipantCouple(ParticipantBase):
    def __init__(self, couple: Couple, category: Category, role = None, status = None, total_points = None) -> None:
        super().__init__(category, role, status, total_points)
        self.couple = couple

class ParticipantTeam(ParticipantBase):
    def __init__(self, team: Team, category: Category, role = None, status = None, total_points = None) -> None:
        super().__init__(category, role, status, total_points)
        self.team = team

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
