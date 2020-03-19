#!/usr/bin/env python3

import io
import os
import sys
import sane
from sane import _sane
import time
import datetime
from subprocess import Popen, PIPE

scanner_name = 'dsseries:usb:0x04F9:0x60E0'

print("Sane init")
sane.init()

# print("Getting devices")
# devices = sane.get_devices(localOnly=True)
"""
print("Found devices")
for device in devices:
    print(dir(device))
"""
print("Opening scanner")
scanner = sane.open(scanner_name)

"""
print("Scanner options")
print(scanner.opt)
print("")

print("Scanner optlist")
print(scanner.optlist)
print("")

print("Scanner area")
print(scanner.area)


print(scanner.get_options())
print(scanner.get_parameters())
"""

while True:
    try:
        scanner.start()
    except _sane.error as e:
        print("Sleeping while waiting for input")
        time.sleep(5)
        continue
    # print(scanner.get_options())
    # print(scanner.get_parameters())

    print("Getting scanner snap")
    snap = scanner.snap()
    print("Saving to buffer")
    imgbytes = io.BytesIO()
    snap.save(imgbytes, format='PNG')
    imgbytes.seek(0)

    now = datetime.datetime.now()
    outfile = '{}.png'.format(now.strftime("%Y-%m-%d %H%M%S"))

    if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
        outfile = os.path.join(sys.argv[1], outfile)

    command = [
        '/usr/bin/env',
        'convert',
        '-',
        '-fuzz',
        '1%',
        '-trim',
        '+repage',
        outfile
    ]
    print("Sending to IM for trim")
    proc = Popen(command, stdin=PIPE)
    proc.communicate(imgbytes.read())
    print("done")
    time.sleep(5)
