#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, Response, flash, redirect, url_for
from grabber import sfu, LoginError
from data import get_years

app = Flask(__name__)
app.secret_key = '8g789erobgyekhlwctybgwy4j93xft6'


@app.route('/')
def index():
    return render_template('index.html', years=get_years())


@app.route('/grab', methods=['POST'])
def grab():
    try:
        student_name, calendar = sfu(request.form['username'], request.form['password'], request.form['alert'], request.form['year'], request.form['semester'])
    except (LoginError, ValueError) as e:
        flash(e.error)
        return redirect(url_for('index'))
    else:
        headers = {'Content-Disposition': 'attachment; filename=' + student_name}
        return Response(calendar, headers=headers, mimetype='text/calendar')

if __name__ == '__main__':
    app.run()
