# rules.Tag
#==============================================================================
# Copyright(c) 2013 Jonathan D. Lettvin, All Rights Reserved
# date   : 20130101
# author : jlettvin
# email  : jlettvin@google.com
# license: Trade secret
# status : Prototype
# version: 0.0.1
# action : specifies tagnames, required parents, and rendering styles
#==============================================================================
# rules.Tag is interpreted as python to generate global symbol 'rules'.
# rules['parent'] is a dictionary.
# rules['render'] is a dictionary.
#==============================================================================
# parent
# Tags specified in the 'parent' section are auto-generated as classes.
# See Tag.py TAG GENERATION section and test cases for usage.
#==============================================================================
# render
# Dictionaries specified in the 'render' section are available for
# modifying appearance during class instancing.
#==============================================================================
# Tag hierarchy requirements.
# Under the parent section, consider the key TABS.
# TABS is required to be a child of a SECTION.
# Any TABS that is not a child of a SECTION will trigger an assert.
# If a key has a list of multiple parents, then it will not trigger an assert
# if its parent is a member of the list.
#==============================================================================
# A Tag with a colon in its name is converted to a tagname and an option.
# Available options are 'close' and 'single'.
# Options are used as enforced args in TAG subclassing and instancing.
#==============================================================================
{
'parent':{
    'HTML'        : [],
    'HEAD'        : ['HTML',],
    'LINK'        : ['HEAD',],
    'BODY'        : ['HTML',],
    'BR:close'    : [],
    'H1'          : [],
    'H2'          : [],
    'H3'          : [],
    'FIELD:close' : [],
    'TABLE'       : [],
    'TABS'        : ['SECTION',],
    'TAB'         : ['TABS',],
    'SECTION'     : [],
    'TR'          : ['TABLE',],
    'TD:close'    : ['TR',],
    },
'render': {
    'cell.passed'  : {'width'        :'500',
                      'align'        :'center',
                      'href'         :'',
                      'fontcolor'    :'black',
                      'bgcolor'      :'green',
                      'fontattribute':'bold'},
    'cell.info'    : {'width'        :'500',
                      'align'        :'center',
                      'href'         :'',
                      'fontcolor'    :'black',
                      'bgcolor'      :'white',
                      'fontattribute':'normal'},
    'cell.warning' : {'width'        :'500',
                      'align'        :'center',
                      'href'         :'',
                      'fontcolor'    :'brown',
                      'bgcolor'      :'yellow',
                      'fontattribute':'bold'},
    'cell.error'   : {'width'        :'500',
                      'align'        :'center',
                      'href'         :'',
                      'fontcolor'    :'red',
                      'bgcolor'      :'black',
                      'fontattribute':'bold'},
    'cell.header'  : {'width'        :'500',
                      'align'        :'center',
                      'href'         :'',
                      'fontcolor'    :'black',
                      'bgcolor'      :'white',
                      'fontattribute':'bold'},
    'cell.critical': {},
    },
}
