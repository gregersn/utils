#!/usr/bin/env python3

import io
import os
import sys
import sane
from sane import _sane
import time
import datetime
from subprocess import Popen, PIPE

from settings import SETTINGS


def trim(data: io.BytesIO, filename: str):
    command = [
        '/usr/bin/env',
        'convert',
        '-',
        '-fuzz',
        '2%',
        '-trim',
        '+repage',
        filename
    ]

    proc = Popen(command, stdin=PIPE)
    proc.communicate(data.read())


def do_scan(scanner):
    try:
        scanner.start()
    except _sane.error as e:
        print("Sleeping while waiting for input")
        time.sleep(5)
        return

    # print(scanner.get_options())
    # print(scanner.get_parameters())

    print("Getting scanner snap")
    snap = scanner.snap()

    print("Saving to buffer")
    imgbytes = io.BytesIO()
    snap.save(imgbytes, format='PNG')

    imgbytes.seek(0)

    now = datetime.datetime.now()
    outfile = f'{now.strftime("%Y-%m-%d %H%M%S")}.png'

    if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
        outfile = os.path.join(sys.argv[1], outfile)

    print("Sending to IM for trim")
    trim(imgbytes, outfile)
    print("done")
    time.sleep(5)


def main():
    scanner_name = SETTINGS.get('scanner', 'dsseries:usb:0x04F9:0x60E0')

    print("Sane init")
    sane.init()

    """
    print("Getting devices")
    devices = sane.get_devices(localOnly=True)

    print("Found devices")
    for device in devices:
        print(device)
        print(dir(device))
    """
    print("Opening scanner")
    scanner = sane.open(scanner_name)

    scanner.mode = 'Color'

    """
    print("Scanner options")
    print(scanner.opt)
    print("")
    """
    """
    Options

    - mode
      index: 2
      'LineArt', 'Gray', 'Color'
    
    - resolution
      index: 3
      75 - 600
    
    - preview
      index: 4
      0, 1 (bool)
    
    - brightness
      cur: 0.0
      index: 14
      -100.0, 100.0
    
    - contrast
      index: 15
      cur: 0.0
      -100.0, 100.0
    
    """
    """
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
            do_scan(scanner)
        except KeyboardInterrupt:
            print("Exiting scanner script")
            break

    scanner.close()


if __name__ == '__main__':
    main()
