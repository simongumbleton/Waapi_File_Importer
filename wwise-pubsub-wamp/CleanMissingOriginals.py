import os
import sys

import trollius as asyncio
from trollius import From

import Tkinter #import Tk
import tkFileDialog
from Tkinter import *

import fnmatch

from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from ak_autobahn import AkComponent

from waapi import WAAPI_URI

Results = {}
parentObject = {}
WwiseQueryResults = {}
WwiseAudioMissingOriginals = {}
WwiseEventsToDelete = []


class MyComponent(AkComponent):


    def onJoin(self, details):
        ###### Function definitions #########

        def exit():
            self.leave()

        def beginUndoGroup():
            self.call(WAAPI_URI.ak_wwise_core_undo_begingroup)

        def cancelUndoGroup():
            self.call(WAAPI_URI.ak_wwise_core_undo_cancelgroup)

        def endUndoGroup():
            undoArgs = {"displayName": "Script Auto Importer"}
            self.call(WAAPI_URI.ak_wwise_core_undo_endgroup, {}, **undoArgs)

        def saveWwiseProject():
            self.call(WAAPI_URI.ak_wwise_core_project_save)

        def setupSubscriptions():
            # Subscribe to ak.wwise.core.object.created
            # Calls on_object_created whenever the event is received
            self.subscribe(onParentSelected, WAAPI_URI.ak_wwise_ui_selectionchanged)

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

        def getAudioFilesInWwise(object):
            #print("Get a list of the audio files currently in the project, under the selected object")
            arguments = {
                "from": {"id": [object]},
                "transform": [
                    {"select": ["descendants"]},
                    {"where":["type:isIn",["Sound"]]}
                ],
                "options": {
                    "return": ["id","type", "name", "path", "sound:originalWavFilePath", "isPlayable","audioSource:playbackDuration"]
                }
            }
            try:
                res = yield From(self.call(WAAPI_URI.ak_wwise_core_object_get, **arguments))
            except Exception as ex:
                print("call error: {}".format(ex))
            else:
                MyComponent.WwiseQueryResults = res.kwresults["return"]

        def getWwiseEventByName(eventName):
            arguments = {
                "from": {"path": ["\\Events"]},
                "transform": [
                    {"select":["descendants"]},
                    {"where": ["name:matches", eventName]}
                ],
                "options": {
                    "return": ["id", "name", "path"]
                }
            }
            try:
                res = yield From(self.call(WAAPI_URI.ak_wwise_core_object_get, **arguments))
            except Exception as ex:
                print("call error: {}".format(ex))
            else:
                MyComponent.WwiseEventsToDelete.append(res.kwresults["return"])

        def createListOfBrokenAudio(WwiseQueryResults):
            #print("creating a list of existing wwise sounds")
            list = []
            for i in WwiseQueryResults:
                #print(i)
                if i["audioSource:playbackDuration"]["playbackDurationMax"] == 0.0:
                    #print(i)
                    list.append(i)
            MyComponent.WwiseAudioMissingOriginals = list

        def onParentSelected():
            yield getSelectedObject()
            obj = MyComponent.Results.kwresults['objects']
            # print(obj[0]['id'])
            MyComponent.parentObject = obj[0]
            # print("Selected object name is...{}".format(MyComponent.parentObject[u"name"]))
            parID = str(MyComponent.parentObject["id"])

            yield getAudioFilesInWwise(parID)
            createListOfBrokenAudio(MyComponent.WwiseQueryResults)

            for x in MyComponent.WwiseAudioMissingOriginals:
                name = x["name"]
                yield getWwiseEventByName(name)

            print("Stop")




        ###### End of function definitions  #########



        ###### Main logic flow #########
        try:
            res = yield From(self.call(WAAPI_URI.ak_wwise_core_getinfo))  # RPC call without arguments
        except Exception as ex:
            print("call error: {}".format(ex))
        else:
            # Call was successful, displaying information from the payload.
            print("Hello {} {}".format(res.kwresults['displayName'], res.kwresults['version']['displayName']))


        setupSubscriptions()





        #exit()


    def onDisconnect(self):
        print("The client was disconnected.")

        asyncio.get_event_loop().stop()


if __name__ == '__main__':
    runner = ApplicationRunner(url=u"ws://127.0.0.1:8080/waapi", realm=u"realm1")
    try:
        runner.run(MyComponent)
    except Exception as e:
        print(type(e).__name__ + ": Is Wwise running and Wwise Authoring API enabled?")
