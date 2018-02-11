import os
import sys

import trollius as asyncio
from trollius import From

import Tkinter #import Tk
import tkFileDialog

import fnmatch

from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from ak_autobahn import AkComponent


# You may also copy-paste the waapi.py file alongside this sample
sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../include/AK/WwiseAuthoringAPI/py'))
from waapi import WAAPI_URI

class MyComponent(AkComponent):

# this script allows creation of Wwise objects and events
# Selecting a parent object in wwise triggers a callback that
# creates the desired object type underneath the selected parent
# Optionally, it is possible to create an event at the same time
# that Plays the recently created object....

#store a ref to the selected parent object
    parentObject = None

#flow control
    parentSelected = False
    objectCreated = False
    eventCreated = False

#dic to store return/results from yield calls
    Results = {}

#Variables for object creation
    objParID = "None"
    objParentName = ""
    objType = "BlendContainer"
    objName = "MyCreatedObject"
    nameConflict = "rename"
    objNotes = "This object was auto created...."

#args dict for object creation For use with create object call
    createObjArgs = {}
    ObjPropertyArgs = {}

#variables for event creation
    eventParent = "\\Events\\"
    eventParentVO = "\\Events\\Greybox_Dialogue_DEV\\Greybox_Dialogue_DEV\\"     ##TODO Make this into batch variable
    eventWorkUnit = "Name"
    eventName = ""
    eventTarget = ""
    evActionType = 1

#args dict for event creation
    createEventArgs = {}

#args for audio import
    INPUT_audioFilePath = "~/Projects/Wwise/WAAPI/AudioFiles"
    INPUT_audioFileList = []
    INPUT_originalsPath = "WAAPI/TestImports"                       ##TODO Variable this based on import language/SFX

    importArgs = {}

#Input variables. TO DO: Drive these from data e.g Reaper
    INPUT_ObjectType = "Sound"
    INPUT_ObjectName = ""
    OPTION_CreateEvent = True
    #INPUT_ImportLanguage = "SFX"
    INPUT_ImportLanguage = "English(US)"

    def printThis(self,msg):
        print(msg)

    def onJoin(self, details):

        def beginUndoGroup():
            self.call(WAAPI_URI.ak_wwise_core_undo_cancelgroup)
            self.call(WAAPI_URI.ak_wwise_core_undo_begingroup)

        yield beginUndoGroup()

        try:
            res = yield From(self.call(WAAPI_URI.ak_wwise_core_getinfo))  # RPC call without arguments
        except Exception as ex:
            print("call error: {}".format(ex))
        else:
            # Call was successful, displaying information from the payload.
            print("Hello {} {}".format(res.kwresults['displayName'], res.kwresults['version']['displayName']))

        #MyComponent.printThis(self,"Test")

        def askUserForImportDirectory():

            root = Tkinter.Tk()
            root.withdraw()
            root.update()
            MyComponent.INPUT_audioFilePath = tkFileDialog.askdirectory()
            root.update()
            root.destroy()
            #print(MyComponent.INPUT_audioFilePath)

        def setupSubscriptions():
            # Subscribe to ak.wwise.core.object.created
            # Calls on_object_created whenever the event is received
            self.subscribe(onParentSelected, WAAPI_URI.ak_wwise_ui_selectionchanged)

            objCreateSubArgs = {
                "options": {
                    "return": ["type", "name", "category", "id", "path"]
                }
            }
            self.subscribe(onObjectCreated, WAAPI_URI.ak_wwise_core_object_created, **objCreateSubArgs)

        def ResetGates():
            MyComponent.parentSelected = False
            MyComponent.objectCreated = False
            MyComponent.eventCreated = False

        def onParentSelected():
            # subscribe to selection change?
            if not MyComponent.parentSelected:

                #print("Method to get the parent to create new object under")
                success = False
                parID = None
                yield getSelectedObject()
                #print("Selected object is...")

                if MyComponent.Results != None:
                    success = True
                    #print(MyComponent.Results.kwresults['objects'])
                    obj = MyComponent.Results.kwresults['objects']
                    # print(obj[0]['id'])
                    MyComponent.parentObject = obj[0]
                    MyComponent.eventWorkUnit = str(MyComponent.parentObject["workunit"]["name"])
                    print("Selected object name is...{}".format(MyComponent.parentObject[u"name"]))
                    parID = str(MyComponent.parentObject["id"])
                    MyComponent.objParentName = str(MyComponent.parentObject[u"name"])
                    MyComponent.parentSelected = True

                yield setupAudioFilePath()


                if success:
                    for file in MyComponent.INPUT_audioFileList:
                        print(file)
                        f = file.rsplit('.')
                        fname = os.path.basename(f[0])
                        wwiseObjType = MyComponent.INPUT_ObjectType
                        setupCreateArgs(parID, wwiseObjType, fname)  # include optional arguments for type/name/conflict
                        yield createWwiseObject(MyComponent.createObjArgs)
                        #print(MyComponent.Results)
                        MyComponent.objectCreated = True

                        CreatedObjectID = MyComponent.Results.kwresults['id']

                        #setupObjPropertyArgs(CreatedObjectID, "IsVoice", True)
                        #yield SetWwiseObjectProperty(MyComponent.ObjPropertyArgs)  #Set a specific propety on the created object

                        yield setupImportArgs(CreatedObjectID, file, MyComponent.INPUT_originalsPath)
                        yield importAudioFiles(MyComponent.importArgs)

                        # Setup an event to play the created object
                        if MyComponent.OPTION_CreateEvent:
                            evName = MyComponent.Results.kwresults["name"]
                            evTarget = str(MyComponent.Results.kwresults["id"])
                            setupEventArgs(evName, evTarget)
                            yield createWwiseObject(MyComponent.createEventArgs)
                           # print(MyComponent.Results)
                            MyComponent.eventCreated = True




                else:
                    print("Something went wrong!!")
                    return

                saveWwiseProject()

                endUndoGroup()

                self.leave()

        def saveWwiseProject():
            self.call(WAAPI_URI.ak_wwise_core_project_save)

        def endUndoGroup():

            undoArgs = {
                "displayName": "Script Auto Importer"
            }

            self.call(WAAPI_URI.ak_wwise_core_undo_endgroup, {}, **undoArgs)


        def setupEventArgs(oname,otarget,oactionType = 1):
            #print("setting up event")

            MyComponent.eventName = oname
            MyComponent.eventTarget = otarget
            MyComponent.evActionType = oactionType

            MyComponent.createEventArgs = {

                "parent": MyComponent.eventParent+MyComponent.eventWorkUnit,
                "type": "Folder",
                "name": MyComponent.objParentName,
                "onNameConflict": "merge",
                "children": [
                    {
                        "type": "Event",
                        "name": "Play_" + MyComponent.eventName,
                        "children": [
                            {
                                "name": "",
                                "type": "Action",
                                "@ActionType": MyComponent.evActionType,
                                "@Target": MyComponent.eventTarget
                            }
                        ]
                    }
                ]
            }

        def setupCreateArgs(parentID ,otype = "Sound",  oname = "" , conflict = "replace"):
            #check the inputs
            if otype == "":
                MyComponent.objType = "BlendContainer"
                print("Defaulting type to Blend Container")
            else:
                MyComponent.objType = otype
            if oname == "":
                MyComponent.objName = "AutoCreatedObject"
                print("Defaulting name to AutoCreatedObject")
            else:
                MyComponent.objName = oname


            MyComponent.objParID = parentID
            MyComponent.nameConflict = conflict

            MyComponent.createObjArgs = {

                "parent": MyComponent.objParID,
                "type": MyComponent.objType,
                "name": MyComponent.objName,
                "onNameConflict": MyComponent.nameConflict,
                "notes": MyComponent.objNotes,
                "@IsVoice":True
            }

        def setupObjPropertyArgs(parentID ,oproperty = "",  ovalue = ""):

            MyComponent.ObjPropertyArgs = {

                "object": parentID,
                "property": oproperty,
                "value": ovalue
            }


        def setupAudioFilePath():
            #print("Setting up audio file path")
            pathToFiles = os.path.expanduser(MyComponent.INPUT_audioFilePath)
            setupAudioFileList(pathToFiles)

        def setupAudioFileList(path):
            #print("Setting up list of audio files")
            filelist = []
            pattern='*.wav'

            for root, dirs, files in os.walk(path):
            #for file in os.listdir(path):
                for filename in fnmatch.filter(files, pattern):
                    absFilePath = os.path.abspath(os.path.join(root,filename))
                    filelist.append(absFilePath)

            MyComponent.INPUT_audioFileList = filelist

        def setupImportArgs(parentID, fileList,originalsPath):
            #print ("Args for audio importing")
            ParentID = str(parentID)
            importFilelist = []
            #for audiofile in fileList:
            foo = fileList.rsplit('.') #remove extension from filename
            audiofilename = foo[0]

            ### Need an extra param in this function to set the originals location for the imported file. Needs to maintain the subfolders after the Main Path
            str_InputFilePath = str(MyComponent.INPUT_audioFilePath).replace('\\','/')
            str_AudioFileName = str(audiofilename).replace('\\','/')
            originalsSubDir = str_AudioFileName.replace(str_InputFilePath,'')

            # Just get the directory name from the audio file path
            originalsSubDir = os.path.dirname(originalsSubDir)
            if originalsSubDir == "/":
                originalsSubDir = ""

            importFilelist.append(
                {
                    "audioFile": fileList,
                    #"objectPath": "<Sound SFX>"+os.path.basename(audiofilename
                    "objectPath": "<Sound Voice>" + os.path.basename(audiofilename)
                }
            )

            MyComponent.importArgs = {
                "importOperation": "replaceExisting",
                "default": {
                    "importLanguage": MyComponent.INPUT_ImportLanguage,
                    "importLocation": ParentID,
                    "originalsSubFolder": originalsPath+originalsSubDir
                    },
                "imports": importFilelist

                }
            print (MyComponent.importArgs)

        def getSelectedObject():
            selectedObjectArgs = {
                "options": {
                    "return": ["workunit", "name", "parent", "id", "path","@IsVoice","type"]
                }
            }
            try:
                x = yield self.call(WAAPI_URI.ak_wwise_ui_getselectedobjects, {}, **selectedObjectArgs)
            except Exception as ex:
                print("call error: {}".format(ex))
            #print (x)
            MyComponent.Results = x

        def createWwiseObject(args):
            try:
                res = yield self.call(WAAPI_URI.ak_wwise_core_object_create, {}, **args)
            except Exception as ex:
                print("call error: {}".format(ex))
            MyComponent.Results = res

        def SetWwiseObjectProperty(args):
            try:
                res = yield self.call(WAAPI_URI.ak_wwise_core_object_setproperty, {}, **args)
            except Exception as ex:
                print("call error: {}".format(ex))
            MyComponent.Results = res

        def importAudioFiles(args):
            try:
                yield self.call(WAAPI_URI.ak_wwise_core_audio_import, {}, **args)
            except Exception as ex:
                print("call error: {}".format(ex))
            #MyComponent.Results = res

        def onObjectCreated(**kwargs):
            if not MyComponent.eventCreated:
                #print("Object was created")
                #print(kwargs)
                ob = kwargs["object"]
                obID = ob["id"]
                arguments = {
                    "from": {"id": [obID]},
                    "options": {
                        "return": ["type", "name", "category","id","path"]
                    }
                }
                try:
                    res2 = yield From(self.call(WAAPI_URI.ak_wwise_core_object_get, **arguments))
                except Exception as ex:
                    print("call error: {}".format(ex))
                else:
                    #print(res2.kwresults)
                    returnObjs = res2.kwresults[u"return"]
                    for returnObj in returnObjs:
                        #       print("\t{}".format(returnObj[u"type"]))
                        print("Created object name is...{}".format(returnObj[u"name"]))
                        print("%s object type is...%s." % (returnObj[u"name"], returnObj[u"type"]))
                        print("%s object path is...%s." % (returnObj[u"name"], returnObj["path"]))

        askUserForImportDirectory()

        setupSubscriptions()

        #print("This is the name of the script", sys.argv[0])
       # print("This is the number of arguments", len(sys.argv))
        #print("The arguments are...", str(sys.argv))



        print("This script will auto create wwise objects and events...")
        print("...Select an object to be the parent in the Project Explorer")





    def onDisconnect(self):
        print("The client was disconnected.")

        asyncio.get_event_loop().stop()


if __name__ == '__main__':
    runner = ApplicationRunner(url=u"ws://127.0.0.1:8080/waapi", realm=u"realm1")
    try:
        runner.run(MyComponent)
    except Exception as e:
        print(type(e).__name__ + ": Is Wwise running and Wwise Authoring API enabled?")
