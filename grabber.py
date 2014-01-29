#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import getpass
import os.path
from uuid import uuid1
import requests
from bs4 import BeautifulSoup
from icalendar import Calendar, Event
from datetime import datetime, date, time
from pytz import timezone
import json

def sfu(username, password):
	def login(username, password):
		username_upper = username.upper()
		session = requests.Session()
		payload = {'user': username, 'pwd': password, 'httpPort': '', 'timezoneOffset': '480', 'userid': username_upper}
		session.post('https://go.sfu.ca/psp/paprd/EMPLOYEE/EMPL/?cmd=login', data=payload)
		return session

	# student number is needed in extracting frame
	def get_student_number(session):
		frame = session.get('https://go.sfu.ca/psp/paprd/EMPLOYEE/EMPL/h/?cmd=getCachedPglt&pageletname=SFU_STU_CENTER_PAGELET&tab=SFU_STUDENT_CENTER&PORTALPARAM_COMPWIDTH=Narrow&ptlayout=N')
		raw_page = BeautifulSoup(frame.text)
		student_number = raw_page.find(id='DERIVED_SSS_SCL_EMPLID').string
		return student_number
	
	# extract frame
	def get_frame(session, student_number):
		frame = session.get('https://sims-prd.sfu.ca/psc/csprd_1/EMPLOYEE/HRMS/c/SA_LEARNER_SERVICES.SS_ES_STUDY_LIST.GBL?Page=SS_ES_STUDY_LIST&Action=U&ACAD_CAREER=UGRD&EMPLID='+student_number+'&INSTITUTION=SFUNV&STRM=1141&TargetFrameName=None')
		raw_page = BeautifulSoup(frame.text)
		class_frame = raw_page.find(id="ACE_$ICField68$0")
		student_name = raw_page.find(id='DERIVED_SSE_DSP_PERSON_NAME').string
		return (class_frame, student_name)
		
	# extract text
	def generate_text(class_frame):
		soup_all = class_frame.find_all("span")
		text = []
		for item in soup_all:
			if len(item.string.strip()) > 0:
				text.append(item.string.strip()) # remove empty lines
		return text

	# index class name to separate text for each class
	def generate_index(class_frame, text):
		soup_name = class_frame.find_all(title="Class Description")
		class_index = []
		for item in soup_name:
			class_index.append(text.index(item.string))
		class_count = len(class_index) # count class number for loop
		class_index.append(len(text)) # the last index acts as limit
		return (class_index, class_count)

	# change weekdays to numbers for datetime.weekday()
	weekdays = {
		'MO': 0,
		'TU': 1,
		'WE': 2,
		'TH': 3,
		'FR': 4,
		'SA': 5,
		'SU': 6
	}
	
	# parse text to lesson
	def generate_lesson_item(text_item):
		lesson_item = {}
		lesson_item['start_time'] = text_item[0]
		lesson_item['end_time'] = text_item[1]
		lesson_item['days'] = text_item[2].split(',')
		for day_i, value in enumerate(lesson_item['days']):
			lesson_item['days'][day_i] = value[0:2].upper() # icalendar's byday parameter receive "MO TU WE TH FR SA SU" format input
		lesson_item['location'] = text_item[3].replace(u'Location:  ', '') # remove redundant caption
		lesson_item['start_date'] = text_item[4]
		lesson_item['end_date'] = text_item[5]
		if len(text_item) > 6 and text_item[6] == 'Instructor:': # Final has only 6 lines lesson info
			lesson_item['instructor'] = text_item[7]
		return lesson_item

	# parse text to class
	def generate_class_item(text, class_index, class_i, class_count):
		if class_i == class_count - 1:
			last_class = True
		else:
			last_class = False
		start = class_index[class_i]
		end = class_index[class_i + 1]
		current = start
		deleted = False
		class_item = {'lessons':[]}
		class_item['name'] = text[start].replace('  ', ' ') # class name has two space between department and number
		class_item['section'] = text[start + 3]
		if text[start + 4] == 'Section': # Section classes have no scheduled lesson
			deleted = True
			return (deleted, class_item)
		else:
			class_item['component'] = text[start + 4]
		class_item['description'] = text[start + 5]
		if text[start + 8] != 'Enrolled':
			deleted = True
			return (deleted, class_item)
		current = start + 12 # 12 non-empty lines header for each class
		while (current < end - 7 and not last_class) or (current < end and last_class): # 7 captions for class info
			lesson_item = generate_lesson_item(text[current:current + 8]) # 8 lines for one lesson
			class_item['lessons'].append(lesson_item)
			current = current + 9 # move on 9 lines after one lesson
		return (deleted, class_item)

	# dump class info as a list of dictionary
	def dump(classes):
		print json.dumps(classes, ensure_ascii=False, indent=2)

	# parse string to date
	def datelize(date_string):
		new_date = datetime.strptime(date_string, '%Y/%m/%d') # e.g. 2014/01/28
		new_date = new_date.replace(tzinfo=timezone('Canada/Pacific'))
		return new_date.date()

	# parse string to time
	def timelize(time_string):
		new_time = datetime.strptime(time_string, '%I:%M%p') # e.g. 6:00AM
		new_time = new_time.replace(tzinfo=timezone('Canada/Pacific'))
		return new_time.time()
	
	# generate ics file
	def generate_ical():
		cal = Calendar()
		cal['version'] = '2.0'
		cal['prodid'] = '-//Simon Fraser University//Svenja Cao//EN'
		
		holidays = [datelize('2014/02/10')] # Family day in BC
		# more to update
		
		for class_item in classes:
			for lesson in class_item['lessons']:
				start_date = datelize(lesson['start_date'])
				start_time = timelize(lesson['start_time'])
				end_time = timelize(lesson['end_time'])
				start = datetime.combine(start_date, start_time) # class start datetime
				end = datetime.combine(start_date, end_time) # class end datetime
				end_date = datelize(lesson['end_date'])
				until = datetime.combine(end_date, end_time) # recurrence end datetime
				for day in lesson['days']:
					event = Event()
					if lesson['start_date'] == lesson['end_date']:
						# the lesson with same start and end date is the Final
						event.add('summary', class_item['name'] + ' Final')
					else:
						event.add('summary', class_item['name'] + ' ' + class_item['component'])
					event.add('dtstart', start)
					event.add('dtend', end)
					event.add('rrule', {'freq': 'weekly', 'byday': day, 'until': until, 'wkst': 'SU'})
					# byday doesn't support list for now
					event.add('location', lesson['location'])
					if 'instructor' in lesson:
						event.add('description', 'Instructor: ' + lesson['instructor'] + '\nDescription: ' + class_item['description'] + '\nSection: ' + class_item['section'])
					else:
						event.add('description', 'Description: ' + class_item['description'] + '\nSection: ' + class_item['section'])
						# the Final has no instructor

					if start_date.weekday() == weekdays[day]:
						# if a course has class on first day, the first day won't be ignored
						# see weekdays{}
						exdates = []
					else:
						exdates = [start]
					for holiday in holidays:
						exdates.append(datetime.combine(holiday, start_time))
					event.add('exdate', exdates)
					
					event['uid'] = str(uuid1()) + '@SFU'
					cal.add_component(event)
		return cal.to_ical()

	# main
	session = login(username, password)
	student_number = get_student_number(session)
	class_frame, student_name = get_frame(session, student_number)
	text = generate_text(class_frame)
	class_index, class_count = generate_index(class_frame, text)
	class_i = 0
	classes = []
	while class_i < class_count:
		deleted, class_item = generate_class_item(text, class_index, class_i, class_count)
		if not deleted:
			# delete all 'Section' classes and not enrolled classes
			classes.append(class_item)
		class_i = class_i + 1
	with open(os.path.join(os.path.dirname(__file__), student_name + '.ics'), 'w') as ical:
		ical.write(generate_ical())
	print "Dumped successfully."
	# dump(classes)

def main():
	username = raw_input('Username: ')
	password = getpass.getpass('Password: ')
	sfu(username, password)
			
if __name__ == '__main__':
	main()
