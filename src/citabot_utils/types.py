import enum

from attr import dataclass


class Intervals(enum.Enum):
    I_30S = 30
    I_1M = 60
    I_3M = 60 * 3
    I_5M = 60 * 5
    I_10M = 60 * 10
    I_30M = 60 * 30
    I_1H = 60 * 60
    I_2H = 60 * 60 * 2
    I_4H = 60 * 60 * 4
    I_8H = 60 * 60 * 8
    I_12H = 60 * 60 * 12


class Tramites(enum.Enum):
    RENOVACION = "POLICIA- EXPEDICIÓN/RENOVACIÓN DE DOCUMENTOS DE SOLICITANTES DE ASILO"


class Steps(enum.Enum):
    start = "start"
    askCity = "askCity"
    askNie = "askNie"
    askNameSurname = "askNameSurname"
    askYearOfBirth = "askYearOfBirth"
    askCountry = "askCountry"


class Provinces(str, enum.Enum):
    Alicante = "3"
    Murcia = "30"


@dataclass
class Data(object):
    doc_value: str
    name: str
    year_of_birth: str
    country: str
    phone: str
    email: str


@dataclass
class DriverSettings:
    headless: bool = False
    proxy: bool = False


@dataclass
class Task(object):
    tramite: Tramites
    province: str
    nie: str
    nameSurname: str
    yearOfBirth: str
    country: str
