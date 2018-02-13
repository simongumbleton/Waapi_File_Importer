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

    transportObject = 18446744073709551614

    xRtpcName = ""
    yRtpcName = ""

    xTextValue = ""
    yTextValue = ""


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


        def CreateTransport():
            args = {"object": "{D6EA19C7-A50C-4DF4-95B2-FCAB0A2A9BE1}"}
            try:
                yield From(self.call(WAAPI_URI.ak_wwise_core_transport_create, [], **args))
            except Exception as ex:
                print("call error: {}".format(ex))

        def GetTransport():
            try:
                transport = yield From(self.call(WAAPI_URI.ak_wwise_core_transport_getlist))
            except Exception as ex:
                print("call error: {}".format(ex))
            else:
                print (transport.kwresults['list'])

        def SetRTPCs(rtpcs):
            #print("Setting rtpcs in list")
            #print(rtpcs)
            #print("x rtpc = " + MyComponent.xRtpcName)
            #print("y rtpc = " + MyComponent.yRtpcName)
            spanXvalues = (
                    MyComponent.SelectableRtpcs[MyComponent.xRtpcName]["@Max"]
                    - MyComponent.SelectableRtpcs[MyComponent.xRtpcName]["@Min"]
            )
            spanYvalues = (
                    MyComponent.SelectableRtpcs[MyComponent.yRtpcName]["@Max"]
                    - MyComponent.SelectableRtpcs[MyComponent.yRtpcName]["@Min"]
            )

            scaledX = MyComponent.SelectableRtpcs[MyComponent.xRtpcName]["@Min"] + (rtpcs[0] * spanXvalues)
            scaledY = MyComponent.SelectableRtpcs[MyComponent.yRtpcName]["@Min"] + (rtpcs[1] * spanYvalues)

            print(MyComponent.xRtpcName+" = "+str(scaledX)+ "  "+MyComponent.yRtpcName+" = "+str(scaledY))

            Xarguments = {"rtpc": MyComponent.xRtpcName, "value": scaledX, "gameObject": MyComponent.transportObject}
            self.call(WAAPI_URI.ak_soundengine_setrtpcvalue, **Xarguments)
            Yarguments = {"rtpc": MyComponent.yRtpcName, "value": scaledY, "gameObject": MyComponent.transportObject}
            self.call(WAAPI_URI.ak_soundengine_setrtpcvalue, **Yarguments)

        def BindRTPCsToAxis(rtpc, axis):
            print("bind rtpc to axis")


        def mouseMove(event):
            #print (MyComponent.c.canvasx(event.x),MyComponent.c.canvasy(event.y))
            xnorm = MyComponent.c.canvasx(event.x)/MyComponent.canvasWidth
            ynorm = 1 - (MyComponent.c.canvasy(event.y)/MyComponent.canvasHeight)
            #print(xnorm,ynorm)
            SetRTPCs([xnorm,ynorm])
            # Xarguments = {"rtpc": MyComponent.xRtpcName, "value": xnorm, "gameObject": 0}
            # yield From(self.call(WAAPI_URI.ak_soundengine_setrtpcvalue, **Xarguments))
            # Yarguments = {"rtpc": MyComponent.xRtpcName, "value": ynorm, "gameObject": 0}
            # yield From(self.call(WAAPI_URI.ak_soundengine_setrtpcvalue, **Yarguments))



            #set rtpcs with mouse movement

        def show_width(event):
            MyComponent.c.itemconfigure("event", text="winfo_height: %s" % event.widget.winfo_height())
            MyComponent.canvasHeight = event.widget.winfo_height()
            MyComponent.c.itemconfigure("cget", text="winfo_width: %s" % event.widget.winfo_width())
            MyComponent.canvasWidth = event.widget.winfo_width()

        def changeDropdown(*args):
            MyComponent.xRtpcName = str(MyComponent.Xrtpc.get())
            print("X axis RTPC is " + MyComponent.xRtpcName)
            MyComponent.yRtpcName = str(MyComponent.Yrtpc.get())
            print("Y axis RTPC is " + MyComponent.yRtpcName)

        def setupDropDownMenu():

            MyComponent.Xrtpc.set(MyComponent.optionmenuRtpcs[0])
            MyComponent.xRtpcName = str(MyComponent.optionmenuRtpcs[0])
            Xoptions = OptionMenu(MyComponent.frame, MyComponent.Xrtpc, *MyComponent.optionmenuRtpcs)
            # Label(frame,text="Choose RTPC for X axis").grid(row=1,column=1)
            #Xoptions.grid(row=1, column=10)
            xText = Label(MyComponent.frame, text="Choose rtpc for X axis ", bg="red", fg="white")
            xText.pack(side=LEFT)
            Xoptions.pack(side=LEFT)


            MyComponent.Yrtpc.set(MyComponent.optionmenuRtpcs[1])
            MyComponent.yRtpcName = str(MyComponent.optionmenuRtpcs[1])
            Yoptions = OptionMenu(MyComponent.frame, MyComponent.Yrtpc, *MyComponent.optionmenuRtpcs)
            # Label(frame,text="Choose RTPC for X axis").grid(row=1,column=1)
            #Yoptions.grid(row=2, column=1)
            yText = Label(MyComponent.frame, text="Choose rtpc for Y axis ", bg="blue", fg="white")
            yText.pack(side=LEFT)
            Yoptions.pack(side=LEFT)

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

        #MyComponent.xTextValue = MyComponent.c.create_text(100, 100, text=str(MyComponent.xRtpcName) + " = ")
        #MyComponent.yTextValue = MyComponent.c.create_text(200, 100, text=str(MyComponent.yRtpcName) + " = ")


        #MyComponent.c.create_rectangle('16m','10.5m','21m','15.5m',fill='blue')
        MyComponent.c.bind('<Motion>', mouseMove)
        MyComponent.c.bind("<Configure>", show_width)
        MyComponent.Xrtpc.trace('w',changeDropdown)
        MyComponent.Yrtpc.trace('w', changeDropdown)

        MyComponent.root2.mainloop()

        exit()


    def onDisconnect(self):
        print("The client was disconnected.")

        asyncio.get_event_loop().stop()


if __name__ == '__main__':
    runner = ApplicationRunner(url=u"ws://127.0.0.1:8095/waapi", realm=u"realm1")
    try:
        runner.run(MyComponent)
    except Exception as e:
        print(type(e).__name__ + ": Is Wwise running and Wwise Authoring API enabled?")
