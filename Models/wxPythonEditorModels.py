#-----------------------------------------------------------------------------
# Name:        wxPythonEditorModels.py
# Purpose:
#
# Author:      Riaan Booysen
#
# Created:     2002/02/09
# RCS-ID:      $Id$
# Copyright:   (c) 2002 - 2005
# Licence:     GPL
#-----------------------------------------------------------------------------

print 'importing Models.wxPythonEditorModels'

import re, string, os, imp, sys, new

from wxPython import wx

import Preferences, Utils

import EditorHelper
from PythonEditorModels import ClassModel, BaseAppModel, ModuleModel
from Companions import BaseCompanions, FrameCompanions, WizardCompanions

import sourceconst

true,false=1,0

(imgAppModel, imgFrameModel, imgDialogModel, imgMiniFrameModel,
 imgMDIParentModel, imgMDIChildModel, imgPopupWindowModel,
 imgPopupTransientWindowModel, imgFramePanelModel,
 imgWizardModel, imgPyWizardPageModel, imgWizardPageSimpleModel,
) = EditorHelper.imgIdxRange(12)

class _your_frame_attrs_: pass
#    def __repr__(self):return `self.__dict__`

class BaseFrameModel(ClassModel):
    """ Base class for all frame type models that can be opened in the Designer

    This class is responsible for parsing the _init_* methods generated by the
    Designer and maintaining other special values like window id declarations
    """
    modelIdentifier = 'Frames'
    dialogLook = false
    Companion = BaseCompanions.DesignTimeCompanion
    def __init__(self, data, name, main, editor, saved, app=None):
        ClassModel.__init__(self, data, name, main, editor, saved, app)
        self.designerTool = None
        self.specialAttrs = {}

        self.defCreateClass = sourceconst.defCreateClass
        self.defClass = sourceconst.defClass
        self.defImport = sourceconst.defImport
        self.defWindowIds = sourceconst.defWindowIds
        self.defSrcVals = {}


    def renameMain(self, oldName, newName):
        """ Rename the main class of the module """
        ClassModel.renameMain(self, oldName, newName)
        if self.getModule().functions.has_key('create'):
            self.getModule().replaceFunctionBody('create',
                  ['    return %s(parent)'%newName, ''])

    def renameCtrl(self, oldName, newName):
        # Currently DesignerView maintains ctrls
        pass

    def new(self, params):
        """ Create a new frame module """
        paramLst = []
        for param in params.keys():
            paramLst.append(Preferences.cgKeywordArgFormat %{'keyword': param,
                                                        'value': params[param]})
        
        # XXX Refactor line wrappers to Utils and wrap this
        paramStr = 'self, ' + ', '.join(paramLst)

        srcValsDict = {'modelIdent': self.modelIdentifier, 
                       'main': self.main, 
                       'idNames': Utils.windowIdentifier(self.main, ''),
                       'idIdent': sourceconst.init_ctrls, 
                       'idCount': 1, 'defaultName': self.defaultName, 
                       'params': paramStr}
        srcValsDict.update(self.defSrcVals)
                       
        self.data = (sourceconst.defSig + self.defImport + \
                     self.defCreateClass + self.defWindowIds + \
                     self.defClass) % srcValsDict

        self.savedAs = false
        self.modified = true
        self.initModule()
        self.notify()

    def identifyCollectionMethods(self):
        """ Return a list of all _init_* methods in the class """
        results = []
        module = self.getModule()
        if module.classes.has_key(self.main):
            main = module.classes[self.main]
            for meth in main.methods.keys():
                if len(meth) > len('_init_') and meth[:6] == '_init_':
                    results.append(meth)
        return results

    def allObjects(self):
        views = ['Data', 'Designer']

        order = []
        objs = {}

        for view in views:
            order.extend(self.views[view].objectOrder)
            objs.update(self.views[view].objects)

        return order, objs

    def readDesignerMethod(self, meth, codeBody):
        """ Create a new ObjectCollection by parsing the given method body """
        from Views import ObjCollection
        import methodparse
        # Collection method
        if ObjCollection.isInitCollMeth(meth):
            ctrlName = methodparse.ctrlNameFromMeth(meth)
            try:
                res = Utils.split_seq(codeBody, '', string.strip)
                inits, body, fins = res[:3]
            except ValueError:
                raise 'Collection body %s not in init, body, fin form' % meth

            allInitialisers, unmatched = methodparse.parseMixedBody(\
             [methodparse.EventParse, methodparse.CollectionItemInitParse],body)

            creators = allInitialisers.get(methodparse.CollectionItemInitParse, [])
            collectionInits = []
            properties = []
            events = allInitialisers.get(methodparse.EventParse, [])

            methodparse.decorateParseItems(creators + events, ctrlName, self.main)
        # Normal method
        else:
            inits = []
            fins = []

            allInitialisers, unmatched = methodparse.parseMixedBody(\
              [methodparse.ConstructorParse, methodparse.EventParse,
               methodparse.CollectionInitParse, methodparse.PropertyParse],
               codeBody)

            creators = allInitialisers.get(methodparse.ConstructorParse, [])
            collectionInits = allInitialisers.get(methodparse.CollectionInitParse, [])
            properties = allInitialisers.get(methodparse.PropertyParse, [])
            events = allInitialisers.get(methodparse.EventParse, [])

        newObjColl = ObjCollection.ObjectCollection()
        newObjColl.setup(creators, properties, events, collectionInits, inits, fins)

        if unmatched:
            wx.wxLogWarning('The following lines were not used by the Designer '\
                         'and will be lost:\n')
            for line in unmatched:
                wx.wxLogWarning(line)
            wx.wxLogWarning('\nThere were unprocessed lines in the source code of '\
                         'method: %s\nIf this was unexpected, it is advised '\
                         'that you cancel this Designer session and correct '\
                         'the problem before continuing.'%meth)

        return newObjColl

    def readSpecialAttrs(self, mod, cls):
        """ Read special attributes from __init__ method.

        All instance attributes defined between the top of the __init__ method
        and the _init_ctrls() method call will be available to the Designer
        as valid names bound to properties.

        For an attribute to qualify, it has to have a simple deduceable type;
        Python builtin or wxPython objects.
        If for example the attribute is bound to a variable passed in as a
        parameter, you have to first initialise it to a literal of the same
        type. This value will be used at design time.

        e.g.    def __init__(self, parent, myFrameCaption):
                    self.frameCaption = 'Design time frame caption'
                    self.frameCaption = myFrameCaption
                    self._init_ctrls(parent)

        Now you may add this attribute as a parameter or property value
        in the source by hand.

        In the Inspector property values recognised as special attributes
        will display as bold values and cannot be edited (yet).
        """
        initMeth = cls.methods['__init__']
        # determine end of attrs and possible external attrs init
        startline = initMeth.start
        extAttrInitLine = -1
        extAttrInitName = ''
        for idx in range(startline, initMeth.end):
            line = mod.source[idx].strip()
            if line.startswith('self._init_ctrls('):
                endline = idx
                break
            elif line.find('_AttrMixin.__init__(self') != -1:
                extAttrInitLine = idx
                extAttrInitName = line.split('.__init__')[0]
        else:
            raise 'self._init_ctrls not found in __init__'

        # build list of attrs
        attrs = []

        def readAttrsFromSrc(attrs, attributes, source, startline, endline):
            for attr, blocks in attributes.items():
                for block in blocks:
                    if startline <= block.start <= endline and attr not in attrs:
                        linePos = block.start-1
                        line = source[linePos]
                        val = line[line.find('=')+1:].strip()
                        # handle lines continued with ,
                        while val.endswith(','):
                            linePos += 1
                            val += source[linePos].strip()

                        attrs.append( (attr, val) )
                            

        if extAttrInitName:
            if not mod.from_imports_names.has_key(extAttrInitName):
                raise '%s.__init__ called, but not imported in the form: '\
                      'from [ModuleName] import %s'%(extAttrInitName, extAttrInitName)
            # try to load external attrs
            extModName = mod.from_imports_names[extAttrInitName]
            extModFilename = os.path.join(os.path.dirname(self.filename),
                                          extModName+'.py')
            from Explorers.Explorer import openEx
            try:
                data = openEx(extModFilename).load()
            except Exception, error:
                raise 'Problem loading %s: File expected at: %s'%(extModName,
                                                                 extModFilename)
            exModModel = ModuleModel(data, extModFilename, self.editor, 1)
            extModule = exModModel.getModule()
            extClass = extModule.classes[extAttrInitName]
            extMeth = extClass.methods['__init__']

            readAttrsFromSrc(attrs, extClass.attributes, extModule.source,
                  extMeth.start, extMeth.end)

        readAttrsFromSrc(attrs, cls.attributes, mod.source, startline, endline)

        import PaletteMapping
        # build a dictionary that can be passed to eval
        evalNS = _your_frame_attrs_()
        for attr, code in attrs:
            if hasattr(evalNS, attr):
                continue
            try:
                val = PaletteMapping.evalCtrl(code)
            except Exception, err:
                print str(err)
                continue
            else:
                setattr(evalNS, attr, val)
        return {'self': evalNS}

    def readCustomClasses(self, mod, cls):
        """ Read definition for Custom Classes

        Custom Classes can be defined as a class attribute named _custom_classes
        containing a dictionary defining wxPython classes and their custom
        equivalents, e.g.
        _custom_classes = {'wxTreeCtrl': ['MyTreeCtrl', 'AdvancedTreeCtrl']}

        These custom classes will then be available to the Designer
        and will act as equivalent to the corresponding wxPython class,
        but will generate source for the custom definition.

        One implication is that you loose the constructor. Because Boa
        will generate the creation code for the object, the constructor
        signature has to be the same as the wxPython class.
        """
        res = {}
        if cls.class_attributes.has_key('_custom_classes'):
            try:
                import PaletteMapping
                cls_attr = cls.class_attributes['_custom_classes'][0]
                attr_val = cls_attr.signature
                srcline = cls_attr.start

                # multiline parser ;)
                while 1:
                    try:
                        custClasses = PaletteMapping.evalCtrl(attr_val)
                        assert type(custClasses) == type({})
                        break
                    except SyntaxError, err:
                        if err[0] == 'unexpected EOF while parsing':
                            attr_val = attr_val + mod.source[srcline].strip()
                            srcline = srcline + 1
                        else:
                            raise
            except Exception, err:
                raise '_custom_classes is not valid: '+str(err)

            for wxClassName, customs in custClasses.items():
                wxClass = PaletteMapping.evalCtrl(wxClassName)
                res[wxClassName] = wxClass
                for custom in customs:
                    res[custom] = wxClass
        return res

    def readComponents(self):
        """ Setup object collection dict by parsing all designer controlled methods """
        module = self.getModule()
        # Parse all _init_* methods
        self.objectCollections = {}
        if module.classes.has_key(self.main):
            main = module.classes[self.main]

            self.specialAttrs = self.readSpecialAttrs(module, main)
            self.customClasses = self.readCustomClasses(module, main)
            self.resources = self.readResources(module, main, 
                  specialAttrs=self.specialAttrs)

            for oc in self.identifyCollectionMethods():
                codeSpan = main.methods[oc]
                codeBody = module.source[codeSpan.start : codeSpan.end]

                self.objectCollections[oc] = self.readDesignerMethod(oc, codeBody)

                # XXX Hack: This should not be necessary !!
                for prop in self.objectCollections[oc].properties[:]:
                    if prop.asText() in ('self.%s()'%sourceconst.init_utils, 
                                         'self.%s()'%sourceconst.init_sizers):
                        self.objectCollections[oc].properties.remove(prop)

            # Set the model's constructor
            if self.objectCollections.has_key(sourceconst.init_ctrls):
                try:
                    self.mainConstr = \
                      self.objectCollections[sourceconst.init_ctrls].creators[0]
                except IndexError:
                    raise 'Inherited __init__ method missing'
        else:
            raise 'Main class "%s" not found. Please fix file header or class name.'%self.main

    def removeWindowIds(self, colMeth):
        """ Remove a method's corresponding window ids from the source code """
        # find windowids in source
        winIdIdx = -1
        reWinIds = re.compile(sourceconst.srchWindowIds % colMeth)
        module = self.getModule()
        for idx in range(len(module.source)):
            match = reWinIds.match(module.source[idx])
            if match:
                # XX always 2 lines? check this
                del module.source[idx]
                del module.source[idx]
                module.renumber(-2, idx)
                break

    def writeWindowIds(self, colMeth, companions):
        """ Write a method's corresponding window ids to the source code """
        # To integrate efficiently with Designer.SaveCtrls this method
        # modifies module.source but doesn't refresh anything

        # find windowids in source
        winIdIdx = -1
        winIdLen = 2
        reWinIds = re.compile(sourceconst.srchWindowIdsCont % colMeth)
        module = self.getModule()
        for idx in range(len(module.source)):
            line = module.source[idx]
            match = reWinIds.match(line)
            if match:
                startLine = line
                startIdx = idx
                while startIdx > 0 and startLine[0] != '[':
                    startIdx = startIdx - 1
                    startLine = module.source[startIdx]

                winIdIdx = startIdx
                winIdLen = idx - startIdx + 2
                break

        # build window id list
        lst = []
        for comp in companions:
            if winIdIdx == -1:
                comp.updateWindowIds()
            comp.addIds(lst)
        lst.sort()

        if lst:
            lines = []
            if len(lst) > 1 and Preferences.cgWrapLines:
                # build win ids spanning multiple lines
                line = '['+lst[0]+', '
                for seg in lst[1:]:
                    newLine = line+seg +', '
                    if len(newLine) >= Preferences.cgLineWrapWidth:
                        lines.append(line)
                        line = ' '+seg+', '
                    else:
                        line = newLine
                lines.append(line)
                lines.append((sourceconst.defWindowIdsCont %
                      {'idIdent': colMeth, 'idCount': len(lst)}).strip())
            else:
                lines.append((sourceconst.defWindowIds % {
                    'idNames': ', '.join(lst), 'idIdent': colMeth,
                    'idCount': len(lst)}).strip())
            lines.append('')

            if winIdIdx == -1:
                # No window id definitions could be found add one above class def
                insPt = module.classes[self.main].block.start - 1
                module.source[insPt:insPt] = lines
                module.renumber(len(lines), insPt)
            else:
                module.source[winIdIdx:winIdIdx + winIdLen] = lines
                module.renumber(len(lines)-winIdLen, winIdIdx)

    def update(self):
        ClassModel.update(self)

    def getSimpleRunnerSrc(self):
        """ Return template of source code that will run this module type as
        a stand-alone file """
        return sourceconst.simpleAppFrameRunSrc


class FrameModel(BaseFrameModel):
    modelIdentifier = 'Frame'
    defaultName = 'wx.Frame'
    bitmap = 'wx.Frame.png'
    imgIdx = imgFrameModel
    Companion = FrameCompanions.FrameDTC

class DialogModel(BaseFrameModel):
    modelIdentifier = 'Dialog'
    defaultName = 'wx.Dialog'
    bitmap = 'wx.Dialog.png'
    imgIdx = imgDialogModel
    dialogLook = true
    Companion = FrameCompanions.DialogDTC

    def getSimpleRunnerSrc(self):
        return sourceconst.simpleAppDialogRunSrc

class MiniFrameModel(BaseFrameModel):
    modelIdentifier = 'MiniFrame'
    defaultName = 'wx.MiniFrame'
    bitmap = 'wx.MiniFrame.png'
    imgIdx = imgMiniFrameModel
    Companion = FrameCompanions.MiniFrameDTC

class MDIParentModel(BaseFrameModel):
    modelIdentifier = 'MDIParent'
    defaultName = 'wx.MDIParentFrame'
    bitmap = 'wx.MDIParentFrame.png'
    imgIdx = imgMDIParentModel
    Companion = FrameCompanions.MDIParentFrameDTC

class MDIChildModel(BaseFrameModel):
    modelIdentifier = 'MDIChild'
    defaultName = 'wx.MDIChildFrame'
    bitmap = 'wx.MDIChildFrame.png'
    imgIdx = imgMDIChildModel
    dialogLook = true
    Companion = FrameCompanions.MDIChildFrameDTC

class PopupWindowModel(BaseFrameModel):
    modelIdentifier = 'PopupWindow'
    defaultName = 'wx.PopupWindow'
    bitmap = 'wx.PopupWindow.png'
    imgIdx = imgPopupWindowModel
    dialogLook = true
    Companion = FrameCompanions.PopupWindowDTC

    def getSimpleRunnerSrc(self):
        return sourceconst.simpleAppPopupRunSrc

class PopupTransientWindowModel(BaseFrameModel):
    modelIdentifier = 'PopupTransientWindow'
    defaultName = 'wx.PopupTransientWindow'
    bitmap = 'wx.PopupTransientWindow.png'
    imgIdx = imgPopupTransientWindowModel
    dialogLook = true
    Companion = FrameCompanions.PopupWindowDTC

    def getSimpleRunnerSrc(self):
        return sourceconst.simpleAppPopupRunSrc

class AppModel(BaseAppModel):
    modelIdentifier = 'App'
    defaultName = 'wx.App'
    bitmap = 'wx.App.png'
    imgIdx = imgAppModel

    def renameMain(self, oldName, newName):
        BaseAppModel.renameMain(self, oldName, newName)
        self.getModule().replaceFunctionBody('main',
          ['    application = %s(0)'%newName, '    application.MainLoop()', ''])

    def new(self, mainModule):
        self.data = (sourceconst.defEnvPython + sourceconst.defSig + \
              sourceconst.defImport + sourceconst.defApp) % {
                'modelIdent': self.modelIdentifier,
                'main': sourceconst.boaClass,
                'mainModule': mainModule}
        self.saved = false
        self.modified = true
        self.update()
        self.notify()

class FramePanelModel(BaseFrameModel):
    modelIdentifier = 'FramePanel'
    defaultName = 'wx.Panel'
    bitmap = 'wx.FramePanel.png'
    imgIdx = imgFramePanelModel
    dialogLook = true
    Companion = FrameCompanions.FramePanelDTC

    def __init__(self, data, name, main, editor, saved, app=None):
        BaseFrameModel.__init__(self, data, name, main, editor, saved, app)

        self.defCreateClass = ''
        # can this be any uglier (or shorter ;) ?
        self.defClass = sourceconst.defClass.replace('parent',
              'parent, id, pos, size, style, name', 1)

    def getSimpleRunnerSrc(self):
        return ''

sourceconst.defWizardImport = sourceconst.wsfix('\nimport wx.wizard\n')

class WizardModel(DialogModel):
    modelIdentifier = 'Wizard'
    defaultName = 'wx.Wizard'
    bitmap = 'wx.wizard.Wizard.png'
    imgIdx = imgWizardModel
    dialogLook = true
    Companion = WizardCompanions.WizardDTC

    def __init__(self, data, name, main, editor, saved, app=None):
        DialogModel.__init__(self, data, name, main, editor, saved, app)
        self.defImport = sourceconst.defImport.strip()+sourceconst.defWizardImport
        
    def getSimpleRunnerSrc(self):
        return ''

sourceconst.defPyWizPageClass = sourceconst.defClass+sourceconst.wsfix('''
\tdef GetNext(self):
\t\treturn None

\tdef GetPrev(self):
\t\treturn None
''')


class PyWizardPageModel(FramePanelModel):
    modelIdentifier = 'PyWizardPage'
    defaultName = 'wx.PyWizardPage'
    bitmap = 'wx.wizard.PyWizardPage.png'
    imgIdx = imgPyWizardPageModel
    dialogLook = true
    Companion = WizardCompanions.PyWizardPageDTC

    def __init__(self, data, name, main, editor, saved, app=None):
        FramePanelModel.__init__(self, data, name, main, editor, saved, app)
        self.defClass = sourceconst.defPyWizPageClass
        self.defImport = sourceconst.defImport.strip()+sourceconst.defWizardImport
        self.defWindowIds = ''

    def getSimpleRunnerSrc(self):
        return ''

class WizardPageSimpleModel(FramePanelModel):
    modelIdentifier = 'WizardPageSimple'
    defaultName = 'wx.WizardPageSimple'
    bitmap = 'wx.wizard.WizardPageSimple.png'
    imgIdx = imgWizardPageSimpleModel
    dialogLook = true
    Companion = WizardCompanions.WizardPageSimpleDTC

    def __init__(self, data, name, main, editor, saved, app=None):
        FramePanelModel.__init__(self, data, name, main, editor, saved, app)
        self.defClass = sourceconst.defClass
        self.defImport = sourceconst.defImport.strip()+sourceconst.defWizardImport
        self.defWindowIds = ''
        
    def getSimpleRunnerSrc(self):
        return ''

#-------------------------------------------------------------------------------
# model registry: add to this dict to register a Model (needed for explorer images)
EditorHelper.modelReg.update({
      AppModel.modelIdentifier: AppModel,
      FrameModel.modelIdentifier: FrameModel,
      DialogModel.modelIdentifier: DialogModel,
      MiniFrameModel.modelIdentifier: MiniFrameModel,
      MDIParentModel.modelIdentifier: MDIParentModel,
      MDIChildModel.modelIdentifier: MDIChildModel,
      PopupWindowModel.modelIdentifier: PopupWindowModel,
      PopupTransientWindowModel.modelIdentifier: PopupTransientWindowModel,
      FramePanelModel.modelIdentifier: FramePanelModel,
      WizardModel.modelIdentifier: WizardModel,
      PyWizardPageModel.modelIdentifier: PyWizardPageModel,
      WizardPageSimpleModel.modelIdentifier: WizardPageSimpleModel,
})
