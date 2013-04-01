#!/usr/bin/env python

"""
Logger.py implements a uniform logging mechanism for all tests.
It outputs logging information to both stdout and to log/Logger.{timestamp}.log
py.test discards stdout, but the logfile remains after a run.

When logging is desirable, either instance or derive from a Logger object.
See test_Logger.py for an example of how this is done.
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
Logger.py
Logger.py implements a uniform logging mechanism for all tests.
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

import os, sys, logging, inspect, string, time, exceptions

sys.path.append('..')

#from Common.Config import Config
import Color

class Logger(object):

    t0 = time.time()
    configured = False
    scriptname, basename = None, None
    logger = logging.getLogger(sys.argv[0])
    logname, level = None, 0
    #xmltab, xmlname, xmlstream = 0, None, None
    now = time.gmtime()
    timestamp = str(now.tm_year)
    # CAUTION: This formatter must not change if test_Logger.py is to succeed.
    # In other words, if you change this format, change test_Logger.py.
    # This takes a bit of labor and meticulous testing to get right.
    formatter = logging.Formatter(
             '%(asctime)s %(name)24s %(levelname)8s %(message)s')
    timestamp += string.join([".%02d" % (piece) for piece in (
        now.tm_mon, now.tm_mday, now.tm_hour, now.tm_min, now.tm_sec)
        ], '')
    levels = {
             '0': logging.DEBUG,
             '1': logging.INFO,
             '2': logging.WARNING,
             '3': logging.ERROR,
             '4': logging.CRITICAL,
             }

    color = {
            'debug' : Color.Color(
                foreground='blue' , background='white'),
            'info' : Color.Color(
                foreground='black' , background='white'),
            'warning' : Color.Color(
                foreground='yellow' , background='black', render='bright'),
            'error' : Color.Color(
                foreground='red' , background='black', render='bright'),
            'critical': Color.Color(
                foreground='magenta', background='black', render='bright'),
            }

    def __del__(self):
        #if Logger.xmlstream:
            #Logger.xmlstream.close()
            #Logger.xmlstream = None
        pass

    def configure(self, **kw):
        assert not Logger.configured

        if not Logger.logname: Logger.logname = kw.get('logfile', None)
        Logger.level = Logger.levels[kw.get('level', '0')]

        if not Logger.logname:
            Logger.scriptname = sys.argv[0]
            Logger.basename = os.path.basename(Logger.scriptname)
            Logger.logname = "log/%s.%s.log" % (Logger.basename, Logger.timestamp)
            #Logger.xmlname = "xml/%s.%s.xml" % (Logger.basename, Logger.timestamp)
            try:
                os.mkdir("log")
            except exceptions.OSError as e:
                pass
            #try:
                #os.mkdir("xml")
                #Logger.xmlstream = open(Logger.xmlname, "w")
                #print "Opened", Logger.xmlname
                #pass
            #except exceptions.OSError as e:
                #pass

        # Note: output is sent to both stdout and to a file named by filename.
        # This file will always appear in a directory named log just beneath
        # the directory in which the py.test or scrip using this module is executed.
        handlers = (logging.StreamHandler(sys.stdout), logging.FileHandler(Logger.logname))
        Logger.logger.setLevel(Logger.level)

        for handler in handlers:
            handler.setLevel(Logger.level)
            handler.setFormatter(Logger.formatter)
            Logger.logger.addHandler(handler)
        Logger.configured = True

    def required(self):
        if not Logger.configured:
            self.configure()

    def filename(self):
        return Logger.logname

    def whoami(self, level=1):
        self.debug(inspect.stack()[level][3])

    def _whoami(self):
        """
_whoami gathers information from a variety of places
to establish the name of the calling function
the name of its module, and the line number of the call,
and the elapsed time since the last _whoami.
"""
        frame_records = inspect.stack()[2]
        module_name = inspect.getmodulename(frame_records[1])
        method_name = frame_records[3]
        frame,fname,lnum,fun,lines,ind = inspect.getouterframes(
                inspect.currentframe())[2]
        t1 = time.time()
        dt = t1 - Logger.t0
        Logger.t0 = t1

        # CAUTION: This format must not change if test_Logger.py is to succeed.
        # In other words, if you change this format, change test_Logger.py.
        # This takes a bit of labor and meticulous testing to get right.
        seconds = {'inDay': 3600.0*24.0, 'inHour': 3600.0, 'inMinute': 60.0}

        D = int(dt / seconds['inDay'])
        dt -= float(D * seconds['inDay'])

        H = int(dt / seconds['inHour'])
        dt -= float(H * seconds['inHour'])

        M = int(dt / seconds['inMinute'])
        dt -= float(M * seconds['inMinute'])

        S = dt

        duration = "%d:%02d:%02d:%06.3f" % (D,H,M,S)

        module_method = '%s [%s.%s:%d]' % (
                duration, module_name, method_name, lnum)
        return '%-42s ' % (module_method)

    def xml(self, msg):
        # TODO XML output unimplemented
        tag = inspect.stack()[1][3]
        #print>>Logger.xmlstream, '<%s "%s"/>' % (tag, msg)

    def debug( self, msg, *args, **kw):
        self.required()
        color = Logger.color['debug']
        self.xml(msg)
        Logger.logger.debug( color(self._whoami()+msg), *args, **kw)
    def info( self, msg, *args, **kw):
        self.required()
        color = Logger.color['info']
        self.xml(msg)
        Logger.logger.info( color(self._whoami()+msg), *args, **kw)
    def warning( self, msg, *args, **kw):
        self.required()
        color = Logger.color['warning']
        self.xml(msg)
        Logger.logger.warning( color(self._whoami()+msg), *args, **kw)
    def error( self, msg, *args, **kw):
        self.required()
        color = Logger.color['error']
        self.xml(msg)
        Logger.logger.error( color(self._whoami()+msg), *args, **kw)
    def critical( self, msg, *args, **kw):
        self.required()
        color = Logger.color['critical']
        self.xml(msg)
        Logger.logger.critical( color(self._whoami()+msg), *args, **kw)
    def log( self, lvl, msg, *args, **kw):
        self.required()
        self.xml(msg)
        Logger.logger.log( lvl, self._whoami()+msg, *args, **kw)
    def setLevel( self, lvl):
        self.required()
        Logger.logger.setLevel(lvl)

if __name__ == "__main__":
    logger = Logger()
    logger.debug( 'debug' )
    logger.info( 'info' )
    logger.warning( 'warning' )
    logger.error( 'error' )
    logger.critical( 'critical')
    logger.setLevel(logging.DEBUG)
    logger.info(logger.filename())
    logger.log(logging.INFO,"log")
    logger.whoami()
