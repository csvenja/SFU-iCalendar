#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import getpass
import requests
import re
from bs4 import BeautifulSoup
import json

def sfu(username, password):
	def login(username, password):
		username_upper = username.upper()
		session = requests.Session()
		payload = {'user': username, 'pwd': password, 'httpPort': '', 'timezoneOffset': '480', 'userid': username_upper}
		session.post('https://go.sfu.ca/psp/paprd/EMPLOYEE/EMPL/?cmd=login', data=payload)
		return session
	
	def get_student_number(session):
		frame = session.get('https://go.sfu.ca/psp/paprd/EMPLOYEE/EMPL/h/?cmd=getCachedPglt&pageletname=SFU_STU_CENTER_PAGELET&tab=SFU_STUDENT_CENTER&PORTALPARAM_COMPWIDTH=Narrow&ptlayout=N')
		raw_page = BeautifulSoup(frame.text)
		student_number = raw_page.find(id='DERIVED_SSS_SCL_EMPLID').string
		return student_number
	
	def get_frame(session, student_number):
		frame = session.get('https://sims-prd.sfu.ca/psc/csprd_1/EMPLOYEE/HRMS/c/SA_LEARNER_SERVICES.SS_ES_STUDY_LIST.GBL?Page=SS_ES_STUDY_LIST&Action=U&ACAD_CAREER=UGRD&EMPLID='+student_number+'&INSTITUTION=SFUNV&STRM=1141&TargetFrameName=None')
		raw_page = BeautifulSoup(frame.text)
		class_frame = raw_page.find(id="ACE_$ICField68$0")
		return class_frame
		
	def generate_text(class_frame):
		soup_all = class_frame.find_all("span")
		text = []
		for item in soup_all:
			if len(item.string.strip()) > 0:
				text.append(item.string.strip())
		return text
		
	def generate_index(class_frame, text):
		soup_name = class_frame.find_all(title="Class Description")
		class_index = []
		for item in soup_name:
			class_index.append(text.index(item.string))
		class_count = len(class_index)
		class_index.append(len(text))
		return (class_index, class_count)

	def generate_lesson_item(text_item):
		lesson_item = {}
		lesson_item['start_time'] = text_item[0]
		lesson_item['end_time'] = text_item[1]
		lesson_item['days'] = text_item[2]
		lesson_item['location'] = text_item[3]
		lesson_item['start_date'] = text_item[4]
		lesson_item['end_date'] = text_item[5]
		if text_item[6] == 'Instructor:':
			lesson_item['instructor'] = text_item[7]
		return lesson_item

	def generate_class_item(text, class_index, class_i):
		start = class_index[class_i]
		end = class_index[class_i+1]
		current = start
		deleted = False
		class_item = {'lesson':[]}
		class_item['name'] = text[start].replace('  ', ' ')
		class_item['section'] = text[start+3]
		if text[start+4] == 'Section':
			deleted = True
			return (deleted, class_item)
		else:
			class_item['component'] = text[start+4]
		class_item['description'] = text[start+5]
		current = start + 12
		while current < end - 7:
			lesson_item = generate_lesson_item(text[current:current+8])
			class_item['lesson'].append(lesson_item)
			current = current + 9
		return (deleted, class_item)

	def dump(classes):
		print json.dumps(classes, ensure_ascii=False, indent=2)
		
	session = login(username, password)
	student_number = get_student_number(session)
	class_frame = get_frame(session, student_number)
	text = generate_text(class_frame)
	class_index, class_count = generate_index(class_frame, text)
	class_i = 0
	classes = []
	while class_i < class_count:
		deleted, class_item = generate_class_item(text, class_index, class_i)
		if not deleted:
			classes.append(class_item)
		class_i = class_i + 1
	dump(classes)

def main():
	username = raw_input('Username: ')
	password = getpass.getpass('Password: ')
	sfu(username, password)
		
if __name__ == '__main__':
	main()