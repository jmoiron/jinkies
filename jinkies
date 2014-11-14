#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Jinkies is a command line jenkins program.

Usage:
    jinkies list (jobs|views)
    jinkies show <view>
    jinkies build <job>
    jinkies --config

Options:
    -h --help       Show this help.
    --version       Show version and exit.
    --config        Show config and exit.
"""

cookie_help = """Get a valid jenkins session cookie by using dev tools:

> document.cookie

And then setting your JENKINS_COOKIE environment variable, eg:

$ export JENKINS_COOKIE="JSESSIONID.667a88d9=1dn2t...;"
$ export JENKINS_URL="https://foo.bar.com"
"""

import sys
import os
import cookielib
import requests
import docopt
import time
from pprint import pformat

COOKIE={}
URL="https://jenkins/"

def main():
    args = docopt.docopt(__doc__, version="1.0")
    global URL, COOKIE
    try:
        COOKIE = dict(cookielib.parse_ns_headers([os.getenv("JENKINS_COOKIE")])[0])
    finally:
        if not COOKIE:
            print cookie_help
            return
    if os.getenv("JENKINS_URL"):
        URL = os.getenv("JENKINS_URL")
    if args['--config']:
        print "COOKIE: %s" % (pformat(COOKIE))
        print "URL: %s" % (URL)
        return
    if args['list']:
        return cmd_list(args)
    elif args['show']:
        return cmd_show(args)
    elif args['build']:
        return cmd_build(args)

def print_job(job):
    print job['name']

def print_response_err(resp):
    print "Error: %s" % (resp)
    print resp.text

def cmd_list(args):
    url = "%s/api/json" % URL
    resp = requests.get(url, cookies=COOKIE)
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
    resp = requests.get(url, cookies=COOKIE)
    if not resp.ok:
        print_response_err(resp)
        return
    doc = resp.json()
    for job in doc['jobs']:
        print_job(job)

def cmd_build(args):
    # first, fetch the job to figure out what the next build number is
    # this also lets us bail out if the job is invalid
    job = args['<job>']
    url = "%s/job/%s/api/json" % (URL, job)
    resp = requests.get(url, cookies=COOKIE)
    if not resp.ok:
        print_response_err(resp)
        return
    doc = resp.json()
    build = doc['nextBuildNumber']

    # now lets start the build job
    url = "%s/job/%s/build?delay=0sec" % (URL, job)
    resp = requests.post(url, cookies=COOKIE)
    if not resp.ok:
        print "Error starting build:"
        print_response_err(resp)
        return

    first = True
    url = "%s/job/%s/%s/api/json" % (URL, job, build)
    while 1:
        resp = requests.get(url, cookies=COOKIE)
        if not resp.ok:
            print_response_err(resp)
            return
        doc = resp.json()
        if first:
            print "Started build #%d, ETA %.1fs" % (build, doc['estimatedDuration']/1000.0)
            first = False
        if not doc['building']:
            print doc['result']
            return
        time.sleep(2)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass