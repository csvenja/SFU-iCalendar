#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, Response
from grabber import sfu

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/grab', methods=['POST'])
def grab():
    student_name, calendar = sfu(request.form['username'], request.form['password'], request.form['alert'])
    headers = {'Content-Disposition': 'attachment; filename=' + student_name}
    return Response(calendar, headers=headers, mimetype='text/calendar')

if __name__ == '__main__':
    app.run()
