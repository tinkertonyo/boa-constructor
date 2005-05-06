#-----------------------------------------------------------------------------
# Name:        BasicCompanions.py
# Purpose:
#
# Author:      Riaan Booysen
#
# Created:     2002
# RCS-ID:      $Id$
# Copyright:   (c) 2002 - 2005
# Licence:     GPL
#-----------------------------------------------------------------------------
print 'importing Companions.BasicCompanions'

from wxPython.wx import *

from wxPython.html import *
from wxPython.stc import *

from BaseCompanions import WindowDTC, ChoicedDTC

import Constructors
from EventCollections import *

from PropEdit.PropertyEditors import *
from PropEdit.Enumerations import *

class ScrollBarDTC(Constructors.MultiItemCtrlsConstr, WindowDTC):
    #wxDocs = HelpCompanions.wxScrollBarDocs
    def __init__(self, name, designer, parent, ctrlClass):
        WindowDTC.__init__(self, name, designer, parent, ctrlClass)
        self.windowStyles = ['wx.SB_HORIZONTAL', 'wx.SB_VERTICAL'] + self.windowStyles

    def designTimeSource(self, position = 'wx.DefaultPosition', size = 'wx.DefaultSize'):
        return {'pos': position,
                'size': size,
                'style': 'wx.SB_HORIZONTAL',
                'name': `self.name`}

    def events(self):
        return WindowDTC.events(self) + ['ScrollEvent', 'CmdScrollEvent']

EventCategories['ComboEvent'] = ('wx.EVT_COMBOBOX', 'wx.EVT_TEXT', 
                                 'wx.EVT_TEXT_ENTER')
commandCategories.append('ComboEvent')
class ComboBoxDTC(ChoicedDTC):
    #wxDocs = HelpCompanions.wxComboBoxDocs
    def __init__(self, name, designer, parent, ctrlClass):
        ChoicedDTC.__init__(self, name, designer, parent, ctrlClass)
        self.windowStyles = ['wx.CB_SIMPLE', 'wx.CB_DROPDOWN', 'wx.CB_READONLY',
                             'wx.CB_SORT'] + self.windowStyles

    def constructor(self):
        return {'Value': 'value', 'Position': 'pos', 'Size': 'size',
                'Choices': 'choices', 'Style': 'style',
                'Name': 'name'} 

    def designTimeSource(self, position = 'wx.DefaultPosition', size = 'wx.DefaultSize'):
        return {'value': `self.name`,
                'pos': position,
                'size': size,
                'choices': '[]',
                'style': '0',
                'name': `self.name`}

##    def vetoedMethods(self):
##        return ['GetColumns', 'SetColumns', 'GetSelection', 'SetSelection',
##                'GetStringSelection', 'SetStringSelection']
##
##    def hideDesignTime(self):
##        return ['Label']

    def events(self):
        return ChoicedDTC.events(self) + ['ComboEvent']

    def defaultAction(self):
        insp = self.designer.inspector
        insp.pages.SetSelection(2)
        insp.events.doAddEvent('ComboEvent', 'wx.EVT_COMBOBOX')

EventCategories['ChoiceEvent'] = ('wx.EVT_CHOICE',)
commandCategories.append('ChoiceEvent')
class ChoiceDTC(Constructors.ListConstr, ChoicedDTC):
    #wxDocs = HelpCompanions.wxChoiceDocs = 'wx41.htm'
    def designTimeSource(self, position = 'wx.DefaultPosition', size = 'wx.DefaultSize'):
        return {'pos': position,
                'size': size,
                'choices': `[]`,
                'style': '0',
                'name': `self.name`}

    def events(self):
        return ChoicedDTC.events(self) + ['ChoiceEvent']

    def defaultAction(self):
        insp = self.designer.inspector
        insp.pages.SetSelection(2)
        insp.events.doAddEvent('ChoiceEvent', 'wx.EVT_CHOICE')

class LabeledNonInputConstr:
    def constructor(self):
        return {'Position': 'pos', 'Size': 'size', 'Label': 'label',
                'Style': 'style', 'Name': 'name'}

class StaticTextDTC(LabeledNonInputConstr, WindowDTC):
    #wxDocs = HelpCompanions.wxStaticTextDocs
    def __init__(self, name, designer, parent, ctrlClass):
        WindowDTC.__init__(self, name, designer, parent, ctrlClass)
        self.windowStyles = ['wx.ALIGN_LEFT', 'wx.ALIGN_RIGHT', 'wx.ALIGN_CENTRE',
                             'wx.ST_NO_AUTORESIZE'] + self.windowStyles
    def designTimeSource(self, position = 'wx.DefaultPosition', size = 'wx.DefaultSize'):
        return {'label': `self.name`,
                'pos': position,
                'size': size,
                'style': '0',
                'name': `self.name`}

EventCategories['TextCtrlEvent'] = ('wx.EVT_TEXT', 'wx.EVT_TEXT_ENTER', 
                                    'wx.EVT_TEXT_URL', 'wx.EVT_TEXT_MAXLEN')
commandCategories.append('TextCtrlEvent')
class TextCtrlDTC(WindowDTC):
    #wxDocs = HelpCompanions.wxTextCtrlDocs
    def __init__(self, name, designer, parent, ctrlClass):
        WindowDTC.__init__(self, name, designer, parent, ctrlClass)
        self.windowStyles = ['wx.TE_PROCESS_ENTER', 'wx.TE_PROCESS_TAB',
                             'wx.TE_MULTILINE', 'wx.TE_PASSWORD',
                             'wx.TE_READONLY', 'wx.TE_RICH', 'wx.TE_RICH2', 
                             'wx.TE_AUTO_URL', 'wx.TE_NOHIDESEL',
                             'wx.TE_LEFT', 'wx.TE_CENTER', 'wx.TE_RIGHT', 
                             'wx.TE_DONTWRAP', 'wx.TE_LINEWRAP', 'wx.TE_WORDWRAP',
                             ] + self.windowStyles
        self._maxLength = 0
        self.initPropsThruCompanion.append('MaxLength')

    def properties(self):
        props = WindowDTC.properties(self)
        props.update({'MaxLength':  ('CompnRoute', self.GetMaxLength, self.SetMaxLength)})
        return props

    def constructor(self):
        return {'Value': 'value', 'Position': 'pos', 'Size': 'size',
                'Style': 'style', 'Name': 'name'}

    def designTimeSource(self, position = 'wx.DefaultPosition', size = 'wx.DefaultSize'):
        return {'value': `self.name`,
                'pos': position,
                'size': size,
                'style': '0',
                'name': `self.name`}

    def hideDesignTime(self):
        return WindowDTC.hideDesignTime(self) + \
              ['Selection', 'Title', 'Label', 'DefaultStyle']

    def events(self):
        return WindowDTC.events(self) + ['TextCtrlEvent']

    def GetMaxLength(self, x):
        return self._maxLength

    def SetMaxLength(self, value):
        self._maxLength = value
        self.control.SetMaxLength(value)


EventCategories['RadioButtonEvent'] = ('wx.EVT_RADIOBUTTON',)
commandCategories.append('RadioButtonEvent')
class RadioButtonDTC(Constructors.LabeledInputConstr, WindowDTC):
    #wxDocs = HelpCompanions.wxRadioButtonDocs
    def __init__(self, name, designer, parent, ctrlClass):
        WindowDTC.__init__(self, name, designer, parent, ctrlClass)
        self.editors['Value'] = BoolPropEdit
        self.windowStyles = ['wx.RB_GROUP'] + self.windowStyles

    def designTimeSource(self, position = 'wx.DefaultPosition', size = 'wx.DefaultSize'):
        return {'label': `self.name`,
                'pos': position,
                'size': size,
                'style': '0',
                'name': `self.name`}

    def events(self):
        return WindowDTC.events(self) + ['RadioButtonEvent']

    def defaultAction(self):
        insp = self.designer.inspector
        insp.pages.SetSelection(2)
        insp.events.doAddEvent('RadioButtonEvent', 'wx.EVT_RADIOBUTTON')


EventCategories['CheckBoxEvent'] = ('wx.EVT_CHECKBOX',)
commandCategories.append('CheckBoxEvent')
class CheckBoxDTC(Constructors.LabeledInputConstr, WindowDTC):
    #wxDocs = HelpCompanions.wxCheckBoxDocs = 'wx39.htm'
    def __init__(self, name, designer, parent, ctrlClass):
        WindowDTC.__init__(self, name, designer, parent, ctrlClass)
        self.editors['Value'] = BoolPropEdit
    def designTimeSource(self, position = 'wx.DefaultPosition', size = 'wx.DefaultSize'):
        return {'label': `self.name`,
                'pos': position,
                'size': size,
                'style': '0',
                'name': `self.name`}
    def events(self):
        return WindowDTC.events(self) + ['CheckBoxEvent']

    def defaultAction(self):
        insp = self.designer.inspector
        insp.pages.SetSelection(2)
        insp.events.doAddEvent('CheckBoxEvent', 'wx.EVT_CHECKBOX')


class SliderDTC(WindowDTC):
    #wxDocs = HelpCompanions.wxSliderDocs
    def __init__(self, name, designer, parent, ctrlClass):
        WindowDTC.__init__(self, name, designer, parent, ctrlClass)
        self.editors['MinValue'] = IntConstrPropEdit
        self.editors['MaxValue'] = IntConstrPropEdit
        self.windowStyles = ['wx.SL_HORIZONTAL', 'wx.SL_VERTICAL',
                             'wx.SL_AUTOTICKS', 'wx.SL_LABELS', 'wx.SL_LEFT',
                             'wx.SL_RIGHT', 'wx.SL_TOP',
                             'wx.SL_SELRANGE'] + self.windowStyles

    def constructor(self):
        return {'Value': 'value', 'MinValue': 'minValue', 'MaxValue': 'maxValue',
                'Position': 'point', 'Size': 'size', 'Style': 'style',
                'Name': 'name'} 

    def designTimeSource(self, position = 'wx.DefaultPosition', size = 'wx.DefaultSize'):
        return {'value': '0',
                'minValue': '0',
                'maxValue': '100',
                'point': position,
                'size': size,
                'style': 'wx.SL_HORIZONTAL',
                'name': `self.name`}

    def hideDesignTime(self):
        return WindowDTC.hideDesignTime(self) + ['TickFreq']

    def events(self):
        return WindowDTC.events(self) + ['ScrollEvent', 'CmdScrollEvent']

    def defaultAction(self):
        insp = self.designer.inspector
        insp.pages.SetSelection(2)
        insp.events.doAddEvent('ScrollEvent', 'wx.EVT_SCROLL')

class GaugeDTC(WindowDTC):
    #wxDocs = HelpCompanions.wxGaugeDocs
    def __init__(self, name, designer, parent, ctrlClass):
        WindowDTC.__init__(self, name, designer, parent, ctrlClass)
        self.windowStyles = ['wx.GA_HORIZONTAL', 'wx.GA_VERTICAL',
                        'wx.GA_PROGRESSBAR', 'wx.GA_SMOOTH'] + self.windowStyles

    def constructor(self):
        return {'Range': 'range', 'Position': 'pos', 'Size': 'size',
                'Style': 'style', 'Name': 'name'} 

    def designTimeSource(self, position = 'wx.DefaultPosition', size = 'wx.DefaultSize'):
        return {'range': '100',
                'pos': position,
                'size': size,
                'style': 'wx.GA_HORIZONTAL',
                'name': `self.name`}

class StaticBoxDTC(LabeledNonInputConstr, WindowDTC):
    #wxDocs = HelpCompanions.wxStaticBoxDocs
    def designTimeSource(self, position = 'wx.DefaultPosition', size = 'wx.DefaultSize'):
        return {'label': `self.name`,
                'pos': position,
                'size': self.getDefCtrlSize(),
                'style': '0',
                'name': `self.name`}
    
    def properties(self):
        props = WindowDTC.properties(self)
        del props['Sizer']
        return props

class StaticLineDTC(Constructors.WindowConstr, WindowDTC):
    #wxDocs = HelpCompanions.wxStaticLineDocs
    def __init__(self, name, designer, parent, ctrlClass):
        WindowDTC.__init__(self, name, designer, parent, ctrlClass)
        self.windowStyles = ['wx.LI_HORIZONTAL', 'wx.LI_VERTICAL'] + self.windowStyles

    def designTimeSource(self, position = 'wx.DefaultPosition', size = 'wx.DefaultSize'):
        return {'pos': position,
                'size': size,
                'style': '0',
                'name': `self.name`}

class StaticBitmapDTC(WindowDTC):
    #wxDocs = HelpCompanions.wxStaticBitmapDocs
    def __init__(self, name, designer, parent, ctrlClass):
        WindowDTC.__init__(self, name, designer, parent, ctrlClass)
        self.editors['Bitmap'] = BitmapPropEdit

    def constructor(self):
        return {'Bitmap': 'bitmap', 'Label': 'label', 'Position': 'pos',
                'Size': 'size', 'Style': 'style', 'Name': 'name'}

    def designTimeSource(self, position = 'wx.DefaultPosition', size = 'wx.DefaultSize'):
        return {'bitmap': 'wx.NullBitmap',
                'pos': position,
                'size': size,
                'style': '0',
                'name': `self.name`}

class HtmlWindowDTC(WindowDTC):
    def __init__(self, name, designer, parent, ctrlClass):
        WindowDTC.__init__(self, name, designer, parent, ctrlClass)
        self.windowStyles = ['wx.html.HW_SCROLLBAR_NEVER', 'wx.html.HW_SCROLLBAR_AUTO'] + self.windowStyles
        self._borders = 10
        self.initPropsThruCompanion.append('Borders')

    def constructor(self):
        return {'Position': 'pos', 'Size': 'size', 'Name': 'name', 'Style': 'style'}

    def designTimeSource(self, position = 'wx.DefaultPosition', size = 'wx.DefaultSize'):
        return {'pos': position,
                'size': self.getDefCtrlSize(),
                'style': 'wx.html.HW_SCROLLBAR_AUTO',
                'name': `self.name`}

    def properties(self):
        props = WindowDTC.properties(self)
        props.update({'Borders':  ('CompnRoute', self.GetBorders, self.SetBorders)})
        return props

    def events(self):
        return WindowDTC.events(self) + ['ScrollEvent']

    def writeImports(self):
        return '\n'.join( (WindowDTC.writeImports(self), 
                           'import wx.html') )

    def GetBorders(self, x):
        return self._borders

    def SetBorders(self, value):
        self._borders = value
        self.control.SetBorders(value)

stcEOLMode = [wxSTC_EOL_CRLF, wxSTC_EOL_CR, wxSTC_EOL_LF]
stcEOLModeNames = {'wx.stc.STC_EOL_CRLF': wxSTC_EOL_CRLF,
                   'wx.stc.STC_EOL_CR': wxSTC_EOL_CR,
                   'wx.stc.STC_EOL_LF': wxSTC_EOL_LF}

stcEdgeMode = [wxSTC_EDGE_NONE, wxSTC_EDGE_LINE, wxSTC_EDGE_BACKGROUND]
stcEdgeModeNames = {'wx.stc.STC_EDGE_NONE': wxSTC_EDGE_NONE,
                    'wx.stc.STC_EDGE_LINE': wxSTC_EDGE_LINE,
                    'wx.stc.STC_EDGE_BACKGROUND': wxSTC_EDGE_BACKGROUND}

stcLexer = [wxSTC_LEX_NULL, wxSTC_LEX_PYTHON, wxSTC_LEX_CONTAINER,
            wxSTC_LEX_CPP , wxSTC_LEX_HTML , wxSTC_LEX_XML, wxSTC_LEX_PERL,
            wxSTC_LEX_SQL, wxSTC_LEX_VB, wxSTC_LEX_PROPERTIES,
            wxSTC_LEX_ERRORLIST, wxSTC_LEX_MAKEFILE, wxSTC_LEX_BATCH,
            wxSTC_LEX_XCODE, wxSTC_LEX_LATEX, wxSTC_LEX_LUA, wxSTC_LEX_DIFF,
            wxSTC_LEX_CONF, wxSTC_LEX_PASCAL, wxSTC_LEX_AVE, wxSTC_LEX_ADA,
            wxSTC_LEX_LISP, wxSTC_LEX_RUBY, wxSTC_LEX_EIFFEL, wxSTC_LEX_EIFFELKW,
            wxSTC_LEX_TCL, wxSTC_LEX_NNCRONTAB, wxSTC_LEX_BULLANT,
            wxSTC_LEX_VBSCRIPT, wxSTC_LEX_ASP, wxSTC_LEX_PHP, wxSTC_LEX_BAAN,
            wxSTC_LEX_MATLAB, wxSTC_LEX_SCRIPTOL, wxSTC_LEX_AUTOMATIC]
stcLexerNames = {'wx.stc.STC_LEX_NULL': wxSTC_LEX_NULL,
      'wx.stc.STC_LEX_PYTHON': wxSTC_LEX_PYTHON,
      'wx.stc.STC_LEX_CONTAINER': wxSTC_LEX_CONTAINER,
      'wx.stc.STC_LEX_CPP': wxSTC_LEX_CPP, 'wx.stc.STC_LEX_HTML': wxSTC_LEX_HTML,
      'wx.stc.STC_LEX_XML': wxSTC_LEX_XML, 'wx.stc.STC_LEX_PERL': wxSTC_LEX_PERL,
      'wx.stc.STC_LEX_SQL': wxSTC_LEX_SQL, 'wx.stc.STC_LEX_VB': wxSTC_LEX_VB,
      'wx.stc.STC_LEX_PROPERTIES': wxSTC_LEX_PROPERTIES,
      'wx.stc.STC_LEX_ERRORLIST': wxSTC_LEX_ERRORLIST,
      'wx.stc.STC_LEX_MAKEFILE': wxSTC_LEX_MAKEFILE,
      'wx.stc.STC_LEX_BATCH': wxSTC_LEX_BATCH,
      'wx.stc.STC_LEX_XCODE': wxSTC_LEX_XCODE, 'wx.stc.STC_LEX_LATEX': wxSTC_LEX_LATEX,
      'wx.stc.STC_LEX_LUA': wxSTC_LEX_LUA, 'wx.stc.STC_LEX_DIFF': wxSTC_LEX_DIFF,
      'wx.stc.STC_LEX_CONF': wxSTC_LEX_CONF, 'wx.stc.STC_LEX_PASCAL': wxSTC_LEX_PASCAL,
      'wx.stc.STC_LEX_AVE': wxSTC_LEX_AVE, 'wx.stc.STC_LEX_ADA': wxSTC_LEX_ADA,
      'wx.stc.STC_LEX_LISP': wxSTC_LEX_LISP, 'wx.stc.STC_LEX_RUBY': wxSTC_LEX_RUBY,
      'wx.stc.STC_LEX_EIFFEL': wxSTC_LEX_EIFFEL,
      'wx.stc.STC_LEX_EIFFELKW': wxSTC_LEX_EIFFELKW,
      'wx.stc.STC_LEX_TCL': wxSTC_LEX_TCL, 'wx.stc.STC_LEX_NNCRONTAB': wxSTC_LEX_NNCRONTAB,
      'wx.stc.STC_LEX_BULLANT': wxSTC_LEX_BULLANT,
      'wx.stc.STC_LEX_VBSCRIPT': wxSTC_LEX_VBSCRIPT, 'wx.stc.STC_LEX_ASP': wxSTC_LEX_ASP,
      'wx.stc.STC_LEX_PHP': wxSTC_LEX_PHP, 'wx.stc.STC_LEX_BAAN': wxSTC_LEX_BAAN,
      'wx.stc.STC_LEX_MATLAB': wxSTC_LEX_MATLAB,
      'wx.stc.STC_LEX_SCRIPTOL': wxSTC_LEX_SCRIPTOL,
      'wx.stc.STC_LEX_AUTOMATIC': wxSTC_LEX_AUTOMATIC}

stcPrintColourMode = [wxSTC_PRINT_NORMAL, wxSTC_PRINT_INVERTLIGHT,
      wxSTC_PRINT_BLACKONWHITE, wxSTC_PRINT_COLOURONWHITE,
      wxSTC_PRINT_COLOURONWHITEDEFAULTBG]
stcPrintColourModeNames = {'wx.stc.STC_PRINT_NORMAL': wxSTC_PRINT_NORMAL,
      'wx.stc.STC_PRINT_INVERTLIGHT': wxSTC_PRINT_INVERTLIGHT,
      'wx.stc.STC_PRINT_BLACKONWHITE': wxSTC_PRINT_BLACKONWHITE,
      'wx.stc.STC_PRINT_COLOURONWHITE': wxSTC_PRINT_COLOURONWHITE,
      'wx.stc.STC_PRINT_COLOURONWHITEDEFAULTBG': wxSTC_PRINT_COLOURONWHITEDEFAULTBG}

stcWrapMode = [wxSTC_WRAP_NONE, wxSTC_WRAP_WORD]
stcWrapModeNames = {'wx.stc.STC_WRAP_NONE': wxSTC_WRAP_NONE,
                    'wx.stc.STC_WRAP_WORD': wxSTC_WRAP_WORD}

class StyledTextCtrlDTC(Constructors.WindowConstr, WindowDTC):
    def __init__(self, name, designer, parent, ctrlClass):
        WindowDTC.__init__(self, name, designer, parent, ctrlClass)
        self.editors.update(
            {'BackSpaceUnIndents': BoolPropEdit,
             'BufferedDraw': BoolPropEdit,
             'CaretLineVisible': BoolPropEdit,
             'EndAtLastLine': BoolPropEdit,
             'IndentationGuides': BoolPropEdit,
             'MouseDownCaptures': BoolPropEdit,
             'Overtype': BoolPropEdit,
             'ReadOnly': BoolPropEdit,
             'UndoCollection': BoolPropEdit,
             'UseHorizontalScrollBar': BoolPropEdit,
             'UseTabs': BoolPropEdit,
             'ViewEOL': BoolPropEdit,
             'ViewWhiteSpace': BoolPropEdit,
             'EOLMode': EnumPropEdit,
             'EdgeMode': EnumPropEdit,
             'Lexer': EnumPropEdit,
             'PrintColourMode': EnumPropEdit,
             'WrapMode': EnumPropEdit,
            })

        self.options.update({'EOLMode'   : stcEOLMode,
                             'EdgeMode' : stcEdgeMode,
                             'Lexer': stcLexer,
                             'PrintColourMode': stcPrintColourMode,
                             'WrapMode': stcWrapMode,
                            })
        self.names.update({'EOLMode'   : stcEOLModeNames,
                           'EdgeMode' : stcEdgeModeNames,
                           'Lexer': stcLexerNames,
                           'PrintColourMode': stcPrintColourModeNames,
                           'WrapMode': stcWrapModeNames,
                          })

    def designTimeSource(self, position='wx.DefaultPosition', size='wx.DefaultSize'):
        return {'pos': position,
                'size': self.getDefCtrlSize(),
                'style': '0',
                'name': `self.name`}

    def hideDesignTime(self):
        return WindowDTC.hideDesignTime(self) + ['Anchor', 'CodePage',
               'DocPointer', 'LastKeydownProcessed', 'ModEventMask',
               'Status', 'STCFocus']

    def writeImports(self):
        return '\n'.join( (WindowDTC.writeImports(self), 
                           'import wx.stc') )

#-------------------------------------------------------------------------------
import PaletteStore

PaletteStore.paletteLists['BasicControls'] = []
PaletteStore.palette.append(['Basic Controls', 'Editor/Tabs/Basic',
                             PaletteStore.paletteLists['BasicControls']])
PaletteStore.paletteLists['BasicControls'].extend([wxStaticText, wxTextCtrl,
  wxComboBox, wxChoice, wxCheckBox, wxRadioButton, wxSlider, wxGauge,
  wxScrollBar, wxStaticBitmap, wxStaticLine, wxStaticBox, wxHtmlWindow,
  wxStyledTextCtrl])


PaletteStore.compInfo.update({
    wxStaticText: ['wx.StaticText', StaticTextDTC],
    wxTextCtrl: ['wx.TextCtrl', TextCtrlDTC],
    wxChoice: ['wx.Choice', ChoiceDTC],
    wxComboBox: ['wx.ComboBox', ComboBoxDTC],
    wxCheckBox: ['wx.CheckBox', CheckBoxDTC],
    wxRadioButton: ['wx.RadioButton', RadioButtonDTC],
    wxSlider: ['wx.Slider', SliderDTC],
    wxGauge: ['wx.Gauge', GaugeDTC],
    wxStaticBitmap: ['wx.StaticBitmap', StaticBitmapDTC],
    wxScrollBar: ['wx.ScrollBar', ScrollBarDTC],
    wxStaticBox: ['wx.StaticBox', StaticBoxDTC],
    wxStaticLine: ['wx.StaticLine', StaticLineDTC],
    wxHtmlWindow: ['wx.html.HtmlWindow', HtmlWindowDTC],
    wxStyledTextCtrl: ['wx.stc.StyledTextCtrl', StyledTextCtrlDTC],
})
