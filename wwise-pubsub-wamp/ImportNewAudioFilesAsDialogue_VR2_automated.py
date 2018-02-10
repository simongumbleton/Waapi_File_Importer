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
    ImportAudioFilePath = ""    #full path to root folder for files to import

    INPUT_SectionName = "ArtGalleryMission"      #the section name, from BAT file. Use to find actor mixer and events parent for importing

    ImportLanguage = "English(UK)" #Default language for Wwise projects, Or SFX

    pathToOriginalsFromProjectRoot = ["Originals","Voices",ImportLanguage]

    stepsUpToCommonDirectory = 2

    DirOfWwiseProjectRoot = ["Wwise_Project","WAAPI_Test"]


    ImportAudioFileList = []

    WwiseQueryResults = []
    ExistingWwiseAudio = []

    OPTION_IsStreaming = True

    DefaultOriginalsPathForNewFiles = "WAAPI/TestImports"  ##TODO Variable this based on import language/SFX



#store a ref to the selected parent object
    parentObject = None
    parentObjectPath = ""
    parentID = ""

#flow control
    parentSelected = False
    objectCreated = False
    eventCreated = False

#dic to store return/results from yield calls
    Results = {}

    ImportOperationSuccess = False

# Internal Variables for object creation
    objParID = "None"

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

        def exit():
            self.leave()

        try:
            res = yield From(self.call(WAAPI_URI.ak_wwise_core_getinfo))  # RPC call without arguments
        except Exception as ex:
            print("call error: {}".format(ex))
        else:
            # Call was successful, displaying information from the payload.
            print("Hello {} {}".format(res.kwresults['displayName'], res.kwresults['version']['displayName']))


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
                cancelUndoGroup()
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


        def ImportIntoWwiseUnderParentObject(parentObjectID):
            # subscribe to selection change?
            #print("Method to get the parent to create new object under")
            success = False
            parID = parentObjectID

            #print("Selected object is...")
            if parID != None:
                success = True
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
                        yield setupImportArgs(parID, file, MyComponent.DefaultOriginalsPathForNewFiles)
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

            importFilelist.append(
                {
                    "audioFile": fileList,
                    #"objectPath": "<Sound SFX>"+os.path.basename(audiofilename
                    "objectPath": objectPath + objectType + os.path.basename(audiofilename)
                    #"objectPath": "<Sound Voice>" + os.path.basename(audiofilename)
                }
            )
            MyComponent.importArgs = {
                "importOperation": "useExisting",
                "default": {
                    "importLanguage": MyComponent.ImportLanguage,
                    "importLocation": ParentID,
                    "originalsSubFolder": originalsPath+originalsSubDir,
                    "notes":"This object was auto imported",
                    "@IsStreamingEnabled": MyComponent.OPTION_IsStreaming,
                    "@IsZeroLantency": MyComponent.OPTION_IsStreaming,
                    "event": eventPath+"\\"+os.path.basename(audiofilename)+"@Play"
                    #,"ErrorTest":"Failme"
                    },
                "imports": importFilelist
                }

        def importAudioFiles(args):
            try:
                yield self.call(WAAPI_URI.ak_wwise_core_audio_import, {}, **args)
            except Exception as ex:
                print("call error: {}".format(ex))
                MyComponent.ImportOperationSuccess = False
                cancelUndoGroup()
            else:
                MyComponent.ImportOperationSuccess = True

        def SetupImportParentObject(objectName):
            # Setting up the import parent object
            arguments = {
                "from": {"path": ["\Actor-Mixer Hierarchy"]},
                "transform": [
                    {"select":['descendants']},
                    {"where": ["name:matches", objectName]}
                ],
                "options": {
                    "return": ["id","type", "name", "path"]
                }
            }
            try:
                res = yield From(self.call(WAAPI_URI.ak_wwise_core_object_get, **arguments))
            except Exception as ex:
                print("call error: {}".format(ex))
                cancelUndoGroup()
            else:
                ID = ""
                obj = ""
                path = ""
                for x in res.kwresults["return"]:
                    if x["type"] == "WorkUnit":
                        ID = str(x["id"])
                        obj = x
                        path = str(x["path"])
                MyComponent.parentObject = obj
                MyComponent.parentObjectPath = path
                MyComponent.parentID = ID


        def setupBatchFileSysArgs():
            print("Importing Audio files into.. "+sys.argv[1])  # Import section name
            MyComponent.INPUT_SectionName = str(sys.argv[1])


        def walk_up_folder(path, depth):
            _cur_depth = 0
            while _cur_depth < depth:
                path = os.path.dirname(path)
                _cur_depth += 1
            return path

        if (len(sys.argv) > 1):     #If the sys args are longer than the default 1 (script name)
            setupBatchFileSysArgs()

        #askUserForImportDirectory() # instead set this with vars: MyComponent.ImportAudioFilePath

        #Construct the import audio file path
        sharedDir = walk_up_folder(sys.argv[0],MyComponent.stepsUpToCommonDirectory)

        pathToWwiseProject = os.path.join(sharedDir, *MyComponent.DirOfWwiseProjectRoot)
        pathToOriginalFiles = os.path.join(pathToWwiseProject, *MyComponent.pathToOriginalsFromProjectRoot)
        pathToSectionFiles = os.path.join(pathToOriginalFiles,MyComponent.INPUT_SectionName)

        MyComponent.ImportAudioFilePath = os.path.abspath(pathToSectionFiles)

        if MyComponent.ImportAudioFilePath == '':
            print("Error. Directory not selected. Exiting application.")
            self.leave()
            return

        #Get the ID of the parent object from Wwise
        wwiseParentObjectPath = MyComponent.INPUT_SectionName

        beginUndoGroup()

        yield SetupImportParentObject(wwiseParentObjectPath)

        yield ImportIntoWwiseUnderParentObject(MyComponent.parentID)




        exit()



    def onDisconnect(self):
        print("The client was disconnected.")

        asyncio.get_event_loop().stop()


if __name__ == '__main__':
    runner = ApplicationRunner(url=u"ws://127.0.0.1:8080/waapi", realm=u"realm1")
    try:
        runner.run(MyComponent)
    except Exception as e:
        print(type(e).__name__ + ": Is Wwise running and Wwise Authoring API enabled?")
