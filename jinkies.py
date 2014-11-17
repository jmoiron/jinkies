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

import sys
import os
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

    # now lets start the build job
    url = "%s/job/%s/build?delay=0sec" % (URL, job)
    resp = requests.post(url)
    if not resp.ok:
        print "Error starting build:"
        print_response_err(resp)
        return

    def console():
        resp = requests.get("%s/job/%s/%s/consoleText" % (URL, job, build))
        if not resp.ok:
            return []
        lines = resp.text.split("\n")
        return lines

    first = True
    url = "%s/job/%s/%s/api/json" % (URL, job, build)
    cp = 0
    while 1:
        resp = requests.get(url)
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
        cons = console()
        if len(cons) > cp:
            print "\n".join(cons[cp:]),
            cp = len(cons)
        time.sleep(2)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        pass
