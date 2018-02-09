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



class MyComponent(AkComponent):

#list of rtpcs in wwise
    RawListOfRtpcsInWwise = {}
#List of rtpcs for selection
    SelectableRtpcs = {}
    optionmenuRtpcs = []

    root2 = Tkinter.Tk()
#Frame setup
    frame = Frame(root2, width=500, height=800, bd=1)
    frame.grid(column=0, row=0, sticky=(N,W,E,S))
    frame.columnconfigure(0, weight=1)
    frame.rowconfigure(0, weight=1)
    frame.pack(padx=20,pady=20)

    iframe5 = Frame(frame, bd=2)
    iframe5.pack()#(expand=1, fill=X, pady=10, padx=5)

#Canvas setup for XY plane
    c = Canvas(frame, width=500,height=500,background='gray')
    c.pack()

    c.create_text(10, 30, anchor="sw", tags=["event"])
    c.create_text(10, 30, anchor="nw", tags=["cget"])

    canvasWidth = 500
    canvasHeight = 500


    Xrtpc = StringVar(root2)

    Yrtpc = StringVar(root2)



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

        def getRTPCsInWwise():
            #print("Get a list of the audio files currently in the project, under the selected object")
            arguments = {
                "from": {"ofType": ["GameParameter"]},

                "options": {
                    "return": ["id", "name", "@Min", "@Max","@SimulationValue" ]
                }
            }

            try:
                res = yield From(self.call(WAAPI_URI.ak_wwise_core_object_get, **arguments))
            except Exception as ex:
                print("call error: {}".format(ex))
            else:
                MyComponent.RawListOfRtpcsInWwise = res.kwresults["return"]
                print (MyComponent.RawListOfRtpcsInWwise)
                i = 0
                for rtpc in MyComponent.RawListOfRtpcsInWwise:
                    print (rtpc)
                    key =  str(MyComponent.RawListOfRtpcsInWwise[i]["name"])
                    MyComponent.SelectableRtpcs[key] = MyComponent.RawListOfRtpcsInWwise[i]
                    MyComponent.optionmenuRtpcs.append(key)
                    i +=1



        def SetRTPCs(rtpcs):
            print("Setting rtpcs in list")

        def BindRTPCsToAxis(rtpc, axis):
            print("bind rtpc to axis")


        def mouseMove(event):
            #print (MyComponent.c.canvasx(event.x),MyComponent.c.canvasy(event.y))
            xnorm = MyComponent.c.canvasx(event.x)/MyComponent.canvasWidth
            ynorm = MyComponent.c.canvasy(event.y)/MyComponent.canvasHeight
            print(xnorm,ynorm)
            #set rtpcs with mouse movement

        def show_width(event):
            MyComponent.c.itemconfigure("event", text="winfo_height: %s" % event.widget.winfo_height())
            MyComponent.canvasHeight = event.widget.winfo_height()
            MyComponent.c.itemconfigure("cget", text="winfo_width: %s" % event.widget.winfo_width())
            MyComponent.canvasWidth = event.widget.winfo_width()

        def changeDropdown(*args):
            print(MyComponent.Xrtpc.get())

        def setupDropDownMenu():

            MyComponent.Xrtpc.set("")
            Xoptions = OptionMenu(MyComponent.frame, MyComponent.Xrtpc, MyComponent.optionmenuRtpcs)
            # Label(frame,text="Choose RTPC for X axis").grid(row=1,column=1)
            Xoptions.grid(row=1, column=10)
            Xoptions.pack()


            MyComponent.Yrtpc.set("")
            Yoptions = OptionMenu(MyComponent.frame, MyComponent.Yrtpc, MyComponent.optionmenuRtpcs)
            # Label(frame,text="Choose RTPC for X axis").grid(row=1,column=1)
            Yoptions.grid(row=1, column=1)
            Yoptions.pack()

        ###### End of function definitions  #########



        ###### Main logic flow #########
        try:
            res = yield From(self.call(WAAPI_URI.ak_wwise_core_getinfo))  # RPC call without arguments
        except Exception as ex:
            print("call error: {}".format(ex))
        else:
            # Call was successful, displaying information from the payload.
            print("Hello {} {}".format(res.kwresults['displayName'], res.kwresults['version']['displayName']))


        yield getRTPCsInWwise()

        setupDropDownMenu()
        #populate drop down lists X and Y axis

        #bind selected rtpc to axis


        #MyComponent.c.create_rectangle('16m','10.5m','21m','15.5m',fill='blue')
        MyComponent.c.bind('<Motion>', mouseMove)
        MyComponent.c.bind("<Configure>", show_width)
        MyComponent.Xrtpc.trace('w',changeDropdown)

        MyComponent.root2.mainloop()

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
