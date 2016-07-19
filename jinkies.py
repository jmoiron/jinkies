#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Jinkies is a command line jenkins program.

Usage:
    jinkies list (jobs|views)
    jinkies show <view>
    jinkies build <job> [<args>...]
    jinkies params <job>
    jinkies view <job>
    jinkies status <job>
    jinkies --config

Options:
    -h --help       Show this help.
    --version       Show version and exit.
    --config        Show config and exit.
"""

import sys
import os
import re
import cookielib
import requests
import docopt
import time
from pprint import pformat

url_help = """Please set JENKINS_URL to the url to your jenkins instance.

If your jenkins is behind a login, you can first go to:
    https://jenkins/user/<yourname>/configure

And get a token by clicking "Show API Token", and then use a URL like:
    https://<yourname>:<yourtoken>@jenkins/
"""

URL=""

def damnit(string):
    if isinstance(string, str):
        string = string.decode("utf-8").encode("utf-8")
    if isinstance(string, unicode):
        string = string.encode("utf-8")
    return string

white,black,red,green,yellow,blue,purple = range(89,96)
def color(string, color=green, bold=False, underline=False):
    """Usage: color("foo", red, bold=True)"""
    s = '01;' if bold else '04;' if underline else ''
    return '\033[%s%sm' % (s, color) + str(damnit(string)) + '\033[0m'

# boo
spre = re.compile(r'<span style="color: #(?P<color>[0-9A-F]{6});">(?P<txt>.*?)</span>')
are = re.compile(r'<a href=.*?>(?P<txt>.*?)</a>')
spnre = re.compile(r'<span.*?>(?P<txt>.*?)</span>')
bre = re.compile(r'<b>(?P<txt>.*?)</b>')

colmap = {
    '00CDCD': lambda s: color(s, color=blue, bold=True),
    'CDCD00': lambda s: color(s, color=yellow, bold=True),
    '00CD00': lambda s: color(s, color=green, bold=True),
    'CD0000': lambda s: color(s, color=red, underline=False),
    'E5E5E5': lambda s: color(s, color=white, bold=True),
    'link': lambda s: color(s, color=red, underline=True),
    'bold': lambda s: color(s, color=white, bold=True),
    '': lambda s: s,
}

resmap = {
    'SUCCESS': color('✓'),
    'FAILURE': color('✗', color=red),
    'default': color('?', color=yellow),
}

def colorize(text):
    def rep(default):
        def inner(group):
            d = group.groupdict()
            color = d.get('color', default)
            txt = d.get('txt', '')
            return colmap[color](txt)
        return inner
    s = damnit(text)
    s, _ = spre.subn(rep(''), s)
    s, _ = spnre.subn(rep(''), s)
    s, _ = are.subn(rep('link'), s)
    s, _ = bre.subn(rep('bold'), s)
    s = s.replace('&gt;', '>')
    s = s.replace('&lt;', '<').lstrip()
    return s

def main():
    global URL
    args = docopt.docopt(__doc__, version="1.0")
    if os.getenv("JENKINS_URL"):
        URL = os.getenv("JENKINS_URL")
    if not URL:
        print url_help
        return
    if args['--config']:
        print "URL: %s" % (URL)
        return
    if args['list']:
        return cmd_list(args)
    elif args['show']:
        return cmd_show(args)
    elif args['build']:
        return cmd_build(args)
    elif args['params']:
        return cmd_params(args)
    elif args['view']:
        return cmd_view(args)
    elif args['status']:
        return cmd_status(args)

def print_job(job):
    print job['name']

def print_response_err(resp):
    print "Error: %s" % (resp)
    print resp.text

def cmd_list(args):
    url = "%s/api/json" % URL
    resp = requests.get(url)
    if not resp.ok:
        print_response_err(resp)
        return
    doc = resp.json()
    if args['jobs']:
        for job in doc['jobs']:
            print_job(job)
    elif args['views']:
        for view in doc['views']:
            print "%s: %s" % (view['name'], view['url'])

def cmd_show(args):
    url = "%s/view/%s/api/json" % (URL, args['<view>'])
    resp = requests.get(url)
    if not resp.ok:
        print_response_err(resp)
        return
    doc = resp.json()
    for job in doc['jobs']:
        print_job(job)

def cmd_status(args):
    job = args['<job>']
    url = "%s/job/%s/api/json?depth=1" % (URL, job)
    resp = requests.get(url)
    if not resp.ok:
        print_response_err(resp)
        return
    doc = resp.json()
    # print the job and a short description (first line)
    print "%s: %s" % (doc.get("displayName", job), doc.get("description", "").split("\n")[0])
    # print the last 7 runs and their statuses
    for d in doc.get("builds", [])[:7]:
        ts = time.ctime(d["timestamp"]/1000).strip()
        rs = d.get("result", "default")
        if rs not in ('SUCCESS', 'FAILURE', 'default'):
            print 'new result type: %s' % rs
            rs = 'default'
        result = resmap[rs]
        minutes = d["duration"] / 1000 / 60
        seconds = d["duration"] / 1000 % 60
        print " %s #%d %s in %d:%d" % (result, d["number"], ts, minutes, seconds)


def cmd_view(args):
    job = args['<job>']
    url = "%s/job/%s/api/json?depth=1" % (URL, job)
    resp = requests.get(url)
    if not resp.ok:
        print_response_err(resp)
        return
    doc = resp.json()
    # print the job and a short description (first line)
    print "%s: %s" % (doc.get("displayName", job), doc.get("description", "").split("\n")[0])
    # print the last 3 runs and their statuses
    for d in doc.get("builds", [])[:3]:
        ts = time.ctime(d["timestamp"]/1000).strip()
        rs = d.get("result", "default")
        if rs not in ('SUCCESS', 'FAILURE', 'default'):
            print 'new result type: %s' % rs
            rs = 'default'
        result = resmap[rs]
        minutes = d["duration"] / 1000 / 60
        seconds = d["duration"] / 1000 % 60
        print " %s #%d %s in %d:%d" % (result, d["number"], ts, minutes, seconds)


    # if there is a queued job, lets wait for it to start
    if doc['inQueue']:
        next = doc['nextBuildNumber']
        watch(URL, job, next)
        return

    previous = doc['lastBuild']
    previousFinished = doc['lastCompletedBuild']

    if previous['number'] == previousFinished['number']:
        print "Showing previous build %d" % previous['number']
        print '\n'.join(get_console(job, previous['number']))
        print ""
        print "Showed previous build:"
        print "%s/job/%s/%s" % (URL, job, previous['number'])
        return

    watch(URL, job, previous['number'])


def watch(URL, job, build):
    """Watch console output for a job.  In the event that it hasn't begun yet
    (eg. it is queued), wait for it to start and then watch the output."""
    console = lambda: get_console(job, build)

    first = True
    firstWait = True
    url = "%s/job/%s/%s/api/json" % (URL, job, build)
    cp = 0
    failures = 0
    waits = 0
    while 1:
        try:
            resp = requests.get(url)
        except requests.exceptions.ConnectionError:
            if failures > 5:
                print "Failure loading job for %s" % (job)
                return
            failures += 1
            continue
        if not resp.ok and first:
            r2 = requests.get("%s/job/%s/api/json" % (URL, job))
            waits += 1
            if not r2.ok:
                print "Failure loading job for %s" % (job)
                print r2.data
                return
            d = r2.json()
            if d['inQueue']:
                if firstWait:
                    sys.stdout.write('Waiting in job queue .')
                    firstWait = False
                else:
                    sys.stdout.write('.')
                sys.stdout.flush()
                time.sleep(2.5)
            elif not resp.ok:
                failures += 1
                if failures > 5:
                    print "Failure loading job for %s" % (job)
                    return
            continue
        if first and (failures or waits):
            print ""
        doc = resp.json()
        if first:
            print "Started build #%d, ETA %.1fs" % (build, doc['estimatedDuration']/1000.0)
            first = False
        cons = console()
        if len(cons) > cp:
            toprint = filter(None, [c.strip("\r").strip("\n") for c in cons[cp:]])
            if toprint:
                print "\n".join(toprint)
                cp = len(cons)-1
        if not doc['building']:
            print doc['result']
            return
        time.sleep(1.5)

def get_console(job, build):
    resp = requests.get("%s/job/%s/%s/logText/progressiveHtml" % (URL, job, build))
    if not resp.ok:
        return []
    text = colorize(resp.text)
    lines = [l.lstrip() for l in text.split("\n")]
    return lines

def cmd_params(args):
    job = args['<job>']
    url = "%s/job/%s/api/json" % (URL, job)
    resp = requests.get(url)
    if not resp.ok:
        print_response_err(resp)
        return
    doc = resp.json()
    options = _param_defs_from_job(doc)
    if len(options) == 0:
        print "No params necessary."
        return
    for opt in options:
        choices = opt.get('choices', [])
        name = opt['name']
        print "%s: %s" % (name, ', '.join(choices))

def cmd_build(args):
    # first, fetch the job to figure out what the next build number is
    # this also lets us bail out if the job is invalid
    job = args['<job>']
    url = "%s/job/%s/api/json" % (URL, job)
    resp = requests.get(url)
    if not resp.ok:
        print_response_err(resp)
        return
    doc = resp.json()
    build = doc['nextBuildNumber']
    job_param_defs = _param_defs_from_job(doc)
    job_param_names = [p['name'] for p in job_param_defs]

    # now lets start the build job
    params = dict([p.split('=', 1) for p in args.get('<args>', [])])
    for p in params:
        if p not in job_param_names:
            print "Param '%s' isn't an option for this job." % p
            return
    if params:
        url = "%s/job/%s/buildWithParameters?delay=0sec" % (URL, job)
    else:
        url = "%s/job/%s/build?delay=0sec" % (URL, job)
    resp = requests.post(url, data=params)
    if not resp.ok:
        print "Error starting build:"
        print_response_err(resp)
        return

    watch(URL, job, build)


def _param_defs_from_job(job_json):
    for action in job_json['actions']:
        if 'parameterDefinitions' in action:
            return action['parameterDefinitions']
    return []


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
