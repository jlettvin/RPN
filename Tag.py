#!/usr/bin/env python

"""
Tag.py
Generates subset of XML for report generation.
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

To prevent pollution the python namespace
tagnames are used in python as uppercase (i.e. TABLE, TR, TD).
tagnames are emitted in xhtml as lowercase (i.e. table, tr, td).

XML in reports does not comply with the XML standard.
http://www.w3.org/TR/REC-xml/

Variation 1: reports do not have a BOM or declaration.
<?xml version="1.0"?>

Variation 2: reports do not have a DTD.
<!DOCTYPE report SYSTEM "Logger.dtd">

The output of Tags.py is intended to resemble xhtml, an XML variant of HTML.
The use of uppercase tagnames in python has two resonances:
    1. HTML historically uses uppercase tags
    2. xhtml uses lowercase tags, but would tend to pollute python namespaces.

Use coverage.py for code coverage reporting.
http://nedbatchelder.com/code/coverage/
To confirm 100% code coverage:
    $ coverage run Tag.py
    $ coverage report -m

The following pattern identifies use cases within this source module.
    import Tag
    print [tag for tag in dir(Tag) if tag.startswith('test')]

Possible failures arise from:
    Accidentally not using 'close' when not making a context.
    For instance, this is an error:
        TD(a='b')
        TD(c='d')

Candidate xhtml tags to be implemented reside in external files.
multi.Tag contains tags to be implemented as contexts.
close.Tag contains tags to be implemented as immediate closers (i.e.<br/>).

Tag hierarchies must follow any rules specified in the file rules.Tag.
"""

__date__       = "20130101"
__author__     = "jlettvin"
__maintainer__ = "jlettvin"
__email__      = "jlettvin@gmail.com"
__copyright__  = "Copyright(c) 2013 Jonathan D. Lettvin, All Rights Reserved"
__license__    = "GPLv3"
__status__     = "Production"
__version__    = "0.0.1"

import os, sys, inspect, string
from Color      import Color
from Logger     import Logger
from RedirectIO import RedirectStdStreams

###############################################################################
# TAG BASE CLASS

class TAG(object):
    """
    TAG generates pretty-printable XML using 'with' contexts.

    Example tag generation is shown in TAG methods that follow this pattern:
        import Tag
        print [tag for tag in dir(Tag) if tag.startswith('test')]
    Three styles of XML are supported.
        *args: output text style
    0.       : <tagname a="1">\ntext\n</a> # Require a 'with' context
    1. single: <tagname a="1">text</a>     # Require a 'with' context
    2.  close: <tagname a="1"/>\n          # Don't use 'with' context (__del__)
    """
    buf        = '' # Accumulator string
    space      = 2  # Size of indent
    context    = [] # tag stack for validation against parents
    problem    = [] # list of errors encountered
    residual   = [] # leftover errors from last run survives final() method
    count      = {} # instance of tag (used for error message generation)

    #--------------------------------------------------------------------------
    @staticmethod
    def final(DTD="", ignore=False):
        """
        final() checks for errors, delivers accumulated string, and resets vars

        DTD   : if a non-empty string, generate standard XML header
        ignore: if True, bypass assert and
        """
        assert len(TAG.context) == 0 # All contexts should have been closed
        # Prior to clearing class vars, generate output
        # and prefix XML header if a DTD is specified
        output = ("""\
<?xml version="1.0"?>
<!DOCTYPE report SYSTEM "%s">
""" % (DTD) if DTD != "" else "") + TAG.buf
        # Prior to clearing class vars, hold onto errors
        hold = TAG.residual = TAG.errors()
        # Clear class vars
        TAG.buf     = ''
        TAG.problem = []
        TAG.count   = {}
        # Handle errors
        if 0 != len(hold) and not ignore:
            print output
            print hold
            raise Exception(str(hold))
        return output

    #--------------------------------------------------------------------------
    @staticmethod
    def add(msg):
        TAG.buf += msg

    #--------------------------------------------------------------------------
    @staticmethod
    def nl(msg):
        TAG.add(msg+'\n')

    #--------------------------------------------------------------------------
    @staticmethod
    def indent(confirm=True):
        return ' '*(len(TAG.context)*TAG.space) if confirm else ''

    #--------------------------------------------------------------------------
    @staticmethod
    def errors():
        return TAG.problem

    #--------------------------------------------------------------------------
    @staticmethod
    def residue():
        return TAG.residual

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def caller(self):
        caller = inspect.stack()[2]
        callfile = caller[1]
        callline = caller[2]
        callname = caller[3]
        return "%s[%d]: %s" % (callfile, callline, callname)

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def __del__(self):
        """
        __del__ is required to test for absence of context for keyword 'single'
        """
        if self.open:
            name, count = self.tagname.upper(), TAG.count[self.tagname]
            msg = "(%s) missing 'with' or 'close': %s instance %d" % (
                    self.caller(), name, count)
            TAG.problem  += [msg,]
            #raise Exception(TAG.problem)

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def __init__(self, tagname, *args, **kw):
        self.tagname      = tagname
        self.args         = args
        self.kw           = kw
        self.close        = False   # If True close within the same tag.
        self.single       = False   # If True keep on a single line.
        self.attributes   = ''

        TAG.count[tagname]= TAG.count.get(tagname, 0)+1
        # Make instance variables from kw
        for arg in args:
            exec('self.%s=True' % (arg))
        # Prepare for a context
        self.open         = True
        # But bypass context code id self-closing
        if self.close:
            # Generate the self-closing tag
            TAG.add(TAG.indent()+'<'+self.tagname)
            for key, val in self.kw.iteritems():
                TAG.add(' %s="%s"' % (key, val))
            TAG.nl('/>')
            # And make it illegal to go into a context.
            self.open     = False

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def __enter__(self):
        if not self.open:
            name, count = self.tagname.upper(), TAG.count[self.tagname]
            msg = "(%s) forbidden 'with' and 'close': %s instance %d" % (
                    self.caller(), name, count)
            TAG.problem  += [msg,]
        self.open = False # Used to assert closed on close, single, and multi.
        # Begin tag
        TAG.add(TAG.indent()+'<'+self.tagname)
        # Insert attributes
        for key, val in self.kw.iteritems():
            TAG.add(' %s="%s"' % (key, val))
        # Close with or without NL
        TAG.add('>') if self.single else TAG.nl('>')
        # Test validity of tree when required
        upname = self.tagname.upper()
        if upname in allow.keys():
            parents = allow[upname]
            if len(parents) > 0:
                assert TAG.context[-1] in parents # tag has  wrong parent
        # Update context stack
        TAG.context += [upname,]
        return self

    #++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
    def __exit__(self, aType, aValue, aTraceback):
        TAG.context = TAG.context[:-1]
        TAG.nl(TAG.indent(not self.single)+'</%s>' % (self.tagname))

###############################################################################
# TAG GENERATION

allow      = {}

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
def defineTag(tag, *args, **kw):
    """
    Define a class derived from TAG to satisfy rules in rules file.
    (i.e. rule: TABLE:[] will cause definition of the following class)
    +-------------------------------------------------------------+
    | class TABLE(TAG):                                           |
    |     def __init__(self, *args, **kw):                        |
    |         super(TABLE, self).__init__('table',*args,**kw)     |
    +-------------------------------------------------------------+
    """
    #TODO, does this next line break anything?  Check.
    kw = ''
    classline = "class %s(TAG):" % (tag)
    defline   = "def __init__(self, *args, **kw):"
    codeline  = "super(%s,self).__init__('%s',*args,**kw)" % (
            tag,tag.lower())
    generated = '%s\n    %s\n        %s' % (classline, defline, codeline)
    return generated

#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
with open('rules.Tag') as source:
    """
    Assimilate rules from rules file.
    """
    lines = [line for line in source.readlines()
             if not line.startswith('#')]
    code = string.join(lines, ' ')
    rules = eval(code)
    for bigkey, val in rules['parent'].iteritems():
        """composed keys with ':' in them are a key:arg pair."""
        if ':' in bigkey:
            key, cond = bigkey.split(':')
            assert cond.lower() in ['close', 'single']
            condict = {cond: True}
            allow[key] = val
            exec(defineTag(key, **condict))
        else:
            allow[bigkey] = val
            exec(defineTag(bigkey))

###############################################################################
# MAIN
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
        """Display colored text for two buffers with diff style markers."""
        # Prefer to put actual before expect since actual will be shown in red.
        print>>sys.stderr, '<'*79
        print>>sys.stderr, rw(actual)
        print>>sys.stderr, '='*79
        print>>sys.stderr, g_(expect)
        print>>sys.stderr, '>'*79

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def assertPass(**kw):
        testname = whoami(2)
        residual = str(kw.get('residue', ''))
        print g_('[PASS]'), testname, residual

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def assertFail(**kw):
        testname = whoami(2)
        residual = str(kw.get('residue', ''))
        print rw('[FAIL]'), testname, residual

    # assert methods for use by test methods.
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def assertPassFail(actual, expect, **kw):
        level    = kw.get('level', 1)
        check    = kw.get('check', True)
        force    = kw.get('force', False)
        testname = whoami(level+1)
        passfail = ((actual == expect) == check)
        residual = str(kw.get('residue', ''))
        print (g_('[PASS]') if passfail else rw('[FAIL]')), testname, residual
        if not passfail or force:
            showDiff(actual, expect)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def assertEqual(actual, expect, **kw):
        kw2 = kw.copy()
        kw2['level']=2
        assertPassFail(actual, expect, **kw2)

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    def assertNotEqual(actual, expect, **kw):
        kw2 = kw.copy()
        kw2['level']=2
        kw2['check']=False
        assertPassFail(actual, expect, **kw2)

    # XML attribute generation and management
    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    class Attributes(object):
        """
        Attributes generates generic attribute dictionaries for passing to Tag.
        Do not use this class directly to produce dictionaries.
        Use class Declare instead.
        """
        def __init__(self):
            self.content = {'fontattr':'normal', 'fieldattr':'normal'}

        @property
        def bold(self):
            self.content['fontattr'] = 'bold'
            return self

        @property
        def inverse(self):
            self.content['fieldattr'] = 'inverse'
            return self

        @property
        def final(self):
            return self.content

    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    class Declare(dict):
        """
        Declare generates specific attribute dictionaries for passing to Tag.
        """
        @property
        def Normal(self):
            normal = self.get('normal', None)
            if not normal:
                normal = self['normal'] = Attributes().final
            return normal

        @property
        def Emergency(self):
            normal = self.get('emergency', None)
            if not normal:
                normal = self['emergency'] = Attributes().bold.inverse.final
            return normal

    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # Local instancing to enable common usage in tests.
    declare = Declare()
    logger  = Logger()

    ###########################################################################
    # TESTS

    #TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
    def test_text_indent_within_TAG():
        """
        Test for ability to use or ignore text indent within a TAG.
        """
        expect = \
"""\
hello
world
hello
<a>
  world
and people in it
</a>
"""
        TAG.nl('hello')                     # Note absence of indent.
        TAG.nl('world')
        TAG.nl(TAG.indent()+'hello')        # Note presence of indent
        with TAG('a'):
            TAG.nl(TAG.indent()+'world')    # Note presence of indent
            TAG.nl('and people in it')      # Note absence of indent.
        assertEqual(TAG.final(), expect)

    #TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
    def test_TAG_indent_for_nested_contexts():
        """
        Test TAG indent for nested contexts.
        """
        expect = \
"""\
<a>
  <b>
    <c>
    </c>
  </b>
</a>
"""
        with TAG('a'):
            with TAG('b'):
                with TAG('c'):
                    pass
        assertEqual(TAG.final(), expect)

    #TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
    def test_TAG_list():
        expect = \
"""\
<a>Hello world</a>
<a>It's alive!</a>
"""
        with TAG('a', 'single'):
            TAG.add('Hello world')
        with TAG('a', 'single'):
            TAG.add("It's alive!")
        assertEqual(TAG.final(), expect)

    #TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
    def test_TAG_list_auto_close():
        expect = \
"""\
<a/>
<b/>
"""
        TAG('a', 'close')
        TAG('b', 'close')
        assertEqual(TAG.final(), expect)

    #TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
    def test_single_line_TAG_with_attributes():
        expect = \
"""\
<a c="d" e="f">Hello world</a>
<b i="j" g="h">It's alive!</b>
<c>
  <d k="l"/>
  <d m="n"/>
</c>
"""
        # TODO Fragile test because the order of attributes is not guaranteed.
        attributes = {'c':'d', 'e':'f'}
        with TAG('a', 'single', **attributes):  # Note use of separate dictionary.
            TAG.add('Hello world')
        attributes = {'g':'h', 'i':'j'}
        with TAG('b', 'single', **attributes):
            TAG.add("It's alive!")
        with TAG('c'):
            TAG('d', 'close', k='l')            # Note use of keyword dictionary.
            TAG('d', 'close', m='n')
        assertEqual(TAG.final(), expect)

    #TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
    def test_attributes_in_nested_TAG():
        expect = \
"""\
<z>
  <a c="d" e="f">Hello world</a>
  <y>
Is this fun?
  </y>
  <b i="j" g="h">It's alive!</b>
</z>
"""
        with TAG('z'):
            attributes = {'c':'d', 'e':'f'}
            with TAG('a', 'single', **attributes):
                TAG.add('Hello world')
            with TAG('y'):
                TAG.nl('Is this fun?')
            attributes = {'g':'h', 'i':'j'}
            with TAG('b', 'single', **attributes):
                TAG.add("It's alive!")
        # TODO Fragile test because the order of attributes is not guaranteed.
        assertEqual(TAG.final(), expect)

    #TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
    def test_missing_with_or_close():
        expect = \
"""\
<table a="b" c="d">
</table>
Note the missing TABLE (bad structure with no "with" or "close")
"""
        with TABLE(a='b', c='d'): pass
        try:
            TABLE(e='f', g='h')
        finally:
            pass
        TAG.nl('Note the missing TABLE (bad structure with no "with" or "close")')
        final   = TAG.final(ignore=True)
        residue = TAG.residue()                     # Get residual errors
        assertEqual(final, expect, residue=residue)

    #TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
    def test_failure():
        """Force a failed comparison to achieve 100% code coverage."""
        expect = \
"""\
invisible
"""
        with TABLE():
            TAG.nl('invisible')
        with open(os.devnull, 'w') as devnull:
            with RedirectStdStreams(stderr=devnull):
                final   = TAG.final()
                assertNotEqual(final, expect, force=True)
            with RedirectStdStreams(stdout=devnull, stderr=devnull):
                assertFail()

    #TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
    def test_context_close():
        """Keyword close should fail within a context."""
        buf     = ''
        residue = ''

        # RedirectIO contexts fail to pass exceptions through.
        devnull = open(os.devnull, 'w')
        _stdout, _stderr = sys.stdout, sys.stderr
        def flush():
            _stdout.flush()
            _stderr.flush()
        def hide():
            flush()
            sys.stdout, sys.stderr = devnull, devnull
        def show():
            flush()
            sys.stdout, sys.stderr = _stdout, _stderr

        try:
            with TABLE('close'): pass
            hide()
            buf = TAG.final()
        except:
            show()
            residue = TAG.residue()                     # Get residual errors
            assertPass(residue=residue) if residue else assertFail()
        devnull.close()

    #TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
    def test_bad_hierarchy():
        """Force a failed hierarchy to achieve 100% code coverage."""
        expect = \
"""\
invisible
"""
        try:
            with TABLE():
                with TD(): assertFail()
        except:
            TAG.final()
            assertPass()    # Failure is the pass condition

    #TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
    #def test_bad_single():
        #"""Force 'single' keyword to fail inside a context."""
        #expect = \
#"""\
#invisible
#"""
        #with TABLE('single'): pass
        #assertPass() if 0 != len(TAG.errors()) else assertFail()

    #TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
    def test_random_things():
        expect = \
"""\
<name name="name"/>
"""
        TAG.final()
        TAG('name', 'close', name='name')
        assertEqual(TAG.final(), expect)

    #TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
    def test_XML_tagnames():
        expect = \
"""\
<table>
  <tr>
    <td a="b" c="d"/>
    Ordinary text
  </tr>
</table>
"""
        with TABLE():
            with TR():
                TD('close', a='b', c='d') # Note lack of quotes on keys.
                TAG.nl(TAG.indent()+'Ordinary text')
        assertEqual(TAG.final(), expect)

    #TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
    def test_XML_with_simplified_attributes():
        expect = \
"""\
<table fieldattr="inverse" fontattr="bold">
  <tr>
    <td fieldattr="normal" fontattr="normal"/>
  </tr>
</table>
"""
        with TABLE(**declare.Emergency):
            with TR():
                TD('close', **declare.Normal)
        assertEqual(TAG.final(), expect)

    #TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
    def test_XML_attributes():
        expect = \
"""\
<table bgcolor="white" align="center" fontattribute="normal" width="500" href="" fontcolor="black">
  <tr>
    <td bgcolor="black" align="center" fontattribute="bold" width="500" href="" fontcolor="red"/>
  </tr>
</table>
"""
        render = rules['render']
        with TABLE(**render['cell.info']):
            with TR():
                TD('close', **render['cell.error'])
        assertEqual(TAG.final(), expect)

    #TTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTTT
    def test_XML_prologue():
        expect = \
"""\
<?xml version="1.0"?>
<!DOCTYPE report SYSTEM "Logger.dtd">
<table bgcolor="white" align="center" fontattribute="normal" width="500" href="" fontcolor="black">
  <tr>
    <td bgcolor="black" align="center" fontattribute="bold" width="500" href="" fontcolor="red"/>
  </tr>
</table>
"""
        render = rules['render']
        with TABLE(**render['cell.info']):
            with TR():
                TD('close', **render['cell.error'])
        assertEqual(TAG.final(DTD="Logger.dtd"), expect)

  #############################################################################
  # TEST
    def main():
        logger.info('='*79)

        test_text_indent_within_TAG()
        test_TAG_indent_for_nested_contexts()
        test_TAG_list()
        test_TAG_list_auto_close()
        test_single_line_TAG_with_attributes()
        test_attributes_in_nested_TAG()
        test_missing_with_or_close()
        test_failure()
        test_context_close()
        test_bad_hierarchy()
        #test_bad_single()
        test_random_things()
        test_XML_tagnames()
        test_XML_with_simplified_attributes()
        test_XML_attributes()
        test_XML_prologue()

        logger.info('='*79)

        logger.info('Use XML tags and attributes as illustrated in the last two.')
        logger.info('For a report on code coverage use coverage.py')
        logger.info('http://pypi.python.org/pypi/coverage')
        logger.info('$ coverage run ./Tag.py')
        logger.info('$ coverage report -m')

        logger.info('='*79)

    main()

###############################################################################
# Tag.py <EOF>
###############################################################################
