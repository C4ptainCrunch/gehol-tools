#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
from urllib2 import urlopen, HTTPError
from urlparse import urlparse

import ics


def get_cal(url):
    o = urlparse(url)
    if not o.scheme == 'http' or not (o.netloc == 'scientia-web.ulb.ac.be' or o.netloc == 'mongehol.ulb.ac.be'):
        raise ValueError('Must be an http gehol url.')

    i = 0
    while i < 10:
        i += 1
        try:
            content = urlopen(url).read()
        except HTTPError:
            time.sleep(3)
        else:
            content = content.decode('iso-8859-1')
            cal = ics.Calendar(content)
            break
    if i == 10:
        raise IOError('Gehol down')

    return cal


def extract_names(cal):
    return set(map(lambda x: x.name, cal.events))


def filter_events(cal, only):
    cal = cal.clone()
    cal.events = filter(lambda x: x.name in only, cal.events)
    return cal

def clean_cal(cal):
    for event in cal.events:
        if event.description == 'Professeur:  \\n Assistant':
            event.name += ' (TP)'
        event.description = ""
