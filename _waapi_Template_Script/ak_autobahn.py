import inspect

import six
import txaio

from autobahn import util
from autobahn.wamp import exception, types, uri
from autobahn.wamp.message import Call, Subscribe
from autobahn.wamp.protocol import CallRequest, is_method_or_function
from autobahn.asyncio.wamp import ApplicationSession
from autobahn.wamp.request import Handler, SubscribeRequest

class AkCall(Call):
    """
    Special implementation with support for custom options
    """
    def __init__(self, request, procedure, args=None, kwargs=None):
        super(AkCall, self).__init__(request, procedure, args, kwargs)
        self.options = kwargs.pop(u"options", {})

    def marshal(self):
        """
        Reimplemented to return a fully formed message with custom options
        """
        res = [Call.MESSAGE_TYPE, self.request, self.options, self.procedure, self.args or []]
        if self.kwargs:
            res.append(self.kwargs)
        return res


class AkSubscribe(Subscribe):
    """
    Special implementation with support for custom options
    """
    def __init__(self, request, topic, options=None):
        super(AkSubscribe, self).__init__(request, topic)
        self.options = options or {}

    def marshal(self):
        """
        Reimplemented to return a fully formed message with custom options
        """
        return [Subscribe.MESSAGE_TYPE, self.request, self.options, self.topic]


class AkComponent(ApplicationSession):
    def call(self, procedure, *args, **kwargs):
        """
        Reimplemented to support calls with custom options
        """
        if six.PY2 and type(procedure) == str:
            procedure = six.u(procedure)
        assert(isinstance(procedure, six.text_type))
        if not self._transport:
            raise exception.TransportLost()

        request_id = util.id()
        on_reply = txaio.create_future()
        self._call_reqs[request_id] = CallRequest(request_id, procedure, on_reply, {})

        try:
            self._transport.send(AkCall(request_id, procedure, args, kwargs))
        except Exception as e:
            if request_id in self._call_reqs:
                del self._call_reqs[request_id]
            raise e
        return on_reply

    def _subscribe(self, obj, fn, topic, options):
        request_id = self._request_id_gen.next()
        on_reply = txaio.create_future()
        handler_obj = Handler(fn, obj, None)
        self._subscribe_reqs[request_id] = SubscribeRequest(request_id, topic, on_reply, handler_obj)
        self._transport.send(AkSubscribe(request_id, topic, options))
        return on_reply

    def subscribe(self, handler, topic=None, options=None):
        """
        Implements :func:`autobahn.wamp.interfaces.ISubscriber.subscribe`
        """
        if six.PY2 and type(topic) == str:
            topic = six.u(topic)
        assert (topic is None or type(topic) == six.text_type)
        assert((callable(handler) and topic is not None) or hasattr(handler, '__class__'))
        assert (options is None or isinstance(options, dict))

        if not self._transport:
            raise exception.TransportLost()

        if callable(handler):
            # subscribe a single handler
            return self._subscribe(None, handler, topic, options)
        else:
            # subscribe all methods on an object decorated with "wamp.subscribe"
            on_replies = []
            for k in inspect.getmembers(handler.__class__, is_method_or_function):
                proc = k[1]
                wampuris = filter(lambda x: x.is_handler(), proc.__dict__.get("_wampuris")) or ()
                for pat in wampuris:
                    subopts = pat.options or options or types.SubscribeOptions(
                        match=u"wildcard" if pat.uri_type == uri.Pattern.URI_TYPE_WILDCARD else
                              u"exact").message_attr()
                    on_replies.append(self._subscribe(handler, proc, pat.uri(), subopts))
            return txaio.gather(on_replies, consume_exceptions=True)
