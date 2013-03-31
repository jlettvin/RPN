#!/usr/bin/env python

"""
Pickets.py
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
Pickets.py
Pickets.py implements a method for evenly spacing.
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

import sys, scipy, itertools

scipy.set_printoptions(precision=3, suppress=True, linewidth=100)

class Pickets(object):

    def __init__(self, radial=1):
        self.radial = radial
        div1 = 1 + 2 * radial
        div2 = 1 if radial < 1 else 2 + 1.0 / radial
        seq = [0,] if radial == 0 else scipy.linspace(-1.0, 1.0, div1) / div2
        if len(seq) > 1:
            """Assert that the pickets are evenly spaced."""
            one = 2*seq[-1] + seq[1 + len(seq) / 2]
            epsilon = scipy.fabs(1.0 - one)
            assert epsilon < 1e-10
        self.pickets = list(itertools.product(seq, repeat=2))

    def __str__(self):
        return str(list(self.pickets))

    @property
    def data(self):
        return self.pickets

    @property
    def interval(self):
        return self.radial

if __name__ == "__main__":
    args = sys.argv
    radial = 0 if len(args) < 2 or not args[1].isdigit() else int(args[1])
    pickets = Pickets(radial)
    print pickets
