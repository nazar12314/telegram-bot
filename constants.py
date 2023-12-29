from enum import Enum


class Buttons(Enum):
    # Main page
    ASTROLOGY = 'Астрология'
    OFFICE = 'Кабинет'
    OWN_BOT = 'Личный бот'
    ABOUT = 'О проекте'
    REFERENCE = 'Справочник'

    # Zodiac signs
    ARIES = 'Овен'
    CANCER = 'Рак'
    LIBRA = 'Весы'
    CAPRICORN = 'Козерог'
    TAURUS = 'Телец'
    LEO = 'Лев'
    SCORPIO = 'Скорпион'
    AQUARIUS = 'Водолей'
    GEMINI = 'Близнецы'
    VIRGO = 'Дева'
    SAGITTARIUS = 'Стрелец'
    PISCES = 'Рыбы'

    # Eastern zodiac signs
    RAT = 'Крыса'
    BULL = 'Бык'
    TIGER = 'Тигр'
    RABBIT = 'Кролик'
    DRAGON = 'Дракон'
    SNAKE = 'Змея'
    HORSE = 'Лошадь'
    MONKEY = 'Обезьяна'
    GOAT = 'Коза'
    ROOSTER = 'Петух'
    DOG = 'Собака'
    PIG = 'Свинья'

    BACK = 'Назад'
    CONTINUE = 'Пропустить'

    CHANGE_ZODIAC_SIGN = 'Сменить знак зодиака'
    PERSON_DESIGN = 'Дизайн личности'
    CHANGE_EAST_ZODIAC = 'Сменить восточный знак зодиака'
    MAIN_PAGE_BACK = 'На главную'

    # Horoscopes
    HOROSCOPE = 'Гороскоп'
    EAST_HOROSCOPE = 'Восточный гороскоп'
    HOROSCOPE_FOR_TODAY = 'На сегодня'
    HOROSCOPE_FOR_MONTH = 'На месяц'
    HOROSCOPE_FOR_YEAR = 'На год'

    # Admin
    ADMIN = 'Админка'
    PRESENT_USERS = 'Пользователи'
    LEFT_USERS = 'Отписки'
    ADVERT = 'Объявление'


class States(Enum):
    ZODIAC_SIGN = 1
    EAST_ZODIAC_SIGN = 2
    MAIN_PAGE = 3
    OFFICE = 4
    ABOUT = 5
    ASTROLOGY = 6
    PERSONAL_DESIGN = 7

    CHANGE_ZODIAC_SIGN = 8
    ZODIAC_CHANGED = 9

    CHANGE_EAST_ZODIAC_SIGN = 10
    EAST_ZODIAC_CHANGED = 11

    HOROSCOPE = 12
    CHANGE_ZODIAC_SIGN_ASTROLOGY = 13

    EAST_HOROSCOPE = 14
    CHANGE_EAST_ZODIAC_SIGN_ASTROLOGY = 15

    ADMIN_PANEL = 16
    ADVERT_TEXT = 17
    ADVERT_IMAGE = 18


EASTERN_ZODIAC_SIGNS = {'Крыса', 'Бык', 'Тигр', 'Кролик', 'Дракон', 'Змея', 'Лошадь', 'Коза', 'Обезьяна', 'Петух', 'Собака', 'Свинья'}
ZODIAC_SIGNS = {"Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"}