#!/usr/bin/env python

"""
RedirectIO.py
Modified from:
stackoverflow.com/questions/6796492/python-temporarily-redirect-stdout-stderr
"""

__date__       = "20130101"
__author__     = "jlettvin"
__maintainer__ = "jlettvin"
__email__      = "jlettvin@gmail.com"
__copyright__  = "Copyright(c) 2013 Jonathan D. Lettvin, All Rights Reserved"
__license__    = "GPLv3"
__status__     = "Production"
__version__    = "0.0.1"

"""
RedirectIO.py
RedirectIO.py implements a method for redirecting output.
Copyright(c) 2013 Jonathan D. Lettvin, All Rights Reserved"

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
import sys

class RedirectStdStreams(object):
    def __init__(self, stdout=None, stderr=None):
        self._stdout = stdout or sys.stdout
        self._stderr = stderr or sys.stderr

    def __enter__(self):
        self.old_stdout, self.old_stderr = sys.stdout, sys.stderr
        self.old_stdout.flush(); self.old_stderr.flush()
        sys.stdout, sys.stderr = self._stdout, self._stderr

    def __exit__(self, exc_type, exc_value, traceback):
        self._stdout.flush(); self._stderr.flush()
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr

if __name__ == '__main__':

    devnull = open(os.devnull, 'w')
    print('Fubar')

    with RedirectStdStreams(stdout=devnull, stderr=devnull):
        print("You'll never see me")

    print("I'm back!")
