#-----------------------------------------------------------------------------
# Name:        CVSExplorer.py
# Purpose:
#
# Author:      Riaan Booysen
#
# Created:     2000/10/22
# RCS-ID:      $Id$
# Copyright:   (c) 1999 - 2005 Riaan Booysen
# Licence:     GPL
#-----------------------------------------------------------------------------
print 'importing Explorers.CVSExplorer'

""" Explorer classes for CVS browsing and operations """

import time, stat, os

from wxPython.lib.dialogs import wxScrolledMessageDialog
from wxPython.wx import *

import ExplorerNodes
from Models import EditorModels, EditorHelper
from Preferences import IS

import ProcessProgressDlg, Utils
import scrm

cvs_environ_vars = ['CVSROOT', 'CVS_RSH', 'HOME']
cvs_environ_ids  = map(lambda x: wxNewId(), range(len(cvs_environ_vars)))

(wxID_CVSUPDATE, wxID_CVSCOMMIT, wxID_CVSADD, wxID_CVSADDBINARY, wxID_CVSREMOVE,
 wxID_CVSDIFF, wxID_CVSLOG, wxID_CVSSTATUS, wxID_FSCVSIMPORT, wxID_FSCVSCHECKOUT,
 wxID_FSCVSLOGIN, wxID_FSCVSLOGOUT, wxID_FSCVSENV, wxID_CVSTAG, wxID_CVSBRANCH,
 wxID_CVSLOCK, wxID_CVSUNLOCK, wxID_CVSTEST) = Utils.wxNewIds(18)

cvsFolderImgIdx = 6

def isCVS(filename):
    file = os.path.basename(filename)
    return file.lower() == 'cvs' and \
                      os.path.exists(os.path.join(filename, 'Entries')) and \
                      os.path.exists(os.path.join(filename, 'Repository')) and \
                      os.path.exists(os.path.join(filename, 'Root'))

def cvsFileLocallyModified(filename, timestamp):
    """  cvsFileLocallyModified -> modified, conflict """
    ismerge = timestamp.split('+')
    conflict = ismerge[0] == 'Result of merge'
    filets = time.asctime(time.gmtime(os.stat(filename)[stat.ST_MTIME]))
    if conflict and len(ismerge) == 1 or ismerge[0][:15] == 'dummy timestamp':
        filesegs, cvssegs = 1, 0
    # convert day to int to avoid zero padded differences
    else:
        if conflict:
            filesegs, cvssegs = filets.split(), ismerge[1].split()
        else:
            filesegs, cvssegs = filets.split(), timestamp.split()
        if cvssegs and cvssegs[0] == 'Initial' or len(cvssegs) < 3:
            cvssegs.append('0')
        # use day field of dates for comparison
        filesegs[2], cvssegs[2] = int(filesegs[2]), int(cvssegs[2])

    return (filesegs != cvssegs, conflict)


class CVSController(ExplorerNodes.Controller):
    updateBmp = 'Images/CvsPics/Update.png'
    commitBmp = 'Images/CvsPics/Commit.png'
    addBmp = 'Images/CvsPics/Add.png'
    addBinBmp = 'Images/CvsPics/AddBinary.png'
    removeBmp = 'Images/CvsPics/Remove.png'
    diffBmp = 'Images/CvsPics/Diff.png'
    logBmp = 'Images/CvsPics/Log.png'
    statusBmp = 'Images/CvsPics/Status.png'
    tagBmp = 'Images/CvsPics/Tag.png'
    branchBmp = 'Images/CvsPics/Branch.png'
    def __init__(self, editor, list, inspector, controllers):
        ExplorerNodes.Controller.__init__(self, editor)
        self.list = list
        self.menu = wxMenu()
        self.cvsOptions = '-z7'

        self.cvsMenuDef = [
              (wxID_CVSUPDATE, 'Update', self.OnUpdateCVSItems, self.updateBmp),
              (wxID_CVSCOMMIT, 'Commit', self.OnCommitCVSItems, self.commitBmp),
              (-1, '-', None, ''),
              (wxID_CVSADD, 'Add', self.OnAddCVSItems, self.addBmp),
              (wxID_CVSADDBINARY, 'Add binary', self.OnAddBinaryCVSItems, self.addBinBmp),
              (wxID_CVSREMOVE, 'Remove', self.OnRemoveCVSItems, self.removeBmp),
              (-1, '-', None, ''),
              (wxID_CVSDIFF, 'Diff', self.OnDiffCVSItems, self.diffBmp),
              (wxID_CVSLOG, 'Log', self.OnLogCVSItems, self.logBmp),
              (wxID_CVSSTATUS, 'Status', self.OnStatusCVSItems, self.statusBmp),
#              (wxID_CVSTEST, 'TEST', self.OnTest),
              (-1, '-', None, ''),
              (wxID_CVSTAG, 'Tag', self.OnTagCVSItems, self.tagBmp),
              (wxID_CVSBRANCH, 'Branch', self.OnBranchCVSItems, self.branchBmp),
              (wxID_CVSLOCK, 'Lock', self.OnLockCVSItems, '-'),
              (wxID_CVSUNLOCK, 'Unlock', self.OnUnlockCVSItems, '-') ]

        self.setupMenu(self.menu, self.list, self.cvsMenuDef)

        self.fileCVSMenuDef = [
              (wxID_FSCVSIMPORT, 'Import', self.OnImportCVSFSItems, '-'),
              (wxID_FSCVSCHECKOUT, 'Checkout', self.OnCheckoutCVSFSItems, '-'),
              (-1, '-', None, ''),
              (wxID_FSCVSLOGIN, 'Login', self.OnLoginCVS, '-'),
              (wxID_FSCVSLOGIN, 'SF Login', self.OnSFLoginCVS, '-'),
              (wxID_FSCVSLOGOUT, 'Logout', self.OnLogoutCVS, '-'),
        ]

        self.fileCVSMenu = wxMenu()
        self.setupMenu(self.fileCVSMenu, self.list, self.fileCVSMenuDef, false)

##        self.cvsEnvMenu = wxMenu()
##        menus = []
##        for env, id in map(lambda x, v = cvs_environ_vars, i = cvs_environ_ids: \
##            (v[x], i[x]), range(len(cvs_environ_vars))):
##            menus.append( (id, env, self.OnEditEnv, '-') )
##        self.setupMenu(self.cvsEnvMenu, self.list, menus)
##
##        self.fileCVSMenu.AppendMenu(wxID_FSCVSENV, 'CVS shell environment vars', self.cvsEnvMenu)

        self.images = wxImageList(16, 16)
        for cvsImg in ( 'Images/CvsPics/File.png',
                        'Images/CvsPics/BinaryFile.png',
                        'Images/CvsPics/ModifiedFile.png',
                        'Images/CvsPics/ModifiedBinaryFile.png',
                        'Images/CvsPics/MissingFile.png',
                        'Images/CvsPics/ConflictingFile.png',
                        'Images/CvsPics/Dir.png',
                        'Images/Modules/FolderUp.png',
                        'Images/CvsPics/UnknownDir.png',
                        'Images/CvsPics/UnknownFile.png'):
            self.images.Add(IS.load(cvsImg))

        self.toolbarMenus = [self.cvsMenuDef]

        FSCVSFolderNode.images = self.images

    def destroy(self):
        self.cvsMenuDef = ()
        self.fileCVSMenuDef = ()
        self.toolbarMenus = ()
        self.images = None
        FSCVSFolderNode.images = None
        self.menu.Destroy()

    def getName(self, item):
        name = ExplorerNodes.Controller.getName(self, item)
        if ' ' in name:
            return '"%s"' % name
        else:
            return name

    def setupListCtrl(self):
        self.list.SetWindowStyleFlag(wxLC_REPORT)
        self.list.InsertColumn(0, 'Name', wxLIST_FORMAT_LEFT, 150)
        self.list.InsertColumn(1, 'Rev.', wxLIST_FORMAT_LEFT, 50)
        self.list.InsertColumn(2, 'Date', wxLIST_FORMAT_LEFT, 150)
        self.list.InsertColumn(3, 'Status', wxLIST_FORMAT_LEFT, 150)
        self.list.InsertColumn(4, 'Options', wxLIST_FORMAT_LEFT, 50)

    def cleanupListCtrl(self):
        cols = range(5)
        cols.reverse()
        for col in cols:
            self.list.DeleteColumn(col)

    def showMessage(self, cmd, msg):
        dlg = wxScrolledMessageDialog(self.list, msg, cmd)
        try: dlg.ShowModal()
        finally: dlg.Destroy()

    def cvsCmd(self, command, options, files, extraOptions = ''):
        cvsOpts = self.cvsOptions
        if extraOptions:
            cvsOpts = '%s %s'%(cvsOpts, extraOptions)
        return 'cvs %s %s %s %s' % (cvsOpts, command, options, ' '.join(files))

    def cvsCmdPrompt(self, wholeCommand, inDir, help = ''):
        if isinstance(self.list.node, FSCVSFolderNode):
            cvsroot = self.list.node.root
        else:
            cvsroot = os.environ.get('CVSROOT', '(not defined)')
        dlg = wxTextEntryDialog(self.list, 'CVSROOT: %s\nCVS_RSH: %s\n(in dir %s)\n\n%s'\
              %(cvsroot, os.environ.get('CVS_RSH', '(not defined)'), inDir, help),
              'CVS command line', wholeCommand)
        if wxPlatform == '__WXMSW__':
            te = Utils.getCtrlsFromDialog(dlg, 'TextCtrl')[0]
            try:
                te.SetSelection(wholeCommand.index('['),
                                wholeCommand.index(']')+1)
            except ValueError:
                te.SetInsertionPoint(len(wholeCommand))
        try:
            if dlg.ShowModal() == wxID_OK:
                return dlg.GetValue()
            else:
                return ''
        finally:
            dlg.Destroy()

    def getCvsHelp(self, cmd, option = '-H'):
        CVSPD = ProcessProgressDlg.ProcessProgressDlg(self.list,
                  'cvs %s %s'% (option, cmd), '', modally=false)
        try:
            return ' '.join(CVSPD.errors[:-1]).expandtabs(8)
        finally:
            CVSPD.Destroy()

    # cvsOutput can be 'output window', 'dialogs' or 'tuple'
    def doCvsCmd(self, cmd, cvsDir, stdinput='', cvsOutput='output window'):
        # Repaint background
        wxYield()

        cwd = os.getcwd()
        try:
            os.chdir(cvsDir)
            CVSPD = ProcessProgressDlg.ProcessProgressDlg(self.list, cmd, 'CVS progress...')
            try:
                if CVSPD.ShowModal() == wxOK:
                    outls = CVSPD.output
                    errls = CVSPD.errors
                else:
                    return
            finally:
                CVSPD.Destroy()

            err = ''.join(errls).strip()

            if cvsOutput == 'output window':
                errout = self.editor.erroutFrm
                tbs = errout.updateCtrls((), outls, 'CVS Result', '', err)
                errout.display(tbs)

            elif cvsOutput == 'dialogs':
                if err.strip():
                    dlg = wxMessageDialog(self.list, err,
                      'Server response or Error', wxOK | wxICON_EXCLAMATION)
                    try: dlg.ShowModal()
                    finally: dlg.Destroy()

                if outls and not (len(outls) == 1 and not outls[0].strip()):
                    self.showMessage(cmd, ''.join(outls))
            elif cvsOutput == 'tuple':
                return outls, errls

            #msgType = 'warning' if err else 'info' # i wish
            if err: msgType = 'Warning'
            else: msgType = 'Info'
            self.editor.setStatus('CVS command completed: %s'%cmd, msgType)

        finally:
            os.chdir(cwd)

    def doCvsCmdOnSelection(self, cmd, cmdOpts,
              preCmdFunc=None, postCmdFunc=None, cvsOutput='output window'):
        if self.list.node:
            names = self.getNamesForSelection(self.list.getMultiSelection())
            cvsDir = os.path.dirname(self.list.node.resourcepath)
            if not names: names = ['']
##                names = ['']
##                cvsDir, names[0] = os.path.split(cvsDir)
            cmdStr = self.cvsCmdPrompt(self.cvsCmd(cmd, cmdOpts, names), cvsDir,
                  self.getCvsHelp(cmd))
            if cmdStr:
                if preCmdFunc: preCmdFunc(names)
                res = self.doCvsCmd(cmdStr, cvsDir, cvsOutput=cvsOutput)
                if postCmdFunc: postCmdFunc(names)
                return res

    def doCvsCmdInDir(self, cmd, cmdOpts, cvsDir, items, cvsOpts = ''):
        cmdStr = self.cvsCmdPrompt(self.cvsCmd(cmd, cmdOpts, items, cvsOpts),
              cvsDir, self.getCvsHelp(cmd))
        if cmdStr:
            self.doCvsCmd(cmdStr, cvsDir)
            return true
        else:
            return false

    def importCVSItems(self):
        # Imports are called from normal folders not CVS folders

        # XXX Check if CVS folder exists ?
        cvsDir = self.list.node.resourcepath
        if self.doCvsCmdInDir('import', '', cvsDir, ['[MODULE]', 'VENDOR', 'RELEASE']):
            self.list.refreshCurrent()


    def checkoutCVSItems(self):
        # Checkouts are called from normal folders not CVS folders
        file, lines = self.readCVSPass()
        del file
        cvsroots = []
        for line in lines:
            cvsroots.append(line.split()[0])
        if cvsroots:
            dlg = wxSingleChoiceDialog(self.list, 'Select and click OK to set CVSROOT'\
             ' or Cancel to use environment variable.\n\nYou have pserver access to the following servers:',
             'Choose CVSROOT (-d parameter)', cvsroots)
            try:
                if dlg.ShowModal() == wxID_OK:
                    cvsOpts = '-d'+dlg.GetStringSelection()
                else:
                    cvsOpts = ''
            finally:
                dlg.Destroy()
        else:
            cvsOpts = ''


        cvsDir = self.list.node.resourcepath
        if self.doCvsCmdInDir('checkout', '-P', cvsDir, ['[MODULE]'], cvsOpts):
            self.list.refreshCurrent()

    def updateCVSItems(self):
        self.doCvsCmdOnSelection('update', '')
        self.list.refreshCurrent()

    def OnUpdateCVSItems(self, event):
        self.updateCVSItems()

    def OnCommitCVSItems(self, event):
        self.doCvsCmdOnSelection('commit', '-m "[no message]"')
        self.list.refreshCurrent()

    def OnAddCVSItems(self, event):
        self.doCvsCmdOnSelection('add', '')
        self.list.refreshCurrent()

    def OnAddBinaryCVSItems(self, event):
        self.doCvsCmdOnSelection('add', '-kb')
        self.list.refreshCurrent()

    quotes = ('"', "'")
    def selPreCmd_remove(self, list):
        dir = os.path.dirname(self.list.node.resourcepath)
        for name in list:
            try:

                if name[0] in self.quotes and name[-1] in self.quotes:
                    name = name[1:-1]
                os.remove(os.path.join(dir, name))
            except OSError, err:
                # Skip files already removed
                print err

    def OnRemoveCVSItems(self, event):
        self.doCvsCmdOnSelection('remove', '', self.selPreCmd_remove)
        self.list.refreshCurrent()

    def OnDiffCVSItems(self, event):
        # a syntax highlighted window is provided for unified diffs
        res = self.doCvsCmdOnSelection('diff', '-u', cvsOutput='tuple')
        if res is not None and len(res)==2:
            outls, errls = res
            errout = self.editor.erroutFrm
            tbs = errout.updateCtrls((), outls, 'CVS Result', '', errls)
            errout.display(tbs)
            errout.displayDiff(''.join(outls))


    def OnLogCVSItems(self, event):
        self.doCvsCmdOnSelection('log', '')

    def OnStatusCVSItems(self, event):
        self.doCvsCmdOnSelection('status', '')

    def OnImportCVSFSItems(self, event):
        self.importCVSItems()

    def OnCheckoutCVSFSItems(self, event):
        self.checkoutCVSItems()

    def OnTagCVSItems(self, event):
        self.doCvsCmdOnSelection('tag', '[TAG]')

    def OnBranchCVSItems(self, event):
        self.doCvsCmdOnSelection('tag', '-b')

    def OnLockCVSItems(self, event):
        self.doCvsCmdOnSelection('admin', '-l[REV]')

    def OnUnlockCVSItems(self, event):
        self.doCvsCmdOnSelection('admin', '-u[REV]')

    def OnLoginCVS(self, event, cvsroot=''):
        cvsDir = self.list.node.resourcepath

        # Login can be called from file system folders and cvs folders
        if isinstance(self.list.node, FSCVSFolderNode):
            cvsroot = self.list.node.root
        else:
            if not cvsroot:
                if os.environ.has_key('CVSROOT'):
                    cvsroot = os.environ['CVSROOT']
                else:
                    cvsroot = ''

        cvsroot = self.cvsCmdPrompt(cvsroot, cvsDir, 
              help='Change the CVSROOT if necessary:')

        dlg = wxTextEntryDialog(self.list, 'Enter cvs password for '+cvsroot, 
              'CVS login', '', style=wxOK|wxCANCEL|wxCENTRE|wxTE_PASSWORD)
        try:
            if dlg.ShowModal() == wxID_OK:
                password = scrm.scramble(dlg.GetValue())
            else:
                return
        finally:
            dlg.Destroy()

        passfile, passwds = self.readCVSPass()

        passln = cvsroot + ' ' +password + '\n'

        if passln not in passwds:
            passfile.write(passln)
        passfile.close()

    def OnSFLoginCVS(self, event):
        self.OnLoginCVS(event, ':pserver:anonymous@cvs.sourceforge.net:/cvsroot/[PROJECT]')

    def readCVSPass(self):
        if os.environ.has_key('HOME') and os.path.isdir(os.environ['HOME']):
            cvspass = os.path.join(os.environ['HOME'], '.cvspass')
            if os.path.exists(cvspass):
                passfile = open(cvspass, 'r+')
                return passfile, passfile.readlines()
            else:
                return open(cvspass, 'w'), []
        else:
            raise Exception('HOME env var is not defined or not legal')

    def OnLogoutCVS(self, event):
        cvsDir = self.list.node.resourcepath
        self.doCvsCmdInDir('logout', '', cvsDir, [])

    def OnEditEnv(self, event):
        envKey = cvs_environ_vars[cvs_environ_ids.index(event.GetId())]
        envVal = os.environ.get(envKey, '(not defined)')
        dlg = wxTextEntryDialog(self.list, 'Edit CVS shell environment variable: %s\nA blank entry will remove the variable.'% envKey,
            'CVS shell environment variables', envVal)
        try:
            if dlg.ShowModal() == wxID_OK:
                answer = dlg.GetValue()
                if answer and answer != '(not defined)':
                    try:
                        os.environ[envKey] = answer
                    except:
                        wxMessageBox('Changing environment variables is not supported on this OS\nConsult CVS howtos on how to set these globally')
                else:
                    if os.environ.has_key(envKey):
                        del os.environ[envKey]
        finally:
            dlg.Destroy()

    def OnTest(self, event):
        print 'TEST'
#        self.list.SetWindowStyleFlag(wxLC_REPORT)
        self.setupListCtrl()

class CVSFolderNode(ExplorerNodes.ExplorerNode):
    protocol = 'cvs'
    def __init__(self, entriesLine, resourcepath, dirpos, parent):
        if entriesLine:
            name, self.revision, self.timestamp, self.options, self.tagdate = \
              entriesLine[2:].split('/')
        else:
            name=self.revision=self.timestamp=self.options=self.tagdate = ''

        ExplorerNodes.ExplorerNode.__init__(self, name, resourcepath, None, cvsFolderImgIdx, parent)

        self.dirpos = dirpos

    def text(self):
        return '/'.join(('D', self.name, self.revision, self.timestamp, self.options, self.tagdate))

    def isFolderish(self):
        return false

    def notifyBeginLabelEdit(self, event):
        event.Veto()

    def createParentNode(self):
        parent = os.path.abspath(os.path.join(self.resourcepath, '..'))
        return PyFileNode(os.path.basename(parent), parent, self.clipboard,
                  EditorModels.FolderModel.imgIdx, self)

    def open(self, editor):
        tree = editor.explorer.tree
        par = tree.GetItemParent(tree.GetSelection())
        chd = tree.getChildNamed(par, self.name)
        if not tree.IsExpanded(chd):
            tree.Expand(chd)
        cvsChd = tree.getChildNamed(chd, 'CVS')
        tree.SelectItem(cvsChd)
        return None, None

class CVSFileNode(ExplorerNodes.ExplorerNode):
    protocol = 'cvs'
    def __init__(self, entriesLine, resourcepath, parent):
        if entriesLine:
            name , self.revision, self.timestamp, self.options, self.tagdate = \
              entriesLine.strip()[1:].split('/')
        else:
            name=self.revision=self.timestamp=self.options=self=tagdate = ''

        ExplorerNodes.ExplorerNode.__init__(self, name, resourcepath, None, -1, parent)

        self.missing = false
        self.modified = false
        self.conflict = false
        self.imgIdx = 0
        if self.timestamp:
            filename = os.path.abspath(os.path.join(self.resourcepath, '..', name))
            if os.path.exists(filename):
                self.modified, self.conflict = cvsFileLocallyModified(filename, self.timestamp)
            else:
                self.missing = true

        self.imgIdx = self.missing and self.missing << 2 \
                      or (self.options == '-kb' and not self.modified) \
                      or (self.options == '-kb' and self.modified and 3) \
                      or self.conflict *5 or self.modified << 1

    def isFolderish(self):
        return false

    def notifyBeginLabelEdit(self, event):
        event.Veto()

    def getDescription(self):
        return '%s, (%s, %s)'%(self.name, self.revision, self.timestamp)#, self.options, self.tagdate), '/')

    def open(self, editor):
        tree = editor.explorer.tree
        node = editor.explorer.list.getSelection()
        timestamp = node.timestamp
        tree.SelectItem(tree.GetItemParent(tree.GetSelection()))
        editor.explorer.list.selectItemNamed(self.name)
        if self.conflict:
            node = editor.explorer.list.getSelection()

            if timestamp.startswith('Result of merge+'):
                model, controller = editor.openOrGotoModule(node.resourcepath,
                      transport=node)

                # XXX inefficient
                conflicts = model.getCVSConflicts()
                if conflicts:
                    from Views.EditorViews import CVSConflictsView
                    if not model.views.has_key(CVSConflictsView.viewName):
                        resultView = editor.addNewView(CVSConflictsView.viewName,
                              CVSConflictsView)
                    else:
                        resultView = model.views[CVSConflictsView.viewName]
                    resultView.refresh()
                    resultView.focus()
                else:
                    editor.setStatus('No CVS conflicts in file', 'Warning', true)

                return model, controller
        return None, None

    def text(self):
        return '/'.join(('', self.name, self.revision, self.timestamp, self.options, self.tagdate))

class CVSUnAddedItem(ExplorerNodes.ExplorerNode):
    def __init__(self, name, resourcepath, parent, isFolder):
        ExplorerNodes.ExplorerNode.__init__(self, name, resourcepath, None, isFolder and 8 or 9, parent)

    def open(self, editor):
        tree = editor.explorer.tree
        tree.SelectItem(tree.GetItemParent(tree.GetSelection()))
        editor.explorer.list.selectItemNamed(self.name)
        return None, None

class FSCVSFolderNode(ExplorerNodes.ExplorerNode):
    protocol = 'cvs'
    def __init__(self, name, resourcepath, clipboard, imgIdx, parent, bookmarks=None):
        ExplorerNodes.ExplorerNode.__init__(self, name, resourcepath, clipboard,
              EditorModels.CVSFolderModel.imgIdx, parent)
        self.vetoSort = true
        self.dirpos = 0
        self.upImgIdx = 7

    def destroy(self):
        self.entries = []

    def getDescription(self):
        try:
            return '%s'% (self.root)
        except AttributeError:
            return ExplorerNodes.ExplorerNode.getDescription(self)

    def getTitle(self):
        try:
            return '%s'% (self.repository)
        except AttributeError:
            return ExplorerNodes.ExplorerNode.getTitle(self)

    def isFolderish(self):
        return true

    def notifyBeginLabelEdit(self, event):
        event.Veto()

    def createParentNode(self):
        if self.parent:
            return self.parent
        else:
            parent = os.path.abspath(os.path.join(self.resourcepath, os.path.join('..', 'CVS')))
            return FSCVSFolderNode(os.path.basename(parent), parent, self.clipboard,
                      EditorModels.CVSFolderModel.imgIdx, self)

    def createChildNode(self, txtEntry):
        if not txtEntry or txtEntry == 'D':
            return None
            # XXX Maybe add all dirs?
        elif txtEntry[0] == 'D':
            return CVSFolderNode(txtEntry, self.resourcepath, self.dirpos, self)
            self.dirpos = self.dirpos + 1
        else:
            try:
                return CVSFileNode(txtEntry, self.resourcepath, self)
            except IOError:
                return None

    def openList(self):
        def readFile(self, name):
            return open(os.path.join(self.resourcepath, name)).read().strip()

        self.root = readFile(self, 'Root')
        self.repository = readFile(self, 'Repository')
        self.entries = []

        res = {}
        self.dirpos = 0
        fileEntries = self.parent.openList()
        txtEntries = open(os.path.join(self.resourcepath, 'Entries')).readlines()
        filenames = map(lambda x: x.name, fileEntries)
        missingEntries = []

        for txtEntry in txtEntries:
            cvsNode = self.createChildNode(txtEntry.strip())
            if cvsNode:
                res[cvsNode.name] = cvsNode
                if cvsNode.name not in filenames:
                    missingEntries.append(cvsNode)

        lst = []
        for entry in fileEntries:
            testCVSDir = os.path.join(entry.resourcepath, 'CVS')
            if os.path.isdir(entry.resourcepath) and \
                  os.path.exists(testCVSDir) and isCVS(testCVSDir):
                node = CVSFolderNode('D/%s////'%entry.name, self.resourcepath,
                  self.dirpos, self)
            else:
                node = res.get(entry.name, CVSUnAddedItem(entry.name, entry.resourcepath, self, entry.isFolderish()))
            if node:
                lst.append(node)

        for missing in missingEntries:
            lst.append(missing)

        self.entries = lst
        return lst

    def open(self, editor):
        return editor.openOrGotoModule(self.resourcepath)

    def openParent(self, editor):
        tree = editor.explorer.tree
        cvsParentItemParent = tree.GetItemParent(tree.GetItemParent(tree.GetSelection()))

        cvsChd = tree.getChildNamed(cvsParentItemParent, 'CVS')
        if cvsChd.IsOk():
            tree.SelectItem(cvsChd)
            return true
        else:
            return false

#---------------------------------------------------------------------------
# Register cvs dirs as a subtype of file explorers
import FileExplorer
FileExplorer.FileSysNode.subExplorerReg['folder'].append(
      (FSCVSFolderNode, isCVS, EditorHelper.imgCVSFolder)
)

ExplorerNodes.register(FSCVSFolderNode, clipboard=None, confdef=('', ''),
                       controller=CVSController)
