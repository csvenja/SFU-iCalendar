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


def sfu(username, password, alert):
    def login(username, password):
        username_upper = username.upper()
        session = requests.Session()
        payload = {'user': username, 'pwd': password, 'httpPort': '', 'timezoneOffset': '480', 'userid': username_upper}
        session.post(data.login_address, data=payload)
        return session

    # student number is needed in extracting frame
    def get_student_number(session):
        frame = session.get(data.homepage_address)
        raw_page = BeautifulSoup(frame.text)
        student_number = raw_page.find(id=data.id['student_number']).string
        return student_number

    # extract frame
    def get_frame(session, student_number):
        frame = session.get(data.frame_address(student_number))
        raw_page = BeautifulSoup(frame.text)
        class_frame = raw_page.find(id=data.id['class_frame'])
        student_name = raw_page.find(id=data.id['student_name']).string
        return (class_frame, student_name)

    def get_class_frame(username, password):
        session = login(username, password)
        student_number = get_student_number(session)
        return get_frame(session, student_number)

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

    # dump class info as a list of dictionary
    def dump(classes):
        print json.dumps(classes, ensure_ascii=False, indent=2)

    # generate ics file
    def generate_ical():
        cal = Calendar()
        cal['version'] = '2.0'
        cal['prodid'] = '-//Simon Fraser University//Svenja Cao//EN'

        # holidays via http://www.sfu.ca/students/calendar/2014/summer/academic-dates/2014.html
        holidays = [
            data.datelize('2014/01/11'),  # New Year's Day
            data.datelize('2014/02/10'),  # Family Day in B.C.
            data.datelize('2014/05/19'),  # Victoria Day
            data.datelize('2014/07/01'),  # Canada Day
            data.datelize('2014/08/04'),  # B.C. Day
            data.datelize('2014/09/01'),  # Labour Day
            data.datelize('2014/10/13'),  # Thanksgiving
            data.datelize('2014/11/11'),  # Remembrance Day
        ]

        for class_item in classes:
            for lesson in class_item['lessons']:
                start_date = data.datelize(lesson['start_date'])
                start_time = data.timelize(lesson['start_time'])
                end_time = data.timelize(lesson['end_time'])
                start = datetime.combine(start_date, start_time)  # class start datetime
                end = datetime.combine(start_date, end_time)  # class end datetime
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
                    for holiday in holidays:
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

    # main
    class_frame, student_name = get_class_frame(username, password)
    class_i = 0
    lesson_i = 0
    classes = []
    while True:
        current_class_description = class_frame.find(id=data.id['name'] + str(class_i))
        if current_class_description:
            status = class_frame.find(id=data.id['status'] + str(class_i)).string
            if status == 'Enrolled':
                current_class = {}
                current_class['name'] = current_class_description.span.string.replace('  ', ' ')
                current_class['component'] = class_frame.find(id=data.id['component'] + str(class_i)).string
                current_class['section'] = class_frame.find(id=data.id['section'] + str(class_i)).string
                current_class['description'] = class_frame.find(id=data.id['description'] + str(class_i)).string
                lesson_table = class_frame.find(id=data.id['lesson_table'] + str(class_i))
                current_class['lessons'], lesson_i = generate_lessons(lesson_table, lesson_i)
                if(len(current_class['lessons']) > 0):
                    classes.append(current_class)
            class_i = class_i + 1
        else:
            break
    with open(os.path.join(os.path.dirname(__file__), student_name + '-' + str(data.term) + '.ics'), 'w') as ical:
        ical.write(generate_ical())
    print "Dumped successfully."
#    dump(classes)

if __name__ == '__main__':
    username = raw_input('Username: ')
    password = getpass.getpass('Password: ')
    alert = raw_input('Alert before (minutes, enter to skip): ')
    sfu(username, password, alert)
