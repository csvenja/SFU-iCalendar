from pytz import timezone
from datetime import datetime

# change weekdays to numbers for datetime.weekday()
weekdays = {
    'MO': 0,
    'TU': 1,
    'WE': 2,
    'TH': 3,
    'FR': 4,
    'SA': 5,
    'SU': 6,
}

login_address = 'https://go.sfu.ca/psp/paprd/EMPLOYEE/EMPL/?cmd=login'

homepage_address = 'https://go.sfu.ca/psp/paprd/EMPLOYEE/EMPL/h/?cmd=getCachedPglt&pageletname=SFU_STU_CENTER_PAGELET&tab=SFU_STUDENT_CENTER&PORTALPARAM_COMPWIDTH=Narrow&ptlayout=N'

class_frame_address = [
    'https://sims-prd.sfu.ca/psc/csprd_1/EMPLOYEE/HRMS/c/SA_LEARNER_SERVICES.SS_ES_STUDY_LIST.GBL?Page=SS_ES_STUDY_LIST&Action=U&ACAD_CAREER=UGRD&EMPLID=',
    '&INSTITUTION=SFUNV&STRM=',
    '&TargetFrameName=None'
]

id = {
    'student_number': 'DERIVED_SSS_SCL_EMPLID',
    'class_frame': 'ACE_$ICField76$0',
    'student_name': 'DERIVED_SSE_DSP_PERSON_NAME',
    'name': 'win1divDERIVED_SSE_DSP_CLASS_DESCR$',
    'status': 'PSXLATITEM_XLATSHORTNAME$',
    'section': 'CLASS_TBL_VW_CLASS_SECTION$',
    'component': 'PSXLATITEM_XLATSHORTNAME$103$$',
    'description': 'CLASS_TBL_VW_DESCR$',
    'lesson_table': 'ACE_$ICField118$',
    'start_time': 'CLASS_MTG_VW_MEETING_TIME_START$',
    'end_time': 'CLASS_MTG_VW_MEETING_TIME_END$',
    'days': 'DERIVED_SSE_DSP_CLASS_MTG_DAYS$',
    'location': 'DERIVED_SSE_DSP_DESCR40$',
    'start_date': 'DERIVED_SSE_DSP_START_DT$',
    'end_date': 'DERIVED_SSE_DSP_END_DT$',
    'instructor': 'PERSONAL_VW_NAME$141$$',
}


def get_years():
    today = datetime.today()
    cur_year = today.year
    cur_month = today.month
    year_limit = cur_year + 1
    if cur_month >= 11:  # enroll for new year semester begins at November
        year_limit += 1
    years = range(2014, year_limit)
    years.reverse()  # reverse year list, set default to current year
    return years


def get_term(year, semester):
    term = str(1) + year[2:4] + semester
    return term


# get frame address based on student number and term(year, season)
def frame_address(student_number, term):
    return class_frame_address[0] + student_number + class_frame_address[1] + term + class_frame_address[2]


# parse string to date
def datelize(date_string):
    new_date = datetime.strptime(date_string, '%Y/%m/%d')  # e.g. 2014/01/28
    return new_date.date()


# parse string to time
def timelize(time_string):
    new_time = datetime.strptime(time_string, '%I:%M%p')  # e.g. 6:00AM
    return new_time.time()


def time_zone(time):
    new_time = time.replace(tzinfo=timezone('Canada/Pacific'))
    return new_time


holidays = {
    # holidays via http://www.sfu.ca/students/calendar/2014/summer/academic-dates/2014.html
    '2014': [
        datelize('2014/01/01'),  # New Year's Day
        datelize('2014/02/10'),  # Family Day in B.C.
        datelize('2014/05/19'),  # Victoria Day
        datelize('2014/07/01'),  # Canada Day
        datelize('2014/08/04'),  # B.C. Day
        datelize('2014/09/01'),  # Labour Day
        datelize('2014/10/13'),  # Thanksgiving
        datelize('2014/11/11'),  # Remembrance Day
    ],
    # holidays via http://www.sfu.ca/students/calendar/2015/spring/academic-dates/2015.html
    '2015': [
        datelize('2015/01/01'),  # New Year's Day
        datelize('2015/02/09'),  # Family Day in B.C.
        datelize('2015/02/10'),  # Reading break
        datelize('2015/02/11'),  # Reading break
        datelize('2015/02/12'),  # Reading break
        datelize('2015/02/13'),  # Reading break
        datelize('2015/02/14'),  # Reading break
        datelize('2015/04/03'),  # Good Friday
        datelize('2015/04/06'),  # Easter break
        datelize('2015/05/18'),  # Victoria Day
        datelize('2015/07/01'),  # Canada Day
        datelize('2015/08/03'),  # B.C. Day
        datelize('2015/09/07'),  # Labour Day
        datelize('2015/10/12'),  # Thanksgiving
        datelize('2015/11/11'),  # Remembrance Day
    ],
    # holidays via http://www.sfu.ca/students/calendar/2015/spring/academic-dates/2016.html
    '2016': [
        datelize('2016/01/01'),  # New Year's Day
        datelize('2016/02/08'),  # Family Day in B.C.
        datelize('2016/02/09'),  # Reading break
        datelize('2016/02/10'),  # Reading break
        datelize('2016/02/11'),  # Reading break
        datelize('2016/02/12'),  # Reading break
        datelize('2016/02/13'),  # Reading break
        datelize('2016/02/14'),  # Reading break
        datelize('2016/03/25'),  # Good Friday
        datelize('2016/03/28'),  # Easter Monday
        datelize('2016/05/23'),  # Victoria Day
        datelize('2016/07/01'),  # Canada Day
        datelize('2016/08/01'),  # B.C. Day
        datelize('2016/09/05'),  # Labour Day
        datelize('2016/10/10'),  # Thanksgiving
        datelize('2016/11/11'),  # Remembrance Day
    ],
    # holidays via http://www.sfu.ca/students/calendar/2015/spring/academic-dates/2017.html
    '2017': [
        datelize('2017/01/02'),  # New Year's Day
        datelize('2017/02/13'),  # Family Day in B.C.
        datelize('2017/02/14'),  # Reading break
        datelize('2017/02/15'),  # Reading break
        datelize('2017/02/16'),  # Reading break
        datelize('2017/02/17'),  # Reading break
        datelize('2017/02/18'),  # Reading break
        datelize('2017/02/19'),  # Reading break
        datelize('2017/04/14'),  # Good Friday
        datelize('2017/04/17'),  # Easter Monday
        datelize('2017/05/22'),  # Victoria Day
        datelize('2017/07/03'),  # Canada Day
        datelize('2017/08/07'),  # B.C. Day
    ]
}
