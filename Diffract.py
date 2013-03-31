#!/usr/bin/env python

"""
Diffract.py
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
Diffract.py
Implements an Airy function generator/convolver.
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

###############################################################################
import sys, itertools, scipy

from scipy                       import array, arange, ones, zeros
from scipy                       import exp, sqrt, pi, fabs, ceil
from scipy                       import set_printoptions
from scipy.special               import j1
from scipy.misc                  import imresize
from scipy.ndimage.interpolation import affine_transform
from Image                       import fromarray

from Pickets                     import Pickets
from Report                      import Report
###############################################################################
set_printoptions(precision=2, suppress=True, linewidth=150)

###############################################################################
class Human(Report):

    aawf = {'radius'    : 0e+0,
            'amplitude' : 1e+0,
            'aperture'  : 1e-3,
            'wavelength': 4e-7,
            'focal'     :17e-3}
    zeroPoints = [ # u values where Airy goes to zero, discovered by hand.
            3.83170611001,
            7.01558711101,
            10.1734711001,                  # Maximum kernel radius parameter.
            # u = (pi*r*a) / (w*f) where:
            # r     radius      kernel max
            # a     aperture    diameter    (fixed for a given iteration)
            # w     wavelength  nanometers  (fixed for a color plane)
            # f     focal length            (fixed for a human eye)
            # The radius of a kernel is determined by setting all other values.
            13.3236911001,
            16.4706211111,
            19.6158611111]
    maxima = [
            {'u': 0.0          , 'a': 1.0              },   #  1/1
            {'u': 5.13562311005, 'a': 0.0174978627858  },   # ~1/57
            {'u': 8.41724511071, 'a': 0.00415799638453 },   # ~1/240
            # This is proof that only three maxima and three zeros are needed
            # for 32 bit color (8bit Red, Green, and Blue).
            {'u': 11.6198420998, 'a': 0.00160063766822 },   # ~1/624
            {'u': 14.7959530997, 'a': 0.000779445355471},   # ~1/1284
            {'u': 17.9598201116, 'a': 0.000437025551621},   # ~1/2288
            {'u': 21.1169981116, 'a': 0.000269287409511},]  # ~1/3717

    @property
    def parameters(self):
        return Human.aawf

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, **kw):
        """
        __init__ generates triangular kernel wedges
        then distributes the wedge over eight-fold symmetry
        to fill an entire square of odd length edge.
        """
        self.kw         = kw
        self.verbose    = self.kw.get('verbose', False)
        self.ignore     = self.kw.get('ignore', 1.0/255.0)

        self.coeff      = 2e-1
        self.radius     = self.kernelRadius(**kw)
        self.edge       = 1 + 2 * self.radius
        self.shape      = (self.edge, self.edge)
        self.original   = zeros(self.shape, float)

        self.offset     = Pickets(4)
        self.pickets    = Pickets(1)

        kw['radius']    = 0.0
        test = self.wave()
        if self.verbose:
            self.info('generating kernels for %d radial intervals' %
                    (self.offset.interval))
        if self.kw.get('generate', False):
            w, a = 534e-9, 7e-3
            # Generate kernels for sub-pixel offsets.
            for dx, dy in self.offset.data:
                kernel = self.genAiry(dx, dy, w, a)
        else:
            pass

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def wave(self, **kw):
        amplitude, r, a, w, f = (
                kw.get(key, Human.aawf[key]) for key in (
                    'amplitude', 'radius', 'aperture', 'wavelength', 'focal'))
        u = (pi*r*a)/(w*f)
        if isinstance(r,float):
            return amplitude*(1.0 if u == 0.0 else 2.0*j1(u)/u)
        else:
            u[u==0.0] = 1e-32
            return amplitude*2.0*j1(u)/u

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def kernelRadius(self, **kw):
        """
        For r in millimeters:
        u = (pi*r*a) / (w*f)    # Standard calculation for wave equation
        r = (u*w*f) / (pi*a)    # Algebraic method for determining radius
        wiggle                  # Leaves room for picket wiggle
        """
        a, w, f = (float(kw.get(key, Human.aawf[key]))
                for key in ('aperture', 'wavelength', 'focal'))
        mm_per_meter, h = Human.zeroPoints[2], 1e6
        return int(ceil((mm_per_meter * h * w * f) / (pi*a)))

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def genRadii(self, R, dxy=(0.0,0.0), exy=(0.0,0.0)):
        edge     = 1.0 + 2.0 * R
        um       = 1e-6
        accum    = zeros((edge, edge), float)
        radii    = zeros((edge, edge), float)
        dx, dy   = dxy
        ex, ey   = exy
        sequence = [(X, Y, um*float(X-R), um*float(Y-R)) for X, Y in
                list(itertools.product(range(int(edge)), repeat=2))]
        for X, Y, x, y in sequence:
            radii[X,Y] = sqrt((x+dx+ex)**2 + (y+dy+dy)**2)
        return accum

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def genAiry(self, dx, dy, w, a, **kw):
        if self.verbose:
            self.info("generating kernel at offset(%1.1f,%1.1f)" % (dx,dy))
        um                 = 1e-6                     # microns     in meters
        kw['aperture'  ]   = a                        # millimeters in meters
        kw['wavelength']   = w                        # nanometers  in meters
        R = self.radius    = self.kernelRadius(**kw)  # max displace from (0,0)
        R1                 = R + 1                    # slop for subpixel offset
        self.edge          = 1 + 2 * R1               # linear size of mask
        radii              = zeros((self.edge, self.edge), float)
        accum              = zeros((self.edge, self.edge), float)
        # Make a list of [X,Y] indices and (x,y) coordinates from (0,0) center.
        sequence           = [(X, Y, um*float(X-R1), um*float(Y-R1)) for X, Y in
                list(itertools.product(range(self.edge), repeat=2))]
        # List of sub-pixel displacements
        pickets1           = [[0.0,0.0],]
        pickets2           = array(self.pickets.data) * um
        # Introduce multiple small offsets to emulate a pixel's
        # physical face size.  This eliminates sampling errors
        # that would artificially amplify exactly centered pixels.
        for ex, ey in pickets2:
            for X, Y, x, y in sequence:
                # Determine optical displacement
                radii[X,Y] = sqrt((x+dx+ex)**2 + (y+dy+dy)**2)
            kw['radius']   = radii
            # Generate wave function
            component      = self.wave(**kw)
            # Eliminate radii outside third zero?
            component[radii > (R*um)] = 0.0
            # Sum (precursor to discrete integration.
            accum         += component
        # Normalize to sqrt of intensity map sum
        accum             /= sqrt((accum ** 2).sum())
        # Keep a copy as a file.
        self.save(accum, R, dx, dy)
        # Return kernel.
        return accum

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def genGauss(self, r=3.0, **kw):
        # 1/255 is interpreted as a threshold value of light detection.
        # Gauss is value = exp(-coeff * r * r)
        # 1/255 = exp(-coeff * r * r)
        # log(1/255) = -coeff * r * r
        # -log(1/(255*r*r)) = coeff

        radii = self.genRadii(r)                    # Make a field of radii
        coeff = - scipy.log(1.0 / (255.0 * r * r))  # Calculate coefficient
        accum = exp(-coeff * radii)**2              # Make a Gaussian field
        accum[radii>r] = 0.0                        # Eliminate outliers
        fudge = 0.95                                # Reduce mask (why?)
        accum *= fudge / accum.sum()                # normalize mask
        return accum

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def save(self, kernel, R, dx=0, dy=0, **kw):
        rescaled = (255.0 * kernel).astype('uint8')
        name = "kernels/Airy/kernel.Airy.R%d.dx%1.2f.dy%1.2f" % (R, dx, dy)
        image = fromarray(rescaled)
        image.save(name+".png")
        scipy.save(name+".npy", kernel)

#MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM
if __name__ == "__main__":
    def test_kernel_radius(human):
        aawf = human.parameters
        radius = human.kernelRadius
        for a in arange(1.0e-3, 9.0e-3, 1.0e-3):
            aawf['aperture'] = a
            print "Aperture %f kernel radius=%6.3f" % (a, radius(**aawf))

    human = Human(verbose=True, generate=True)

    test_kernel_radius(human)
    #human.save()
