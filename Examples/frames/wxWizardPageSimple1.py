#Boa:WizardPageSimple:wxWizardPageSimple1

from wxPython.wx import *
from wxPython.wizard import *

[wxID_WXWIZARDPAGESIMPLE1, wxID_WXWIZARDPAGESIMPLE1BUTTON1, 
] = map(lambda _init_ctrls: wxNewId(), range(2))

class wxWizardPageSimple1(wxWizardPageSimple):
    def _init_ctrls(self, prnt):
        # generated method, don't edit
        wxWizardPageSimple.__init__(self, next=None, parent=prnt, prev=None)
        self.SetAutoLayout(True)

        self.button1 = wxButton(id=wxID_WXWIZARDPAGESIMPLE1BUTTON1,
              label='Simple Page 1', name='button1', parent=self, pos=wxPoint(8,
              8), size=wxSize(200, 32), style=0)
        self.button1.SetAutoLayout(True)

    def __init__(self, parent):
        self._init_ctrls(parent)
