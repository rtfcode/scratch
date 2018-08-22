#!/usr/bin/python

from blockext import *
import subprocess
import os

class SSay:

    def say(self, statement, voice):
        if voice == '':
            voice = "Alex"
        os.system("say -v " + voice + " " + statement)


descriptor = Descriptor(
    name = "Scratch Say",
    port = 5000,
    blocks = [
        Block('say', 'command', 'say %s with voice %m.voices', defaults=["hello", "Alex"]),
    ],
    menus = dict(
        voices = subprocess.check_output('say -v ? | grep en_ | cut -d" " -f1', shell=True).split()
    ),
)

extension = Extension(SSay, descriptor)

if __name__ == '__main__':
    extension.run_forever(debug=True)


