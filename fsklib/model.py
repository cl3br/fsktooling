import datetime
from enum import Enum, IntEnum
from typing import List, Optional, Tuple, Union
from typing_extensions import Self

from pydantic import Field, model_validator
from pydantic.dataclasses import dataclass

from fsklib.utils.common import normalize_string


class DataSource(IntEnum):
    FSM = 0
    CALC = 1
    ODF = 2
    DEU = 3
    ISU = 4


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


@dataclass
class Club:
    name: str = ''
    abbr: str = ''
    nation: str = ''


@dataclass
class Person:
    id: str = ''
    first_name: str = ''
    family_name: str = ''
    gender: Gender = Field(Gender.FEMALE)
    bday: datetime.date = Field(datetime.date.today())
    club: Club = Field(Club())

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
        if data_source in [DataSource.DEU, DataSource.ISU]:
            raise Exception("Invalid input data source.")


@dataclass(frozen=True)
class Segment:
    name: str
    abbr: str
    type: SegmentType


class CategoryType(DataEnum):
    MEN = (0, 'S', 'SINGLES', 'Herren', 'Men')
    WOMEN = (1, 'S', 'SINGLES', 'Damen', 'Women')
    SINGLES = (None, 'S', 'SINGLES', 'Einzellaufen', 'Single Skating')
    PAIRS = (2, 'P', 'PAIRS', 'Paarlaufen', 'Pair Skating')
    ICEDANCE = (3, 'D', 'ICEDANCE', 'Eistanzen', 'Ice Dance')
    SYNCHRON = (4, 'T', 'SYNCHRON', 'Synchron', 'Synchronized Skating')
    SOLOICEDANCE = (None, 'D', 'SOLDANCE', 'Eistanzen', 'Solo Ice Dance')

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


@dataclass(frozen=True)
class Category:
    name: str
    type: CategoryType
    level: Union[CategoryLevel, str]
    gender: Optional[Gender]
    segments: Tuple[Segment] = Field(default_factory=tuple)
    number: int = 0

    @model_validator(mode='after')
    def correct_gender(self) -> Self:
        if not self.gender:
            self.gender = self.type.to_gender()
        return self

    def add_segment(self, segment: Segment):
        self.segments = (*self.segments, segment)


@dataclass
class Couple:
    partner_1: Optional[Person]
    partner_2: Optional[Person]


@dataclass
class Team:
    id: str
    name: str  # could be sys team name or couple name
    club: Club  # also holds the nation
    persons: List[Person] = Field(default_factory=list)  # for couples or SYS


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


@dataclass
class ParticipantBase:
    category: Category

    def get_normalized_name(self) -> str:
        pass


@dataclass
class ParticipantBaseDefaults:
    role: Role = Field(Role.ATHLETE)
    status: Optional[str] = Field(None)
    points: Optional[str] = Field(None)


@dataclass
class ParticipantSingleBase(ParticipantBase):
    person: Person

    def get_normalized_name(self, reverse=False) -> str:
        if reverse:
            return normalize_string(self.person.family_name + self.person.first_name)
        else:
            return normalize_string(self.person.first_name + self.person.family_name)


@dataclass
class ParticipantSingle(ParticipantBaseDefaults, ParticipantSingleBase):
    pass


@dataclass
class ParticipantCoupleBase(ParticipantBase):
    couple: Couple

    def get_normalized_name(self) -> str:
        name = "".join([
            p.first_name + p.family_name
            for p in [self.couple.partner_1, self.couple.partner_2]
        ])
        return normalize_string(name)


@dataclass
class ParticipantCouple(ParticipantBaseDefaults, ParticipantCoupleBase):
    pass


@dataclass
class ParticipantTeamBase(ParticipantBase):
    team: Team

    def get_normalized_name(self) -> str:
        return normalize_string(self.team.name)


@dataclass
class ParticipantTeam(ParticipantBaseDefaults, ParticipantTeamBase):
    pass


@dataclass
class Competition:
    name: str
    organizer: str
    place: str
    start: datetime.date
    end: datetime.date
    # categories = [] not yet used
    # participants = [] not yet used


if __name__ == "__main__":
    print(Gender.MALE)
    g = Gender.from_value('F', DataSource.CALC)
    print(g)
    print(g.FSM())
    print(Gender.from_value('M', DataSource.ODF))

    print(Competition("Bär", "BEV", "EHE", datetime.date.today()))
    person = Person("99", "Max", "Mustermann", Gender.MALE, datetime.date(1990, 1, 1), Club("Eissport-Club", "ESC", "GER"))
    print(person)
    print(ParticipantSingle(Category("Nachwuchs Jungs", CategoryType.MEN, CategoryLevel.NOVICE_ADVANCED, None), person))
