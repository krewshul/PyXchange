#!/usr/bin/env python2.7

import collections
import unittest

from . import server
from . import engine


class Transport(object):
    def __init__(self):
        self.messages = collections.deque()


    def write(self, data):
        for message in data.split('\n'):
            if message:
                self.messages.append(engine.json_loads(message))


    def assertMessage(self, message):
        assert message == self.messages.popleft()


    def loseConnection(self):
        pass


class JsonTest(unittest.TestCase):
    dct, sdct = { 'key': None }, '{"key": null}'

    def testLoads(self):
        """ Test JSON loads """

        assert engine.json_loads('true')  is True
        assert engine.json_loads('false') is False
        assert engine.json_loads('null')  is None
        assert engine.json_loads(self.sdct) == self.dct

        with self.assertRaises(TypeError):
            assert engine.json_loads(None)


    def testDumps(self):
        """ Test JSON dumpss """

        assert engine.json_dumps(True)  == 'true'
        assert engine.json_dumps(False) == 'false'
        assert engine.json_dumps(None)  == 'null'
        assert engine.json_dumps(self.dct) == self.sdct

        with self.assertRaises(TypeError):
            assert engine.json_dumps(object)


class MatcherTest(unittest.TestCase):
    createOrderRequest  = { u'orderId': 662688, u'price': 145, u'message': u'createOrder', u'side': u'BUY', u'quantity': 350 }
    createOrderResponse = { u'report': u'NEW', u'orderId': 662688, u'quantity': 350, u'message': u'executionReport' }
    createOrderError = { u'text': u'order already exists', u'message': u'error' }

    cancelOrderRequest  = { u'orderId': 662688, u'message': u'cancelOrder' }
    cancelOrderResponse = { u'orderId': 662688, u'message': u'executionReport', 'report': u'CANCELED', u'quantity': 350 }
    cancelOrderError = { u'text': u'order does not exists', u'message': u'error' }


    def setUp(self):
        self.transport = Transport()
        self.matcher = engine.Matcher()
        self.trader = self.matcher.getTrader('trader-1', self.transport)

    def tearDown(self):
        self.matcher.removeTrader(self.trader)


    def testCreateCancelOrder(self):
        """ Test create/cancel order """

        self.matcher.handleMessageDict(self.trader, self.createOrderRequest)
        self.transport.assertMessage(self.createOrderResponse)

        self.matcher.handleMessageDict(self.trader, self.createOrderRequest)
        self.transport.assertMessage(self.createOrderError)

        self.matcher.handleMessageDict(self.trader, self.cancelOrderRequest)
        self.transport.assertMessage(self.cancelOrderResponse)

        self.matcher.handleMessageDict(self.trader, self.cancelOrderRequest)
        self.transport.assertMessage(self.cancelOrderError)


class TradingTest(unittest.TestCase):
    askOrders = [ { u'orderId': 1, u'price': 1000, u'message': u'createOrder',
                    u'side': u'SELL', u'quantity': 4 },
                  { u'orderId': 2, u'price': 1100, u'message': u'createOrder',
                    u'side': u'SELL', u'quantity': 3 },
                  { u'orderId': 3, u'price': 1200, u'message': u'createOrder',
                    u'side': u'SELL', u'quantity': 1 },
                  { u'orderId': 4, u'price': 1200, u'message': u'createOrder',
                    u'side': u'SELL', u'quantity': 8 },
                  { u'orderId': 5, u'price': 1300, u'message': u'createOrder',
                    u'side': u'SELL', u'quantity': 10 } ]

    def setUp(self):
        self.transport1 = Transport()
        self.transport2 = Transport()

        self.matcher = engine.Matcher()

        self.trader1 = self.matcher.getTrader('trader-1', self.transport1)
        self.trader2 = self.matcher.getTrader('trader-2', self.transport2)


    def tearDown(self):
        self.matcher.removeTrader(self.trader1)
        self.matcher.removeTrader(self.trader2)


    def testBidMatchEvent(self):
        for createOrderRequest in self.askOrders:
            self.matcher.handleMessageDict(self.trader2, createOrderRequest)

        createOrderRequest  = { u'orderId': 1, u'price': 1200,
                                u'message': u'createOrder', u'side': u'BUY', u'quantity': 10 }

        self.matcher.handleMessageDict(self.trader1, createOrderRequest)


# EOF
