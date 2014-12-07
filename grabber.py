#!/usr/bin/env python
# -*- coding: utf-8 -*-

import getpass
import os.path
from uuid import uuid1
import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event, Alarm
from datetime import datetime, timedelta
import json
import data


class LoginError(Exception):
    """docstring for LoginError"""
    def __init__(self, error):
        self.error = error

    def __str__(self):
        return 'LoginError: {}'.format(self.error)


def sfu(username, password, alert, year, semester):
    def login(username, password):
        username_upper = username.upper()
        session = requests.Session()
        payload = {'user': username, 'pwd': password, 'httpPort': '', 'timezoneOffset': '480', 'userid': username_upper}
        session.post(data.login_address, data=payload)
        return session

    def get_student_number(session):
        """student number is needed in extracting frame"""
        frame = session.get(data.homepage_address)
        raw_page = BeautifulSoup(frame.text)
        student_number = raw_page.find(id=data.id['student_number'])
        if student_number:
            return student_number.string
        else:
            raise LoginError('Wrong username or password.')

    def get_frame(session, student_number, term):
        """extract frame"""
        frame = session.get(data.frame_address(student_number, term))
        raw_page = BeautifulSoup(frame.text)
        class_frame = raw_page.find(id=data.id['class_frame'])
        student_name = raw_page.find(id=data.id['student_name']).string
        return (class_frame, student_name)

    def get_class_frame(username, password, term):
        session = login(username, password)
        student_number = get_student_number(session)
        return get_frame(session, student_number, term)

    def generate_lessons(lesson_table, lesson_i):
        lessons = []
        while True:
            current_lesson_start_time = lesson_table.find(id=data.id['start_time'] + str(lesson_i))
            if current_lesson_start_time:
                if current_lesson_start_time.string.strip() != '':
                    current_lesson = {}
                    current_lesson['start_time'] = current_lesson_start_time.string
                    current_lesson['end_time'] = lesson_table.find(id=data.id['end_time'] + str(lesson_i)).string
                    current_lesson['start_date'] = lesson_table.find(id=data.id['start_date'] + str(lesson_i)).string
                    current_lesson['end_date'] = lesson_table.find(id=data.id['end_date'] + str(lesson_i)).string
                    current_lesson['location'] = lesson_table.find(id=data.id['location'] + str(lesson_i)).string.replace(u'Location:  ', '')
                    if lesson_table.find(id=data.id['instructor'] + str(lesson_i)):
                        current_lesson['instructor'] = lesson_table.find(id=data.id['instructor'] + str(lesson_i)).string
                    current_lesson['days'] = lesson_table.find(id=data.id['days'] + str(lesson_i)).string.split(',')
                    for day_i, value in enumerate(current_lesson['days']):
                        current_lesson['days'][day_i] = value[0:2].upper()
                    lessons.append(current_lesson)
                lesson_i = lesson_i + 1
            else:
                break
        return (lessons, lesson_i)

    def dump(classes):
        """dump class info as a list of dictionary"""
        print json.dumps(classes, ensure_ascii=False, indent=2)

    def generate_ical():
        """generate ics file"""
        cal = Calendar()
        cal['version'] = '2.0'
        cal['prodid'] = '-//Simon Fraser University//Svenja Cao//EN'

        for class_item in classes:
            for lesson in class_item['lessons']:
                start_date = data.datelize(lesson['start_date'])
                start_time = data.timelize(lesson['start_time'])
                end_time = data.timelize(lesson['end_time'])
                start = data.time_zone(datetime.combine(start_date, start_time))  # class start datetime
                end = data.time_zone(datetime.combine(start_date, end_time))  # class end datetime
                end_date = data.datelize(lesson['end_date'])
                until = datetime.combine(end_date, end_time)  # recurrence end datetime
                for day in lesson['days']:
                    event = Event()
                    if lesson['start_date'] == lesson['end_date']:
                        # the lesson with same start and end date is the Exam
                        event.add('summary', class_item['name'] + ' Exam')
                    else:
                        event.add('summary', class_item['name'] + ' ' + class_item['component'])
                    event.add('dtstart', start)
                    event.add('dtend', end)
                    event.add('rrule', {'freq': 'weekly', 'byday': day, 'until': until, 'wkst': 'SU'})
                    # byday doesn't support list for now
                    event.add('location', lesson['location'])
                    description = 'Description: ' + class_item['description'] + '\nSection: ' + class_item['section']
                    if 'instructor' in lesson:  # the Final has no instructor
                        description = 'Instructor: ' + lesson['instructor'] + '\n' + description
                    event.add('description', description)

                    if start_date.weekday() == data.weekdays[day]:
                        # if a course has class on first day, the first day won't be ignored
                        # see weekdays{}
                        exdates = []
                    else:
                        exdates = [start]
                    for holiday in data.holidays[year]:
                        exdates.append(datetime.combine(holiday, start_time))
                    event.add('exdate', exdates)

                    if alert and unicode(alert).isnumeric():
                        alarm = Alarm()
                        alarm.add('action', 'DISPLAY')

                        alert_time = timedelta(minutes=-int(alert))
                        alarm.add('trigger', alert_time)
                        event.add_component(alarm)

                    event['uid'] = str(uuid1()) + '@SFU'
                    cal.add_component(event)
        return cal.to_ical()

    term = data.get_term(year, semester)
    class_frame, student_name = get_class_frame(username, password, term)
    class_i = 0
    lesson_i = 0
    classes = []
    while True:
        current_class_description = class_frame.find(id=data.id['name'] + str(class_i))
        if current_class_description:
            status = class_frame.find(id=data.id['status'] + str(class_i)).string
            current_class = {}
            current_class['name'] = current_class_description.span.string.replace('  ', ' ')
            current_class['component'] = class_frame.find(id=data.id['component'] + str(class_i)).string
            current_class['section'] = class_frame.find(id=data.id['section'] + str(class_i)).string
            current_class['description'] = class_frame.find(id=data.id['description'] + str(class_i)).string
            lesson_table = class_frame.find(id=data.id['lesson_table'] + str(class_i))
            current_class['lessons'], lesson_i = generate_lessons(lesson_table, lesson_i)
            if(len(current_class['lessons']) > 0 and status == 'Enrolled'):
                classes.append(current_class)
            class_i = class_i + 1
        else:
            break
    return (student_name, generate_ical())
    # dump(classes)


if __name__ == '__main__':
    username = raw_input('Username: ')
    password = getpass.getpass('Password: ')
    year = raw_input('Year (2015):')
    semester = raw_input('Semester (Spring/Summer/Fall):')
    alert = raw_input('Alert before (minutes, enter to skip): ')
    try:
        student_name, calendar = sfu(username, password, alert, year, semester)
    except LoginError as e:
        print e.error
    else:
        with open(os.path.join(os.path.dirname(__file__), student_name + '.ics'), 'w') as ical:
            ical.write(calendar)
            print 'Dumped successfully.'
