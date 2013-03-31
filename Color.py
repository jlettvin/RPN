#!/usr/bin/env python

"""
Color.py implements color management for stdout.
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
Color.py
Implements a colorizer for an HTML generated table.
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

import os, sys, binascii

class Color(object):
    render = {'reset'    : 0, 'bright': 1, 'faint': 2, 'italic'  : 3,
              'underline': 4, 'slow'  : 5, 'rapid': 6, 'negative': 7}
    fg = {'black': 30, 'red'    : 31, 'green': 32, 'yellow': 33,
          'blue' : 34, 'magenta': 35, 'cyan' : 36, 'white' : 37}
    bg = {'black': 40, 'red'    : 41, 'green': 42, 'yellow': 43,
          'blue' : 44, 'magenta': 45, 'cyan' : 46, 'white' : 47}

    def filldict(d):
        n = d.copy()
        for key, val in d.iteritems():
            n[key] = val
            n[key[0].upper()+key[1:]] = val
            n[key.upper()] = val
            if key == 'black': continue
            n[key[0]] = val
            n[key[0].upper()] = val
        n['0'] = d['black']
        d = n

    filldict(fg)
    filldict(bg)

    def __init__(self, **kw):
        fg = kw.get('foreground', None)
        bg = kw.get('background', None)
        rd = kw.get('render', 'reset')
        if not fg: fg = kw.get('fg', None)
        if not bg: bg = kw.get('bg', None)
        rd = Color.render[rd]
        self.color = '\x1b[0m'
        if fg in Color.fg.keys() and bg in Color.bg.keys():
            self.color = '\x1b['+str(rd)+';'+str(Color.fg[fg])+';'+str(Color.bg[bg])+'m'
    def __call__(self, msg):
        return self.color+msg+'\x1b[0m'

if __name__ == "__main__":
    print 'normal'
    gr = Color(foreground='green',background='red')
    yb = Color(foreground='yellow',background='blue',render='underline')
    fb = Color(fg='foo', bg='bar')
    print gr('hello gr')
    print yb('hello yb')
    print fb('hello fb')
    print 'normal'

