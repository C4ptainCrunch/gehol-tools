#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import base64
import ics
import hashlib
import re
import os

from flask import (Flask, render_template, request,
    session, redirect, Response, abort)

import gehol

# should have a DOMAIN (eg "http://127.0.0.1:5000/" with trailing "/"),
# MAX_URL (eg 10), KEY (eq "wskj§gbqé(JHtzMK|§JFHQg$`ù"), DEBUG (eg True)
# and ROOT_DIR (eg "/home/nginx/gehol/")
from config import *


app = Flask(__name__)
app.secret_key = KEY

DATA_DIR = os.path.join(ROOT_DIR, "data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


def is_md5(string):
    validHash = re.finditer(r'(?=(\b[A-Fa-f0-9]{32}\b))', string)
    result = [match.group(1) for match in validHash]
    return bool(result)


@app.route("/")
def index():
    return render_template('index.html')


@app.route('/filter', methods=['POST', 'GET'])
def filter():
    if request.method == 'POST':
        if request.form['urls']:
            urls = request.form['urls'].strip().split('\n')
            if len(urls) > MAX_URL:
                return "Too many URLs"

            titles = set()
            for url in urls:
                titles |= gehol.extract_names(gehol.get_cal(url))

            persist = json.dumps(urls)
            return render_template('filter.html', titles=titles, persist=base64.b64encode(persist))
        else:
            return "Form was empty"


@app.route('/makeurl', methods=['POST', 'GET'])
def makecal():
    if request.method == 'POST':
        selected = request.form.getlist('name')
        urls = json.loads(base64.b64decode(request.form['persist']))

        if len(urls) > 10:
                return "Too many URLs"

        save_dict = {'urls': urls, 'selected': selected}
        save_str = json.dumps(save_dict)

        h = hashlib.md5(save_str).hexdigest()
        with open(os.path.join(DATA_DIR, '{}'.format(h)), 'w') as f:
            f.write(save_str)

        return redirect('/url/{}'.format(h))


@app.route('/url/<h>')
def url(h):
    if not is_md5(h):
        raise ValueError('Param should be a md5 string')

    return render_template('url.html', DOMAIN=DOMAIN, h=h)


@app.route('/cal/<h>.ics')
def getcal(h):
        if not is_md5(h):
            raise ValueError('Param should be a md5 string')
        try:
            with open(os.path.join(DATA_DIR, '{}'.format(h))) as f:
                j = f.read()
        except IOError:
            return abort(404)
        data = json.loads(j)
        urls, selected = data['urls'], data['selected']

        cal = ics.Calendar()
        for url in urls:
            cal.events = cal.events + gehol.get_cal(url).events
        cal = gehol.filter_events(cal, selected)

        resp = Response(response=str(cal),
                    mimetype="text/calendar")

        return resp

if __name__ == "__main__":
    app.run(debug=DEBUG)
