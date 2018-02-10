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

# this script allows auto importing of new VO files, creating associated events.
# It asks the user for an input folder (audio to import)
# It responds to an object selected callback from WAAPI
# It creates a list of exisiting sound objects underneath the selected import parent
# It imports any NEW audio files, leaving exisiting structures intact
# It also creates events for any new audio files imported


#args for audio import
    ImportAudioFilePath = ""
    ImportAudioFileList = []

    WwiseQueryResults = []
    ExistingWwiseAudio = []

#Input variables. TO DO: Drive these from data e.g Reaper
    INPUT_ObjectType = "Sound"
    INPUT_ObjectName = ""
    OPTION_CreateEvent = False
    OPTION_IsStreaming = True


    INPUT_ImportLanguage = "English(US)" #Default language for Wwise projects, Or SFX
    INPUT_originalsPath = "WAAPI/TestImports"  ##TODO Variable this based on import language/SFX



#store a ref to the selected parent object
    parentObject = None
    parentObjectPath = ""

#flow control
    parentSelected = False
    objectCreated = False
    eventCreated = False

#dic to store return/results from yield calls
    Results = {}

    ImportOperationSuccess = False

# Internal Variables for object creation
    objParID = "None"
    objParentName = ""
    objType = ""
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
    eventAlreadyExists = None

#args dict for event creation
    createEventArgs = {}
#args for importing
    importArgs = {}

    def printThis(self,msg):
        print(msg)

    def onJoin(self, details):

        def beginUndoGroup():
            self.call(WAAPI_URI.ak_wwise_core_undo_begingroup)

        def cancelUndoGroup():
            self.call(WAAPI_URI.ak_wwise_core_undo_cancelgroup)

        def endUndoGroup():
            undoArgs = {"displayName": "Script Auto Importer"}
            self.call(WAAPI_URI.ak_wwise_core_undo_endgroup, {}, **undoArgs)

        cancelUndoGroup()
        beginUndoGroup()

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
            MyComponent.ImportAudioFilePath = tkFileDialog.askdirectory()
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

        def getExistingAudioInWwise(object):
            #print("Get a list of the audio files currently in the project, under the selected object")
            arguments = {
                "from": {"id": [object]},
                "transform":[
                    {"select":["descendants"]},
                ],
                "options": {
                    "return": ["type", "name", "path"]
                }
            }
            try:
                res = yield From(self.call(WAAPI_URI.ak_wwise_core_object_get, **arguments))
            except Exception as ex:
                print("call error: {}".format(ex))
            else:
                MyComponent.WwiseQueryResults = res.kwresults["return"]


        def createExistingAudioList(WwiseQueryResults):
            #print("creating a list of existing wwise sounds")
            list = []
            for i in WwiseQueryResults:
                #print(i)
                if i["type"] == "Sound":
                    #print(i)
                    soundName = str(i["name"])
                    list.append(soundName)
            MyComponent.ExistingWwiseAudio = list


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
                    MyComponent.parentObjectPath = str(MyComponent.parentObject["path"])
                    MyComponent.eventWorkUnit = str(MyComponent.parentObject["workunit"]["name"])
                    #print("Selected object name is...{}".format(MyComponent.parentObject[u"name"]))
                    parID = str(MyComponent.parentObject["id"])
                    MyComponent.objParentName = str(MyComponent.parentObject[u"name"])
                    MyComponent.parentSelected = True

                if success:
                    yield getExistingAudioInWwise(str(parID))
                    yield createExistingAudioList(MyComponent.WwiseQueryResults)
                    yield setupAudioFilePath()
                    count = 0
                    for file in MyComponent.ImportAudioFileList:
                        #print(file)
                        f = file.rsplit('.')
                        fname = os.path.basename(f[0])
                        if not fname in MyComponent.ExistingWwiseAudio:
                            yield setupImportArgs(parID, file, MyComponent.INPUT_originalsPath)
                            yield importAudioFiles(MyComponent.importArgs)
                            count += 1
                    MyComponent.ImportOperationSuccess = True

                else:
                    print("Something went wrong!!")
                    MyComponent.ImportOperationSuccess = False
                    return

                if (MyComponent.ImportOperationSuccess):
                    saveWwiseProject()
                    endUndoGroup()
                    print("Import operation success. "+str(count)+" new files imported.")
                else:
                    print("Import operation failed! Check log for errors!")
                    endUndoGroup()

                self.leave()

        def saveWwiseProject():
            self.call(WAAPI_URI.ak_wwise_core_project_save)


        def setupAudioFilePath():
            #print("Setting up audio file path")
            pathToFiles = os.path.expanduser(MyComponent.ImportAudioFilePath)
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
            MyComponent.ImportAudioFileList = filelist

        def setupImportArgs(parentID, fileList,originalsPath):
            #print ("Args for audio importing")
            ParentID = str(parentID)
            importFilelist = []
            #for audiofile in fileList:
            foo = fileList.rsplit('.') #remove extension from filename
            audiofilename = foo[0]

            ### Need an extra param in this function to set the originals location for the imported file. Needs to maintain the subfolders after the Main Path
            str_InputFilePath = str(MyComponent.ImportAudioFilePath).replace('\\', '/')
            str_AudioFileName = str(audiofilename).replace('\\','/')
            originalsSubDir = str_AudioFileName.replace(str_InputFilePath,'')

            # Just get the directory name from the audio file path
            originalsSubDir = os.path.dirname(originalsSubDir)
            if originalsSubDir == "/":
                originalsSubDir = ""

            baseDirName = os.path.basename(originalsSubDir)

            eventPath = MyComponent.parentObjectPath.replace("Actor-Mixer Hierarchy", "Events")
            #print(eventPath)

            objectType = "<Sound Voice>"

            # "\\Actor-Mixer Hierarchy\\Script Import\\<Actor-Mixer>Test 0\\<Sequence Container>Container 0\\<Sound SFX>My SFX 0"
            if baseDirName:
                objectPath = "<Actor-Mixer>"+baseDirName+"\\"
            else:
                objectPath = ""

            sectionActorMixer = "<Actor-Mixer>" + MyComponent.INPUT_SectionName + "\\"

            importFilelist.append(
                {
                    "audioFile": fileList,
                    #"objectPath": "<Sound SFX>"+os.path.basename(audiofilename
                    "objectPath": sectionActorMixer + objectPath + objectType + os.path.basename(audiofilename)
                    #"objectPath": "<Sound Voice>" + os.path.basename(audiofilename)
                }
            )
            MyComponent.importArgs = {
                "importOperation": "useExisting",
                "default": {
                    "importLanguage": MyComponent.INPUT_ImportLanguage,
                    "importLocation": ParentID,
                    "originalsSubFolder": originalsPath+originalsSubDir,
                    "notes":"This object was auto imported",
                    "@IsStreamingEnabled": MyComponent.OPTION_IsStreaming,
                    "@IsZeroLantency": MyComponent.OPTION_IsStreaming,
                    "event": eventPath+"\\"+os.path.basename(audiofilename)+"@Play" #"\\Events\\"+MyComponent.eventWorkUnit+"\\"+os.path.basename(audiofilename)
                    #,"ErrorTest":"Failme"
                    },
                "imports": importFilelist
                }

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
            else:
                MyComponent.Results = x


        def importAudioFiles(args):
            try:
                yield self.call(WAAPI_URI.ak_wwise_core_audio_import, {}, **args)
            except Exception as ex:
                print("call error: {}".format(ex))
                MyComponent.ImportOperationSuccess = False
            else:
                MyComponent.ImportOperationSuccess = True

        def deleteWwiseObject(object):
            args = {"object":object}
            try:
                yield self.call(WAAPI_URI.ak_wwise_core_object_delete, {}, **args)
            except Exception as ex:
                print("call error: {}".format(ex))

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
                    #for returnObj in returnObjs:
                        #print("\t{}".format(returnObj[u"type"]))
                        #print("Created object name is...{}".format(returnObj[u"name"]))
                        #print("%s object type is...%s." % (returnObj[u"name"], returnObj[u"type"]))
                        #print("%s object path is...%s." % (returnObj[u"name"], returnObj["path"]))

        def setupBatchFileSysArgs():
            print("Import language is "+sys.argv[1])  # Import Language
            MyComponent.INPUT_ImportLanguage = str(sys.argv[1])
            print("Streaming = "+ str(bool(sys.argv[2])))
            MyComponent.OPTION_IsStreaming = bool(sys.argv[2])
            # print("This is the name of the script", sys.argv[0])
            # print("This is the number of arguments", len(sys.argv))
            # print("The arguments are...", str(sys.argv))

        if (len(sys.argv) > 1):     #If the sys args are longer than the default 1 (script name)
            setupBatchFileSysArgs()

        askUserForImportDirectory()

        if MyComponent.ImportAudioFilePath == '':
            print("Error. Directory not selected. Exiting application.")
            self.leave()
            return

        setupSubscriptions()





        print("This script will auto create wwise objects and events...")
        print("...Select an object to be the parent in the Project Explorer")





    def onDisconnect(self):
        print("The client was disconnected.")

        asyncio.get_event_loop().stop()


if __name__ == '__main__':
    runner = ApplicationRunner(url=u"ws://127.0.0.1:8095/waapi", realm=u"realm1")
    try:
        runner.run(MyComponent)
    except Exception as e:
        print(type(e).__name__ + ": Is Wwise running and Wwise Authoring API enabled?")
