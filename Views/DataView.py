#----------------------------------------------------------------------
# Name:        DataView.py
# Purpose:     
#
# Author:      Riaan Booysen
#
# Created:     2000/02/14
# RCS-ID:      $Id$
# Copyright:   (c) 1999, 2000 Riaan Booysen
# Licence:     GPL
#----------------------------------------------------------------------

from wxPython.wx import *
from Designer import InspectableObjectCollectionView
from EditorModels import init_utils
import PaletteMapping, Utils
from PrefsKeys import keyDefs
import os
            
class DataView(wxListCtrl, InspectableObjectCollectionView):
    viewName = 'Data'
    collectionMethod = init_utils
    postBmp = 'Images/Inspector/Post.bmp'
    cancelBmp = 'Images/Inspector/Cancel.bmp'
    def __init__(self, parent, inspector, model, compPal):
        [self.wxID_DATAVIEW] = map(lambda _init_ctrls: wxNewId(), range(1))    
        wxListCtrl.__init__(self, parent, self.wxID_DATAVIEW, style = wxLC_SMALL_ICON)#wxLC_LIST)

        InspectableObjectCollectionView.__init__(self, inspector, model, compPal,
          (('Default editor', self.OnDefaultEditor, '-', ()),
           ('Post', self.OnPost, self.postBmp, ()),
           ('Cancel', self.OnCancel, self.cancelBmp, ()),
           ('-', None, '-', ()),
           ('Cut', self.OnCutSelected, '-', ()),
           ('Copy', self.OnCopySelected, '-', keyDefs['Copy']),
           ('Paste', self.OnPasteSelected, '-', keyDefs['Paste']),
           ('Delete', self.OnControlDelete, '-', keyDefs['Delete']),
           ), 0)

        self.il = wxImageList(24, 24)
        self.SetImageList(self.il, wxIMAGE_LIST_SMALL)

        EVT_LEFT_DOWN(self, self.OnSelectOrAdd)
        EVT_LIST_ITEM_SELECTED(self, self.wxID_DATAVIEW, self.OnObjectSelect)
        EVT_LIST_ITEM_DESELECTED(self, self.wxID_DATAVIEW, self.OnObjectDeselect)

        self.selection = []
        self.vetoSelect = false

        self.active = true

    def initialize(self):
        objCol = self.model.objectCollections[self.collectionMethod]
        objCol.indexOnCtrlName()

        deps, depLinks = {}, {}
        self.initObjectsAndCompanions(objCol.creators, objCol, deps, depLinks)

    def refreshCtrl(self):
        print 'refreshCtrl'
        self.DeleteAllItems()

        objCol = self.model.objectCollections[self.collectionMethod]
        objCol.indexOnCtrlName()

#        ctrls, props, events = self.organiseCollection()

        for ctrl in objCol.creators:
            print 'refreshCtrl', ctrl
            if ctrl.comp_name:
                try:
                    classObj = eval(ctrl.class_name)
                    className = classObj.__name__
                    idx1 = self.il.Add(PaletteMapping.bitmapForComponent(classObj, gray = true))
                except:
                    className = aclass
                    module = self.model.getModule()
                    if len(module.classes[aclass].super):
                        base = module.classes[aclass].super[0]
                        try: base = base.__class__.__name__
                        except: pass #print 'ERROR', base
                        idx1 = self.il.Add(PaletteMapping.bitmapForComponent(aclass, base, gray = true))
                    else:
                        idx1 = self.il.Add(PaletteMapping.bitmapForComponent(aclass, 'Component'))
                
                self.InsertImageStringItem(self.GetItemCount(), '%s : %s' % (ctrl.comp_name, className), idx1)

##        for name, idx in self.selection:
##            self.SetItemState(idx, wxLIST_STATE_SELECTED, wxLIST_STATE_SELECTED)

##        print '$$$$ INIT DV'
##        for i in self.collEditors.values():
##            print id(i.companion.textConstrLst),
##            print id(self.model.objectCollections[i.companion.collectionMethod].creators)

##    def renameCtrl(self, oldName, newName):
##        print self.objects

    def loadControl(self, ctrlClass, ctrlCompanion, ctrlName, params):
        """ Create and register given control and companion.
            See also: newControl """
        print 'loadControl', params
        args = self.setupArgs(ctrlName, params, self.handledProps)
        
        # Create control and companion
        companion = ctrlCompanion(ctrlName, self, ctrlClass)
        self.objects[ctrlName] = [companion, companion.designTimeObject(args), None]
        self.objectOrder.append(ctrlName)
        
        return ctrlName

    def selectNone(self):
        for itemIdx in range(self.GetItemCount()):
            a = wxLIST_STATE_SELECTED
            state = self.GetItemState(itemIdx, a)
            self.SetItemState(itemIdx, 0, a)

    def selectCtrls(self, ctrls):
        for itemIdx in range(self.GetItemCount()):
            name = string.split(self.GetItemText(itemIdx), ' : ')[0]
            a = wxLIST_STATE_SELECTED
            if name in ctrls: f = a
            else: f = 0
            state = self.GetItemState(itemIdx, a)
            self.SetItemState(itemIdx, f, a)

    def deleteCtrl(self, name, parentRef = None):
        self.selectNone()
        
        # notify other components of deletion
        self.notifyAction(self.objects[name][0], 'delete')
        
        InspectableObjectCollectionView.deleteCtrl(self, name, parentRef)
        self.refreshCtrl()                

    def renameCtrl(self, oldName, newName):
        InspectableObjectCollectionView.renameCtrl(self, oldName, newName)
        self.refreshCtrl()                

    def close(self):
##        print 'DATAVIEW CLOSE'
        self.cleanup()
        InspectableObjectCollectionView.close(self)

    def getSelectedName(self):
        return string.split(self.GetItemText(self.selection), ' : ')[0]

    def getSelectedNames(self):
        selected = []
        for itemIdx in range(self.GetItemCount()):
            name = string.split(self.GetItemText(itemIdx), ' : ')[0]
            state = self.GetItemState(itemIdx, wxLIST_STATE_SELECTED)
            if state:
                selected.append( (name, itemIdx) )
        return selected
                
    def OnSelectOrAdd(self, event):
        """ Control is clicked. Either select it or add control from palette """
        if self.compPal.selection:
            objName = self.newObject(self.compPal.selection[1], self.compPal.selection[2])
            self.compPal.selectNone()
            self.refreshCtrl()
            self.selectCtrls([objName])
        else:
            # Skip so that OnObjectSelect may be fired
            event.Skip()
    
    def updateSelection(self):
        if len(self.selection) == 1:
            self.inspector.selectObject(self.objects[self.selection[0][0]][0], false)
        else:
            self.inspector.cleanup()
##            self.selectNone()
    
    def OnObjectSelect(self, event):
        self.inspector.containment.cleanup()
        self.selection = self.getSelectedNames()
        print 'updateSelection', self.selection
        self.updateSelection()

    def OnObjectDeselect(self, event):
        event.Skip()
        if self.vetoSelect: return
        idx = 0
        while idx < len(self.selection):
            name, ctrlIdx = self.selection[idx]
            if ctrlIdx == event.m_itemIndex:
                del self.selection[idx]
            else:
                idx = idx + 1

#        self.inspector.cleanup()
        self.updateSelection()

    def OnPost(self, event):
        """ Close all designers and save all changes """
        self.controllerView.saveOnClose = true
        self.close()

    def OnCancel(self, event):
        """ Close all designers and discard all changes """
        self.controllerView.saveOnClose = false
        self.close()
    
    def OnCutSelected(self, event):
        """ Cut current selection to the clipboard """
        ctrls = map(lambda ni: ni[0], self.selection)

        output = []
        self.cutCtrls(ctrls, [], output)
        
        Utils.writeTextToClipboard(string.join(output, os.linesep))
        
        self.refreshCtrl()
        
    def OnCopySelected(self, event):
        """ Copy current selection to the clipboard """
        ctrls = map(lambda ni: ni[0], self.selection)
        print 'OnCopySelected', ctrls

        output = []
        self.copyCtrls(ctrls, [], output)

        Utils.writeTextToClipboard(string.join(output, os.linesep))

    def OnPasteSelected(self, event):
        """ Paste current clipboard contents into the current selection """
        pasted = self.pasteCtrls('', string.split(Utils.readTextFromClipboard(), 
                                                  os.linesep))
        if len(pasted):
            self.refreshCtrl()
            self.selectCtrls(pasted)
    
    def OnControlDelete(self, event):
        self.vetoSelect = true
        try:
            for name, idx in self.selection:
                self.deleteCtrl(name)
        finally:
            self.vetoSelect = false

        self.selection = self.getSelectedNames()
        self.updateSelection()

    def OnDefaultEditor(self, event):
        if len(self.selection) == 1:
            self.objects[self.selection[0][0]][0].defaultAction()        
        
        
        
    
