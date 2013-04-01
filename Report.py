#!/usr/bin/env python

"""
Report.py adds relevant logging for 
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
Report.py
Report.py generates HTML reports based on a simple markup language.
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

import os, sys

sys.path.append('..')

from Logger import Logger
from Tag import *

render = rules['render']

class Report(Logger):
    def __init__(self, markup):
        prefix = {'.': 'passed', '?': 'warning', '!': 'error', '^': 'header'}
        with TABLE():
            for line in markup:
                with TR():
                    for cell in [chunk.strip() for chunk in line.split('|')]:
                        style = 'info'
                        if cell[0] in prefix.keys():
                            style = prefix[cell[0]]
                            cell = cell[1:]
                        attributes = {'value': cell}
                        attributes.update(render['cell.%s' % (style)])
                        TD('close', **attributes)
    @property
    def final(self):
        return TAG.final()

if __name__ == "__main__":
    ##########################################################################
    # TEST RESOURCES

    # Methods for coloring output text.
    g_ = Color(foreground='green', background='black', render='bright')
    rw = Color(foreground='red'  , background='white', render='bright')

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def whoami(level):
        """Introspect the name of the calling function."""
        return inspect.stack()[level][3]

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def showDiff(actual, expect):
        "Display colored text for two buffers with diff style markers."
        # Prefer to put actual before expect since actual will be shown in red.
        if actual != expect:
            print>>sys.stderr, '<'*79
            print>>sys.stderr, rw(actual)
            print>>sys.stderr, '='*79
            print>>sys.stderr, g_(expect)
            print>>sys.stderr, '>'*79

    """
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def assertPass():
        testname = whoami(2)
        print g_('[PASS]'), testname

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def assertFail():
        testname = whoami(2)
        print rw('[FAIL]'), testname
    """

    # assert methods for use by test methods.
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def assertPassFail(actual, expect, **kw):
        level    = kw.get('level', 1)
        check    = kw.get('check', True)
        force    = kw.get('force', False)
        testname = whoami(level+1)
        passfail = ((actual == expect) == check)
        print (g_('[PASS]') if passfail else rw('[FAIL]')), testname
        #if not passfail or force: showDiff(actual, expect)
        showDiff(actual, expect)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def assertEqual(actual, expect, **kw):
        kw2 = kw.copy()
        kw2['level']=2
        assertPassFail(actual, expect, **kw2)

    """
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def assertNotEqual(actual, expect, **kw):
        kw2 = kw.copy()
        kw2['level']=2
        kw2['check']=False
        assertPassFail(actual, expect, **kw2)
    """

    #TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
    def test_simple():
        expect = """\
<table>
  <tr>
    <td bgcolor="white" align="center" value="a" fontattribute="normal" width="500" href="" fontcolor="black"/>
    <td bgcolor="white" align="center" value="b" fontattribute="normal" width="500" href="" fontcolor="black"/>
    <td bgcolor="white" align="center" value="c" fontattribute="normal" width="500" href="" fontcolor="black"/>
  </tr>
  <tr>
    <td bgcolor="green" align="center" value="d" fontattribute="bold" width="500" href="" fontcolor="black"/>
    <td bgcolor="yellow" align="center" value="e" fontattribute="bold" width="500" href="" fontcolor="brown"/>
    <td bgcolor="black" align="center" value="f" fontattribute="bold" width="500" href="" fontcolor="red"/>
  </tr>
  <tr>
    <td bgcolor="white" align="center" value="g" fontattribute="normal" width="500" href="" fontcolor="black"/>
    <td bgcolor="white" align="center" value="h" fontattribute="normal" width="500" href="" fontcolor="black"/>
    <td bgcolor="white" align="center" value="i" fontattribute="normal" width="500" href="" fontcolor="black"/>
  </tr>
</table>
"""
        assertEqual(Report(['a|b|c', '.d|?e|!f', 'g|h|i']).final, expect)

    #TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
    def test_constructed():
        expect = """\
<table>
  <tr>
    <td bgcolor="white" align="center" value="x" fontattribute="bold" width="500" href="" fontcolor="black"/>
    <td bgcolor="white" align="center" value="y" fontattribute="bold" width="500" href="" fontcolor="black"/>
    <td bgcolor="white" align="center" value="z" fontattribute="bold" width="500" href="" fontcolor="black"/>
  </tr>
  <tr>
    <td bgcolor="white" align="center" value="a" fontattribute="normal" width="500" href="" fontcolor="black"/>
    <td bgcolor="white" align="center" value="b" fontattribute="normal" width="500" href="" fontcolor="black"/>
    <td bgcolor="white" align="center" value="c" fontattribute="normal" width="500" href="" fontcolor="black"/>
  </tr>
  <tr>
    <td bgcolor="green" align="center" value="d" fontattribute="bold" width="500" href="" fontcolor="black"/>
    <td bgcolor="yellow" align="center" value="e" fontattribute="bold" width="500" href="" fontcolor="brown"/>
    <td bgcolor="black" align="center" value="f" fontattribute="bold" width="500" href="" fontcolor="red"/>
  </tr>
  <tr>
    <td bgcolor="white" align="center" value="g" fontattribute="normal" width="500" href="" fontcolor="black"/>
    <td bgcolor="white" align="center" value="h" fontattribute="normal" width="500" href="" fontcolor="black"/>
    <td bgcolor="white" align="center" value="i" fontattribute="normal" width="500" href="" fontcolor="black"/>
  </tr>
</table>
"""
        xyz_str = x, y, z = ['x', 'y', 'z']
        abc_str = a, b, c = ['a', 'b', 'c']
        def_str = d, e, f = ['d', 'e', 'f']
        ghi_str = g, h, i = ['g', 'h', 'i']
        passed, warn, error, header = ['.', '?', '!', '^']

        square = [
                string.join([header+x, header+y, header+z], '|'),
                string.join(abc_str, '|'),
                string.join([passed+d, warn+e, error+f], '|'),
                string.join(ghi_str, '|'),]
        assertEqual(Report(square).final, expect)

    def test_100_percent():
        two = ['a', 'b']
        with open(os.devnull, 'w') as devnull:
            with RedirectStdStreams(stdout=devnull, stderr=devnull):
                showDiff(two[0], two[1])

    test_simple()
    test_constructed()
    test_100_percent()
