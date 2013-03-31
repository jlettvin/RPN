#!/usr/bin/env python

# $Id: RPN.py 0001 2013-01-01 00:00:00Z jlettvin $
# Author: Jonathan D. Lettvin <jlettvin@gmail.com>
# Copyright(c) 2013 Jonathan D. Lettvin, All Rights Reserved

"""
A Reverse Polish Notation engine using scipy for functional image filters.
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

This module defines the following classes:

- `RPN`, Reverse Polish Notation engine

Exception classes: None

Functions:

- `addscipy`
- `scipyFunctions`
- `scipyConstants`
- `unittest`
- `calculator`
- `capture`
- `illegal`

How To Use This Module
======================
(See the individual classes, methods, and attributes for details.)

1. Run it as a standalone aggregate calculator app using RPN.

   a) Display command line options.
      - `./RPN.py --help`

   b) Display runtime help.
      - `./RPN.py   # run calculator mode
      - [1]\ `help` # display help
      - [2]\ `.`    # quit

   c) execute code
      - `./RPN.py   # run calculator mode
      - `[1]\ 4`
      - `[2]\ sqrt`
      - `[3]\ show`
      - `[4]\ [[2,3],[5,7]]`
      - `[5]\ @a`
      - `[6]\ a`
      - `[7]\ e`
      - `[8]\ *`
      - `[9]\ show`
      - `[10]\ (2,square,show)`
      - `[11]\ :sqrtshow|sqrt|show|"a function to square root and show`
      - `[12]\ (4|&sqrtshow)`
      - `[13]\ quit`

   d) execute code
      - `echo "(4,sqrt,show,.)"|./RPN.py   # run calculator mode

2. Run it to test functionality
   a) Run unit tests
      - `./RPN.py --mode=unittest`

3. Run it as a desktop image filter.

   a) Show default window with no filter.
      - `./RPN.py --mode=capture`                 # code file `capture.rpn`

   b) Show default window with human optics filter.
      - `./RPN.py --mode=capture --rpn=human.rpn` # code file `human.rpn`

   c) Change rpn file while filter is running to modify operation.

"""

__docformat__ = 'restructuredtext'

###############################################################################
# RPN.py a reverse polish notation calculator using scipy on aggregates.
# Operates in three modes:
# 1. Calculator mode is default for general calculation use.
# 2. Capture    mode uses Capture.py to filter screen input to output.
# 3. UnitTest   mode exercises almost the entire suite of code.
###############################################################################

# Try the following input where '\ ' is the prompt:

###############################################################################
# IMPORTS
import os, sys, scipy, inspect, traceback, types, scipy.constants

from copy                           import deepcopy, copy
from pprint                         import pprint
from optparse                       import OptionParser
from itertools                      import product
from scipy.signal                   import convolve
from scipy.ndimage.interpolation    import affine_transform

# IMPORTS from this suite
from Diffract                       import Human

###############################################################################
#TODO commented out names require more development.

argc = [
    # http://docs.scipy.org/doc/scipy/reference/constants.html
    'c', 'e', 'pi', 'mu_0', 'epsilon_0', 'h', 'hbar',
    ]
"""NAMES OF PHYSICAL CONSTANTS from scipy.constants"""

argp = [
    'G', 'g', 'R', 'alpha', 'N_A', 'k', 'sigma', 'Wien', 'Rydberg',
    'm_e', 'm_p', 'm_n',
    'yotta', 'zetta', 'exa', 'peta', 'tera', 'giga', 'mega', 'kilo',
    'hecto', 'deka', 'deci', 'centi',
    'milli', 'micro', 'nano', 'pico', 'femto', 'atto', 'zepto',
    'kibi', 'mebi', 'gibi', 'tebi', 'pebi', 'exbi', 'zebi', 'yobi',
    'golden',
    ]
"""NAMES OF PHYSICAL CONSTANTS from scipy.constants.constants"""

arg1 = [
    # http://docs.scipy.org/doc/numpy/reference/routines.math.html
    'nan_to_num', 'sin', 'cos', 'tan', 'arcsin', 'arccos', 'arctan',
    'sinh', 'cosh', 'tanh', 'arcsinh', 'arccosh', # 'arctanh',
    'degrees', 'radians', 'deg2rad', 'rad2deg',
    'around', 'round_', 'rint', 'fix', 'floor', 'ceil', 'trunc',
    'exp', 'expm1', 'exp2', 'log', 'log10', 'log2', 'log1p',
    'i0', 'sinc', 'negative', 'sqrt', 'square', 'absolute', 'fabs', 'sign',
    # http://docs.scipy.org/doc/numpy/reference/routines.statistics.html
    'amin', 'amax', 'nanmax', 'nanmin',
    'average', 'mean', 'median', 'std', 'var',
    ]
"""NAMES OF FUNCTIONS OF 1 PARAMETER from scipy"""

arg2 = [
    # http://docs.scipy.org/doc/numpy/reference/routines.math.html
    'hypot', 'logaddexp', 'logaddexp2', 'copysign',
    'add', 'multiply', 'divide', 'power', 'subtract',
    'true_divide', 'floor_divide', 'fmod', 'mod', 'remainder',
    'maximum', 'minimum',
    #'convolve', 'correlate', 'ldexp',
    ]
"""NAMES OF FUNCTIONS OF 2 PARAMETERS from scipy"""

###############################################################################
# Generate scipy wrapper functions prefixed with 'F_' external.
# Insert them as class functions without the 'F_' prefix.
# Although it is generally considered a bad idea to use eval/exec,
# These interpreter formats enable creation of additional CLASS methods.
# class methods are preferred over instance methods.
fmtf = 'RPN.%s = F_%s'
fmtc = ['def F_%s(self): self.internal_push(scipy.constants.%s)',fmtf]
fmtp = [
    'def F_%s(self): ' +
    'self.internal_push(scipy.constants.constants.%s)',
    fmtf]
fmt1 = [
    'def F_%s(self): self.internal_push(scipy.%s(self.internal_pop()))',
    fmtf]
fmt2 = [
    'def F_%s(self): ' +
    'a=self.internal_pop();' +
    'self.internal_push(scipy.%s(self.internal_pop(),a))',
    fmtf]
"""EVAL FORMATS FOR INSERTING FUNCTIONS AND CONSTANTS from scipy"""

###############################################################################
# SUPPORT for special interpreter symbols

arith= {
    '+':'add',
    '-':'subtract',
    '*':'multiply',
    '/':'divide',
    '^':'power',
    }
"""name conversions between standard arithmetic symbols and scipy names"""

quits= ['quit', 'done', 'exit', 'stop', 'kill', 'die', '.']
"""a set of keywords all of which terminate the interpreter"""

spec = {
    '.stack'  :'pprint(self.stack)',
    '.symbol' :'pprint(self.symbol[-1])',
    '.verbose':'self.verbose=True',
    '.quiet'  :'self.verbose=False',
    '\\'      :'self.show()',
    '?'       :'self.help()',
    }
"""a set of special keywords to enable instrospection"""

#TODO consider making Exception classes such as at the end of statemachine.

#CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
class IdentifyException(Exception):
    def __init__(self, c, r, k, **kw):
        self.value = k if k else False
        if kw.get('verbose', False):
            print "%12s: \'%s\'" % (inspect.stack()[2][3], (c+r))
    def __str__(self):
        return 'Flow control exception'

#CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
class Function(object):

    def __call__(self, c='', r='', k='', **kw):
        if   not c     : raise(IdentifyException(c, r, k))
        elif not c in k: raise(IdentifyException(c, r, 0))
        else           : return (c+r).strip()

#CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
class Number(Function):
    def __call__(self, **kw):
        print '\t\t', kw
        try: l = super(Number, self).__call__(kw['c'], kw['r'], '0123456789')
        except IdentifyException as ie:
            print '\t\t', ie.value
            return ie.value
        kw['rpn'].internal_push(l)
        return True

#CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
class RPN(object):
    """
    A Reverse Polish Notation engine for standalone and integrated use.

    Input is given as one-per-line instructions or
    multiple instructions separated by '|' within parentheses or
    as function definitions with ':' lead character for function name.

    Instructions may be given in several forms:
    as prompted lines in mode=calculator;
    as piped lines in mode=calculator;
    as input lines from a file in mode=capture.
    """

    #TODO here is where to continue developing docstrings
    # Consider imitating method docstrings in statemachine.py

    sequence = [
        # This sets the order of execution
        'interpret_multipart',
        'interpret_comment',
        'interpret_prompt',
        'interpret_number',
        'interpret_symbol',
        'interpret_array',
        'interpret_squote',
        'interpret_print',
        'interpret_define',
        'interpret_load',
        'interpret_pop',
        'interpret_arithmetic',
        'interpret_call',
        'interpret_quit',
        'interpret_special',
        'interpret_function',
        'interpret_dictionary',
        'interpret_rawPython',]

    # Basic resources
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    @property
    def internal_ps1(self):
        """generate and return the prompt from components"""
        return '[%d]%s ' % (self.iteration, self.PS1)

    """
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __getattr__(self, key):
        for i in range(0, len(self.symbol)):
            if key in self.symbol[i].has_key(key):
                return self.symbol[i][key]
        return False

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __setattr__(self, key, value):
        self.symbol[-1][key] = value
    """

    #pppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppp
    def internal_push(self, item):
        """put a value on the stack"""
        self.stack = [item,] + self.stack

    #pppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppp
    def internal_pop(self):
        """recover a value by popping it from the stack"""
        a = self.stack[:1][0]
        self.stack = self.stack[1:]
        return a

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def internal_load(self, filename):
        found = False
        for directory in self.directories:
            try:
                with open(os.path.join(directory, filename)) as codefile:
                    self.code = codefile.readlines()
                found = True
                # execute instructions from codefile
                self.internal_interpret(self.code)
            except:
                pass
            if found:
                break
        if not found:
            print 'Failed to load:', filename
        return found

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def __init__(self, **kw):
        """Initialize RPN instance"""
        self.clear()                        # Prepare for interpreter round.
        self.kw                    = kw     # Keep copy of arg dictionary.
        self.depth                 = 0      # Initialize recursion depth.
        self.PS1                   = '\\'   # Initialize default prompt.
        self.first                 = True
        self.iteration             = 1
        self.aperture              = 0.0
        self.human                 = Human()
        self.extended_input        = ''
        self.kernelX, self.kernelY = (0, 0) # Radius of kernel in X and Y
        self.directories           = ['.', './rpn'] # impodt directories
        self.classNumber           = Number()
        # Prepare to find maximum kernel radius for mask
        self.kradius               = 0
        self.ready                 = kw.get('ready', False)
        #print '\t\tRPN', self.kw

    #()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()()
    def __call__(self, source, **kw):
        """entrypoint for image filtration using Capture.py"""

        if source == None:
            #This is how oversize is returned
            #TODO figure out why the edge reflection still exists.
            return (self.kernelX, self.kernelY)

        # put R=0, G=1, B=2 into symbol table
        for n, letter in enumerate('RGB'): self.symbol[-1][letter] = n
        # put original Capture.py source array as planes into symbol table
        self.symbol[-1]['Rs'], self.symbol[-1]['Gs'], self.symbol[-1]['Bs'] = (
                source)

        # Put dimensions into the symbol table
        self.shape                = (self.W, self.X, self.Y) = source.shape
        self.symbol[-1].update({
            'W':self.W,     # Wavelengths
            'X':self.X,     # Width
            'Y':self.Y,     # Height
            })
        # Put wavelength values into the symbol table
        self.symbol[-1].update({
            'Iw':750e-9,    # Infrared
            'Rw':564e-9,    # Red
            'Gw':534e-9,    # Green
            'Bw':420e-9,    # Blue
            'Uw':390e-5,    # Ultraviolet
            })

        # recover Rt, Gt, Bt target color planes from interpreter
        RGB = [self.symbol[-1].get('%ct' % (plane), None) for plane in 'RGB']
        # if all three planes were generated, construct the target array
        if RGB[0] != None and RGB[1] != None and RGB[2] != None:
            self.symbol[-1]['target']    = scipy.array(RGB)

        # read codefile every time to pick up changes dynamically.
        filename = kw['filename'] = kw.get('rpn', 'capture.rpn')
        self.interpret_load('!', filename)
        self.first = False

        # return generated target array or source array to Capture.py
        if self.ready:
            dx, dy = self.kernelX, self.kernelY
            target = self.symbol[-1].get('target', source)[dx:-dx, dy:-dy]
        else:
            return self.symbol[-1].get('target', source)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def internal_whoami(self, c='', r=''):
        """when verbose, report which interpreter branch was taken"""
        if self.verbose:
            print "%12s: \'%s\'" % (inspect.stack()[1][3], (c+r))

    #iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii
    def interpret_generic(self, c, r, k):
        if not c       : return [k, False, '']
        elif not c in k: return [0, False, '']
        self.internal_whoami(c+r)
        return                  [0,  True, (c+r).strip()]

    # Interpreter branches
    # Note: all these functions are self-choosing and self.documenting.
    # Absence of a first character forces it to return its key character.
    # Mismatch with key character forces it to return False
    # Match with key character causes it to self-identify/act and return True.
    #iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii
    def interpret_comment(self, c='', r=''):
        """comment ignores input"""
        (k, ret, line)  = self.interpret_generic(c, r, '#')
        if k or not ret: return k if k else ret
        return True

    #iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii
    def interpret_multipart(self, c='', r=''):
        """multipart instructions, for instance: (4|sqrt|show)"""
        (k, ret, line)  = self.interpret_generic(c, r, '(')
        if k or not ret: return k if k else ret
        if line[0] == '(' and line[-1] == ')':
            inside = line[1:-1]
            if inside[0] in self.interpret_define():
                self.interpret_define(inside[0], inside[1:])
            else:
                self.internal_interpret(
                        [item.strip() for item in inside.split('|')])
        return True

    #iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii
    def interpret_prompt(self, c='', r=''):
        """prompt changes the prompt to all chars after the key"""
        (k, ret, line)  = self.interpret_generic(c, r, '$')
        if k or not ret: return k if k else ret
        self.PS1 = r
        return True

    #iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii
    def interpret_number(self, c='', r=''):
        "number pushes legal float on stack, use negative to change sign"

        if False:
            return self.classNumber(rpn=self, c=c, r=r)
        else:
            (k, ret, line)  = self.interpret_generic(c, r, '0123456789')
            if k or not ret: return k if k else ret
            self.internal_push(float(line))
            return True

    #iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii
    #TODO consider preventing use of keywords.
    def interpret_symbol(self, c='', r=''):
        """pop the stack and store value as symbol"""
        (k, ret, line)  = self.interpret_generic(c, r, '@')
        if k or not ret: return k if k else ret
        self.symbol[-1][r] = self.internal_pop()
        return True

    #iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii
    def interpret_array(self, c='', r=''):
        """convert [] encapsulated data to scipy array"""
        (k, ret, line)  = self.interpret_generic(c, r, '[')
        if k or not ret: return k if k else ret
        self.internal_push(scipy.array(eval(c+r), float))
        return True

    #iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii
    def interpret_squote(self, c='', r=''):
        """push a name onto the stack"""
        (k, ret, line)  = self.interpret_generic(c, r, "'")
        if k or not ret: return k if k else ret
        self.internal_push(r)
        return True

    #iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii
    def interpret_print(self, c='', r=''):
        """print the message to stdout"""
        (k, ret, line)  = self.interpret_generic(c, r, '"')
        if k or not ret: return k if k else ret
        if self.first: print '%s' % (r)
        return True

    #iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii
    def interpret_define(self, c='', r=''):
        """define a function"""
        (k, ret, line)  = self.interpret_generic(c, r, ':')
        if k or not ret: return k if k else ret
        assert '|' in r
        name, code = r.split('|',1)
        code = [token.strip() for token in code.split('|')]
        self.symbol[-1][name] = code
        return True

    #iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii
    def interpret_load(self, c='', r=''):
        """pop a name from the stack, or 'r' is name, load a file as code"""
        (k, ret, line)  = self.interpret_generic(c, r, '!')
        if k or not ret: return k if k else ret
        filename = r if r else self.internal_pop()
        if not filename.endswith('.rpn'):
            filename += '.rpn'
            self.internal_load(filename)
        return True

    #iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii
    def interpret_pop(self, c='', r=''):
        """pop a number of items from the stack"""
        (k, ret, line)  = self.interpret_generic(c, r, '_')
        if k or not ret: return k if k else ret
        n = self.pop()
        for i in range(n):
            self.pop()
        return True

    #iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii
    def interpret_arithmetic(self, c='', r=''):
        """convert +-*/^ to scipy names and execute"""
        (k, ret, line)  = self.interpret_generic(c, r, arith.keys())
        if k or not ret: return k if k else ret
        eval('self.%s()' % (arith[c]))
        return True

    #iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii
    def interpret_call(self, c='', r=''):
        """function call as defined using ':'"""
        (k, ret, line)  = self.interpret_generic(c, r, '&')
        if k or not ret: return k if k else ret
        code = self.symbol[-1][r]
        self.internal_interpret(code)
        return True

    #iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii
    def interpret_quit(self, c='', r=''):
        """quit the interpreter"""
        (k, ret, line)  = self.interpret_generic(c, r, quits)
        if k or not ret: return k if k else ret
        sys.exit(0)
        return True

    #iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii
    def interpret_special(self, c='', r=''):
        """execute special function like .stack, .verbose, .quiet"""
        (k, ret, line)  = self.interpret_generic(c, r, spec)
        if k or not ret: return k if k else ret
        exec(spec[c+r])
        return True

    #iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii
    def interpret_function(self, c='', r=''):
        """execute extended internal or appended scipy function"""
        key = dir(self)
        if not c: return key
        if not c+r in key: return False
        self.internal_whoami(c+r)
        eval('self.%s()' % (c+r))
        return True

    #iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii
    def interpret_dictionary(self, c='', r=''):
        """push the value from a symbol onto the stack"""
        key = self.symbol[-1].keys()
        if not c: return key
        if not c+r in key: return False
        self.internal_whoami(c+r)
        self.internal_push(self.symbol[-1][c+r]);
        return True

    #iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii
    def interpret_rawPython(self, c='', r=''):
        """evaluate text as raw python code"""
        key = ''
        if not c: return key
        self.internal_whoami(c+r)
        eval(c+r)
        return True

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def internal_execute(self, first, rest):
        """march interpreter functions seeking a working candidate, and exec"""
        for name in RPN.sequence:
            function = RPN.functions[name]
            if function(self, first, rest):
                break

    #IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII
    # The primary method to call with a string to interpret.
    def internal_interpret(self, code):
        """execute one or many .rpn instructions"""
        if isinstance(code, types.ListType):
            """fragment a list and execute each instruction"""
            if code:
                for item in code:
                    self.internal_interpret(item)
        elif '\n' in code:
            """fragment a string and execute each instruction"""
            for single in [one.strip() for one in code.split('\n')]:
                self.internal_interpret(single)
        elif code:
            try:
                self.depth += 1
                """execute a single instruction"""
                if self.verbose:
                    print code

                code = code.strip()
                if code[0] == '#':
                    return self

                # get first character and the remaining string
                if self.extended_input != '':
                    # The space prevents accidental token appending.
                    code = self.extended_input + ' ' + code

                first, rest = code[:1], code[1:]
                # eliminate inline comment after instruction
                rest = (rest.split('#')[0] if '#' in rest else rest).strip()
                if rest != '':
                    t = rest[-1]
                    if t in '|,':
                        self.extended_input = first + rest
                        return self

                self.extended_input = ''
                # execute interpreter instruction
                self.internal_execute(first, rest)
                self.iteration += 1
            except Exception as e:
                print e
            finally:
                self.depth -= 1
        return self

    # Primitives
    # These functions are visible as interpreter keywords
    #pppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppp
    def clear(self):
        """reset the instance for a new interpreter run"""
        self.symbol=[{}]
        self.stack=[]
        self.verbose = False
        self.change = True

    #pppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppp
    def help(self):
        """extract and show interpreter key characters and words"""
        scipy_suite = argc+argp+arg1+arg2
        printlist = []
        local_suite = [
                'show',
                'zoom', 'diffract',
                'negative', 'normalize']
        for key, fun in RPN.functions.iteritems():
            """executing the function with no parameters returns the keys"""
            lead = fun()
            if isinstance(lead, str):
                head = '%s{%s}' % (str(lead), key[10:])
                if head[0] == '[':
                    prefix = '%s]' % (head)
                    printlist += [ '%-20s # %s' % (prefix, str(fun.__doc__)),]
                elif head[0] == '(':
                    prefix = '%s)' % (head)
                    printlist += [ '%-20s # %s' % (prefix, str(fun.__doc__)),]
                elif head[0] == '0':
                    prefix='{float}'
                    printlist += [ '%-20s # %s' % (prefix, str(fun.__doc__)),]
                else:
                    printlist += [ '%-20s # %s' % (head, str(fun.__doc__)),]
            elif isinstance(lead, dict):
                for k, v in lead.iteritems():
                    printlist += [ '%-20s # %s' % (k, v),]
            else:
                for name in lead:
                    if name in arg1:
                        printlist += [ '%-20s # from scipy suite (1 arg)' % (
                            name),]
                    elif name in arg2:
                        printlist += [ '%-20s # from scipy suite (2 args)' % (
                            name),]
                    elif name in argc:
                        printlist += [ '%-20s # from scipy suite (%e)' % (
                                name, eval('scipy.constants.%s' %
                                    (name))),]
                    elif name in argp:
                        printlist += [ '%-20s # from scipy suite (%e)' % (
                                name, eval('scipy.constants.constants.%s' %
                                    (name))),]
                    elif name in scipy_suite:
                        printlist += [ '%-20s # from scipy suite' % (name),]
                    elif name in quits:
                        printlist += [ '%-20s # quit keyword' % (name),]
                    elif name in local_suite:
                        printlist += [ '%-20s # direct keyword' % (name),]
                    else:
                        pass
        n, N = 0, len(printlist)
        while n < N:
            w, h = self.get_terminal()  # Handle changes in window size
            dn = h-1
            np = n+dn
            for text in printlist[n:N if N < np else np]:
                print text
            n = np
            q = raw_input('\tmore[<Enter>]')
            if q != '':
                break

    #pppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppppp
    def show(self):
        """show the top of the stack"""
        print self.stack[0]

    # Enhanced functions
    # These functions are visible as interpreter keywords
    #eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee
    def zoom(self):
        """
        zoom each color plane proportional to its wavelength
        zoom shrinks in proportion to wavelength
        """
        X, Y   = self.X, self.Y
        coeff  = self.internal_pop()
        offset = [X*(1.0-coeff)/2.0, Y*(1.0-coeff)/2.0]
        kernel = [[coeff, 0.0], [0.0, coeff]]
        self.internal_push(affine_transform(
            self.internal_pop(), kernel, offset=offset, prefilter=False))

    #eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee
    def diffract(self):
        """
        diffract all color planes equally (invariant to wavelength)
        Airy function expands in proportion to wavelength
        zoom shrinks in proportion to wavelength
        expansion * shrink == 1.0, so one kernel suffices.
        """
        # get the aperture
        pupil  = self.internal_pop()
        # get the color plane
        source = self.internal_pop()

        # don't generate a new kernel unless aperture changes
        # This is terrible.
        # Pupil should not be variable from function to function.
        # It should be universal and the following code
        # should be executed from the universal acquisition code.
        if pupil != self.aperture:
            """for a given aperture, generate a kernel (see Human.py)"""
            self.aperture    = pupil
            self.kernel      = self.human.genAiry(
                    0, 0, self.symbol[-1]['Rw'], pupil)
            self.Gauss       = self.human.genGauss(
                    self.symbol[-1]['Rw'])
            # Kernel should sum to 1.0
            self.kernel      = self.kernel / self.kernel.sum()
            self.kernelX, self.kernelY = self.kernel.shape
            radius           = self.kernelX/2
            self.kradius     = self.kradius if self.kradius>radius else radius
            self.kradius    /= 2
            self.mask = scipy.ones(source.shape)
            self.mask[0:self.kradius, :] = 0.0
            self.mask[:, 0:self.kradius] = 0.0
            self.mask[-self.kradius:-1,:] = 0.0
            self.mask[:,-self.kradius:-1] = 0.0
        # 'full' didn't eliminate the edge reflection defect.
        mode = self.symbol[-1].get('boundary', 'same')
        attenuate = 0.95
        temp      = attenuate * convolve(source, self.kernel, mode=mode)
        # Prevent the convolution defect from appearing
        # by limiting the image to within the non-defect region.
        temp     *= self.mask
        self.internal_push(temp)

    #eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee
    def average(self):
        source     = self.internal_pop()
        self.internal_push(source)
        #self.Gauss = self.human.genGauss(self.symbol[-1]['Rw'])
        #self.internal_push(convolve(source, self.Gauss, mode='same'))

    #eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee
    def negative(self):
        """invert the sign of the value at the top of stack"""
        self.internal_push(-self.internal_pop())

    #eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee
    def normalize(self):
        """Force the value at the top of stack to maximize at 1.0"""
        source = self.internal_pop()
        M = source.max()
        M = 1.0 if M == 0.0 else M
        self.internal_push(source/M)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # http://rosettacode.org/wiki/Terminal_control/Dimensions#Python
    def get_windows_terminal(self):
        from ctypes import windll, create_string_buffer
        h = windll.kernel32.GetStdHandle(-12)
        csbi = create_string_buffer(22)
        res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)

        #return default size if actual size can't be determined
        if not res: return 80, 25

        import struct
        (bufx, bufy, curx, cury, wattr, left, top, right, bottom, maxx, maxy)\
        = struct.unpack("hhhhHhhhhhh", csbi.raw)
        width = right - left + 1
        height = bottom - top + 1

        return width, height

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # http://rosettacode.org/wiki/Terminal_control/Dimensions#Python
    def get_linux_terminal(self):
        width = os.popen('tput cols', 'r').readline()
        height = os.popen('tput lines', 'r').readline()

        return int(width), int(height)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    # http://rosettacode.org/wiki/Terminal_control/Dimensions#Python
    def get_terminal(self):
        return (self.get_linux_terminal() if os.name == 'posix' else
                self.get_windows_terminal())

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# Note that this is a top-level function executed when the module is loaded.
def addscipy():
    """add scipy functions to RPN as class methods"""
    for a, f in ((argc,fmtc), (argp,fmtp), (arg1,fmt1), (arg2,fmt2)):
        for arg, fmt in product(a, f): exec(fmt % (arg, arg))

# This call adds all the scipy methods to the RPN class before instancing.
addscipy()

RPN.functions = {
    'interpret_multipart' : RPN.interpret_multipart,
    'interpret_comment'   : RPN.interpret_comment,
    'interpret_prompt'    : RPN.interpret_prompt,
    'interpret_number'    : RPN.interpret_number,
    'interpret_symbol'    : RPN.interpret_symbol,
    'interpret_array'     : RPN.interpret_array,
    'interpret_squote'    : RPN.interpret_squote,
    'interpret_print'     : RPN.interpret_print,
    'interpret_define'    : RPN.interpret_define,
    'interpret_load'      : RPN.interpret_load,
    'interpret_pop'       : RPN.interpret_pop,
    'interpret_arithmetic': RPN.interpret_arithmetic,
    'interpret_call'      : RPN.interpret_call,
    'interpret_quit'      : RPN.interpret_quit,
    'interpret_special'   : RPN.interpret_special,
    'interpret_function'  : RPN.interpret_function,
    'interpret_dictionary': RPN.interpret_dictionary,
    'interpret_rawPython' : RPN.interpret_rawPython,}

#MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM
if __name__ == '__main__':

    from Capture import Main

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def scipyFunctions(rpn, count, names):
        """execute all functions in the names list with right count of args"""
        for n in names:
            for i in range(count): rpn.internal_push(scipy.ones((2,2), float))
            print "%-10s" % (n)
            eval('rpn.%s()' % (n)); rpn.show(); rpn.clear()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def scipyConstants():
        """show all the functions in RPN constants lists"""
        for names in (argc, argp):
            for n in names:
                print "%-10s" % (n),
                eval('rpn.%s()' % (n)); rpn.show(); rpn.clear()

    # there are 3 good Main entrypoints and one for a bad command line
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def unittest(**kw):
        """Main entrypoint for unittests"""
        print "\tfunctions of one parameter"
        scipyFunctions(rpn, 1, arg1)
        print "\tfunctions of two parameters"
        scipyFunctions(rpn, 2, arg2)
        print "\tconstants"
        scipyConstants()
        print "\tcommands"
        cmds = [".verbose", "# A comment.", "4", "sqrt", "show"]
        rpn.internal_interpret(cmds[1:]) # without .verbose
        rpn.internal_interpret(cmds)     # with    .verbose
        rpn.internal_interpret('.')
        print "\tend of tests"

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def calculator(**kw):
        """Main entrypoint for command-line calculator"""
        try:
            if not os.isatty(file.fileno(sys.stdin)):
                for line in sys.stdin.readlines():
                    rpn.internal_interpret(line)
            else:
                while True:
                    prompt = rpn.internal_ps1
                    if rpn.extended_input != '':
                        prompt += '> '
                    rpn.internal_interpret(raw_input(prompt))
        except Exception, e:
            print traceback.print_exc()

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def capture(**kw):
        """Main entrypoint for screen capture, filter, and display"""
        #x, y = kw.get('x', 101), kw.get('y', 101)
        half = kw.get('radius', 50)
        edge = 1 + 2 * half
        x = y = edge
        main = Main(size=(x,y), **kw)
        main(**kw)

    #mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm
    mode = {'calculator':calculator,
            'unittest'  :unittest,
            'capture'   :capture   } #, 'illegal' :illegal }

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def illegal(**kw):
        """Main entrypoint if mode is poorly specified on command line"""
        print 'illegal mode argument(%s) given on command line' % (
                kw.get('mode', '?'))

    #mmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmmm
    mode['illegal'] = illegal

    #PPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPPP
    # Command-line parsing
    parser = OptionParser()
    parser.add_option(
            '-R', '--radius', type=int, default=50,
            help='radius of window')
    parser.add_option(
            '-r', '--rpn', type=str, default='capture.rpn',
            help='name of a .rpn file with code')
    parser.add_option(
            '-m', '--mode', type=str, default='calculator',
            help='mode: one of %s' % (str(mode.keys())))
    parser.add_option(
            '-e', '--ready', action="store_true", default=False, help="ready")
    parser.add_option(
            '-g', '--gpgpu', action="store_true", default=False, help="use gpgpu")
    parser.add_option(
            '-v', '--verbose', action="store_true", default=False, help="test")
    (opts, args) = parser.parse_args()
    kw = vars(opts)

    #IIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIIII
    # Instancing of the RPN class
    rpn = RPN(**kw);
    kw['fun'] = rpn

    #EEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE
    # Execution
    mode[kw.get('mode', 'illegal')](**kw)

###############################################################################
# RPN.py <EOF>
###############################################################################
