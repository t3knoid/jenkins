#
# tailDownstreamjob.py
#
# Displays the console output of a downstream job. This script uses the urllib2 library to read
# the progressive text output URL. The code works by looping and waiting if there is more data
# by checking the content of the X-More-Data response header field.
# 

import urllib
import urllib2
import time
import sys
import os

time.sleep(10) # Ten second delay to wait for downstream job to start
JENKINS_BASE = "http://jenkins/job" # Jenkins base URL
JENKINS_JOB = "" # Job Name
job_number='lastBuild' # Job number

start = 0
cont = True
while cont:
    response = urllib2.urlopen(
        '{base}/{job}/{job_number}'
        '/logText/progressiveText?start={start}'.format(
            base=JENKINS_BASE, job=JENKINS_JOB,
            job_number=job_number, start=start
        )
    )

    if response.getcode() != 200:
        print('Job complete or not found')
        sys.exit(1)

    if start != response.info().get('X-Text-Size'):
        for line in response:
           print line.rstrip()
    start = response.info().get('X-Text-Size')
    cont = response.info().get('X-More-Data')
    time.sleep(2)
