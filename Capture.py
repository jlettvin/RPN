#!/usr/bin/env python

"""
Capture.py
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
Capture.py
Implements a screen capture standalone AND service class.
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

import wx, numpy, scipy, pyopencl

from optparse import OptionParser

class Capture(object): #CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC

    def __init__(self, size, **kw): #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        self.kw             = kw
        self.rect           = wx.RectPS((0,0), size)
        self.DC             = {}
        self.BMP            = {}
        self.DC[ 'source']  = wx.ScreenDC()
        self.XY             = self.DC[ 'source'].Size

    def pre(self, client, **kw): #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        size                = kw['size']
        self.X, self.Y      = self.XY
        self.hXY            = [self.X/2, self.Y/2]
        self.BMP['source']  = wx.EmptyBitmap(*self.XY)
        self.BMP['window']  = self.BMP['source'].GetSubBitmap(self.rect)
        self.limit          = [(0, b-a) for a,b in zip(size, self.XY)]
        self.DC[ 'memory']  = wx.MemoryDC(self.BMP['source'])
        self.DC[ 'memory'].Blit(0, 0, self.X, self.Y, self.DC['source'], 0, 0)
        self.DC[ 'memory'].SelectObject(wx.NullBitmap) # instant response
        self.DC[ 'target']  = wx.AutoBufferedPaintDC(client)

    def get(self, ur, XY): #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        return self.BMP['source'].GetSubBitmap(wx.RectPS(ur,XY))

    def put(self, processed): #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        self.DC['target'].DrawBitmap(processed, 0, 0)

class Panel(wx.Panel): #CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC

    def __init__(self, parent, size, process, dt, **kw): #~~
        super(Panel, self).__init__(parent, -1)
        self.kw             = kw
        self.frame          = parent
        self.capture        = Capture(size, **kw)
        self.mXY            = (0,0)
        self.size           = size
        self.process        = process
        self.dt             = dt
        self.ready          = kw.get('ready', False)
        self.savename = {
                'D':'Diffract',
                'H':'Human',
                'O':'Other',
                'R':'Refract',
                }

        self.timer          = wx.Timer(self)
        self.SetSize(size)
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        events = {wx.EVT_PAINT   : self.on_paint,
                  wx.EVT_TIMER   : self.on_timer,
                  wx.EVT_KEY_DOWN: self.on_key  }
        for key, val in events.iteritems(): self.Bind(key, val)
        self.SetFocus()
        self.timer.Start(self.dt)
        self.update()
        self.savers = (
                "abcdefghijklmnopqrstuvwxyz" +
                "ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    def update(self): #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        self.Refresh()
        self.Update()
        wx.CallLater(self.dt, self.update)

    def position(self): #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        # Request a larger size capture area if convolving.
        dx, dy        = self.process(None)
        sx, sy        = self.size
        (X, Y)        = self.capture.limit
        x, y          = [a-b for a,b in zip(self.mXY,[a/2 for a in self.size])]
        self.frame.SetTitle('(%d,%d)' % (self.mXY))

        if self.ready:
            self.oversize = (sx+2*dx, sy+2*dy)
            return (min(max(x,X[0]+dx),X[1]-dx), min(max(y,Y[0]+dy),Y[1]-dy))
        else:
            self.oversize = (sx, sy)
            return (min(max(x, X[0]), X[1]), min(max(y, Y[0]), Y[1]))

    def on_paint(self, event): #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        self.kw['size'] = self.size
        self.capture.pre(self, **self.kw)
        position        =  self.position()
        self.captured   = (self.capture.get(position, self.oversize))
        self.processed  =  self.process(self.captured)
        if self.processed: self.capture.put(self.processed)

    def on_timer(self, event): #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        self.mXY            = tuple(wx.GetMousePosition())

    def on_key(self, event): #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        key                 = event.GetKeyCode()
        if   key      == wx.WXK_ESCAPE: self.frame.Close(True)
        elif chr(key) in self.savers  : self.save(chr(key))
        else: print 'unknown key', key

    def save(self, key): #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
        basename = self.kw.get('rpn', 'unknown')
        srcname = 'img/%s.%s.src.png' % (basename, key)
        tgtname = 'img/%s.%s.tgt.png' % (basename, key)
        print 'Saving as', srcname, tgtname
        self.captured .ConvertToImage().SaveFile(srcname, wx.BITMAP_TYPE_PNG)
        self.processed.ConvertToImage().SaveFile(tgtname, wx.BITMAP_TYPE_PNG)

class Frame(wx.Frame): #CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC

    def __init__(self, size, transform, dt, **kw):
        self.kw = kw
        style = wx.DEFAULT_FRAME_STYLE & ~wx.RESIZE_BORDER & ~wx.MAXIMIZE_BOX
        super(Frame, self).__init__(None, -1, 'Screen Viewer', style=style)
        panel = Panel(self, size, transform, dt, **kw)
        self.Fit()
        #print '\t\tFrame', self.kw

#CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
class Main(object):

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def reverseRB(self, source, **kw):
        if source == None:
            return (2,2)
        sw, sx, sy  = ssize = source.shape
        tx, ty      = tsize = self.size
        tshape      = (3, tx, ty)
        dx, dy      = sx - tx, sy - ty
        left, right = dx/2, dx - dx/2
        up, down    = dy/2, dy - dy/2
        R, G, B     = source
        #print '\t\t', left, right, up, down, source.shape, tshape

        target          = scipy.zeros(tshape, 'float32')

        if right != 0 and down != 0:
            target[0,:,:]   = B[left:-right, up:-down]
            target[1,:,:]   = G[left:-right, up:-down]
            target[2,:,:]   = R[left:-right, up:-down]
        else:
            target[0,:,:]   = B
            target[1,:,:]   = G
            target[2,:,:]   = R
        return target

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, *args, **kw):
        self.args       = args
        self.kw         = kw
        self.size       = kw.get('size'     , (201,201))
        self.dt         = kw.get('dt'       ,        10)
        self.coefficient= 1.0 / 255.0
        self.ctx        = pyopencl.create_some_context()
        self.queue      = pyopencl.CommandQueue(self.ctx)
        self.gpu        = {}
        self.loadGPUcode('noop')
        self.dtype      = scipy.float32
        self.gpgpu      = kw.get('gpgpu', False)
        self.oshape     = None
        self.mf         = pyopencl.mem_flags
        self.srcFlags   = self.mf. READ_ONLY|self.mf.COPY_HOST_PTR
        self.tgtFlags   = self.mf.WRITE_ONLY

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __call__(self, **kw):
        self.fun        = kw.get('fun'      ,      self.reverseRB )
        app             = wx.PySimpleApp()
        self.frame      = Frame(self.size, self.process, self.dt, **kw)
        self.frame.Center()
        self.frame.Show()
        app.MainLoop()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def loadGPUcode(self, filename):
        with open(filename+'.cl', 'r') as source:
            code = "".join(source.readlines())
            self.gpu[filename] = pyopencl.Program(self.ctx, code).build()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def jit(self, sarray):
        # Starting setup for gpgpu
        self.a          = sarray
        self.a_src      = pyopencl.Buffer(self.ctx, self.srcFlags, hostbuf=self.a)
        if not self.oshape or self.shape != self.oshape:
            self.oshape = self.shape
            self.b      = scipy.zeros(self.shape, type(sarray))
            self.b_src  = pyopencl.Buffer(self.ctx, self.srcFlags, hostbuf=self.b)
            self.b_tgt  = pyopencl.Buffer(self.ctx, self.tgtFlags, self.b.nbytes)
        # Finished setup for gpgpu

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def withGPU(self, sarray):
        self.jit(sarray)
        # Starting exec for gpgpu
        self.gpu['noop'].code(self.queue, self.a.shape, None, self.a_src, self.b_tgt)
        tarray          = numpy.empty_like(self.a)
        pyopencl.enqueue_read_buffer(self.queue, self.b_tgt, tarray).wait()
        # tarray now contains the result
        # Finished exec for gpgpu
        return tarray

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def withCPU(self, sarray):
        tarray      = scipy.array(self.fun(sarray, **self.kw), self.dtype)
        #if tarray == None:
            #self.frame.Close(True)
            #return pwh, None
        #print 'CPU:', type(sarray), type(tarray), type(sarray[0,0,0]), type(tarray[0,0,0])
        return tarray

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # This is the core function that calls the RPN client.
    def process(self, sbmp):
        """Core function"""
        if sbmp == None:
            # Oversize required
            return self.size
        # reverse height and width under advice
        (ws, hs, ps)    = shape = (sbmp.GetHeight(), sbmp.GetWidth(), 3)
        simg            = wx.ImageFromBitmap(sbmp)

        sarray          = scipy.array(scipy.fromstring(simg.GetData(), 'uint8'), self.dtype) / 255.0
        sarray          = scipy.rollaxis(scipy.reshape(sarray, shape), 2)
        self.shape      = sarray.shape

        tarray          = (self.withGPU if self.gpgpu else self.withCPU)(sarray)
        mm              = (sarray.min(), sarray.max(), tarray.min(), tarray.max())
        #print '\t', sarray.shape, tarray.shape,
        print type(sarray[0,0,0]), type(tarray[0,0,0]), mm

        tarray          = numpy.nan_to_num(tarray)
        tarray         /= max(tarray.max(), self.coefficient)
        tarray          = scipy.array((tarray * 255.0).tolist(), 'uint8')

        tarray          = scipy.dstack(tarray)
        timg            = wx.EmptyImage(ws, hs)
        timg              .SetData(tarray.tostring())
        self.tbmp       = timg.ConvertToBitmap()
        return self.tbmp

if __name__ == '__main__': #MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM

    parser = OptionParser()
    parser.add_option(
            '-e', '--ready', action="store_true", default=False, help="ready")
    parser.add_option(
            '-g', '--gpgpu', action="store_true", default=False, help="use gpgpu")
    parser.add_option(
            '-v', '--verbose', action="store_true", default=False, help="test")
    (opts, args) = parser.parse_args()
    kw = vars(opts)

    main = Main(**kw)
    main(**kw)
