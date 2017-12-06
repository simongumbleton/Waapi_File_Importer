import sys
import os
from autobahn.twisted.wamp import ApplicationRunner
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.internet.error import ConnectionRefusedError
from ak_autobahn import AkComponent

sys.path.append(os.path.join(os.path.dirname(__file__), '../../../../include/AK/WwiseAuthoringAPI/py'))
from waapi import WAAPI_URI


class MyComponent(AkComponent):
    """
    Subclass of AkComponent which allows to use custom options
    """

    @inlineCallbacks
    def onJoin(self, details):
        @inlineCallbacks
        def on_selection_changed():
            # Options are passed as a special argument called "options"
            arguments = {"options": {"return": ["name"]}}
            res = yield self.call(WAAPI_URI.ak_wwise_ui_getselectedobjects, **arguments)
            data = res.kwresults[u"objects"][0]
            print("New selection: " + data[u"name"])
            self.disconnect()

        # Subscribe to selectionChanged, calls on_selection_changed when the event is received
        yield self.subscribe(on_selection_changed, WAAPI_URI.ak_wwise_ui_selectionchanged)

    def onDisconnect(self):
        # Disconnected
        print("The client was disconnected.")
        reactor.stop()

if __name__ == "__main__":
    runner = ApplicationRunner(u"ws://localhost:8080/waapi", u"pubsub_demo")
    try:
        runner.run(MyComponent)
    except ConnectionRefusedError as e:
        print(type(e).__name__ + ": Is Wwise running and Wwise Authoring API enabled?")
        sys.exit(1)
