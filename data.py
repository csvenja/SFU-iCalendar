from pytz import timezone
from datetime import datetime

term = 1144

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
    'class_frame': 'ACE_$ICField75$0',
    'student_name': 'DERIVED_SSE_DSP_PERSON_NAME',
    'name': 'win1divDERIVED_SSE_DSP_CLASS_DESCR$',
    'status': 'PSXLATITEM_XLATSHORTNAME$',
    'section': 'CLASS_TBL_VW_CLASS_SECTION$',
    'component': 'PSXLATITEM_XLATSHORTNAME$102$$',
    'description': 'CLASS_TBL_VW_DESCR$',
    'lesson_table': 'ACE_$ICField117$',
    'start_time': 'CLASS_MTG_VW_MEETING_TIME_START$',
    'end_time': 'CLASS_MTG_VW_MEETING_TIME_END$',
    'days': 'DERIVED_SSE_DSP_CLASS_MTG_DAYS$',
    'location': 'DERIVED_SSE_DSP_DESCR40$',
    'start_date': 'DERIVED_SSE_DSP_START_DT$',
    'end_date': 'DERIVED_SSE_DSP_END_DT$',
    'instructor': 'PERSONAL_VW_NAME$142$$',
}


def frame_address(student_number):
    return class_frame_address[0] + student_number + class_frame_address[1] + str(term) + class_frame_address[2]


# parse string to date
def datelize(date_string):
    new_date = datetime.strptime(date_string, '%Y/%m/%d')  # e.g. 2014/01/28
    return new_date.date()


# parse string to time
def timelize(time_string):
    new_time = datetime.strptime(time_string, '%I:%M%p')  # e.g. 6:00AM
    return new_time.time()

def time_zone(t):
    new_t = t.replace(tzinfo=timezone('Canada/Pacific'))
    return new_t
