"""
   See https://bittrex.com/Home/Api
"""

import time
import hmac
import hashlib

try:
    from urllib import urlencode
    from urlparse import urljoin
except ImportError:
    from urllib.parse import urlencode
    from urllib.parse import urljoin

try:
    from Crypto.Cipher import AES
except ImportError:
    encrypted = False
else:
    import getpass
    import ast
    import json

    encrypted = True

import requests

BUY_ORDERBOOK = 'buy'
SELL_ORDERBOOK = 'sell'
BOTH_ORDERBOOK = 'both'

ORDERTYPE_LIMIT = 'LIMIT'
ORDERTYPE_MARKET = 'MARKET'

TIMEINEFFECT_GOOD_TIL_CANCELLED = 'GOOD_TIL_CANCELLED'
TIMEINEFFECT_IMMEDIATE_OR_CANCEL = 'IMMEDIATE_OR_CANCEL'
TIMEINEFFECT_FILL_OR_KILL = 'FILL_OR_KILL'

CONDITIONTYPE_NONE = 'NONE'
CONDITIONTYPE_GREATER_THAN = 'GREATER_THAN'
CONDITIONTYPE_LESS_THAN = 'LESS_THAN'
CONDITIONTYPE_STOP_LOSS_FIXED = 'STOP_LOSS_FIXED'
CONDITIONTYPE_STOP_LOSS_PERCENTAGE = 'STOP_LOSS_PERCENTAGE'

USING_V1_1 = 'v1.1'
USING_V2_0 = 'v2.0'

BASE_URL_V1_1 = 'https://bittrex.com/api/v1.1{path}?'
BASE_URL_V2_0 = 'https://bittrex.com/api/v2.0{path}?'

PROTECTION_PUB = 'pub'  # public methods
PROTECTION_PRV = 'prv'  # authenticated methods


def encrypt(api_key, api_secret, export=True, export_fn='secrets.json'):
    cipher = AES.new(getpass.getpass(
        'Input encryption password (string will not show)'))
    api_key_n = cipher.encrypt(api_key)
    api_secret_n = cipher.encrypt(api_secret)
    api = {'key': str(api_key_n), 'secret': str(api_secret_n)}
    if export:
        with open(export_fn, 'w') as outfile:
            json.dump(api, outfile)
    return api


def using_requests(request_url, apisign):
    return requests.get(
        request_url,
        headers={"apisign": apisign}
    ).json()


def api_v1_1(path=None, options=None, api_key=None, protection=PROTECTION_PUB):
    request_url = BASE_URL_V1_1.format(path=path)
    nonce = str(int(time.time() * 1000))

    if protection != PROTECTION_PUB:
        request_url = "{0}apikey={1}&nonce={2}&".format(request_url, api_key, nonce)

    return request_url, options


def api_v2_0(path=None, options=None, api_key=None, protection=PROTECTION_PUB):
    request_url = BASE_URL_V2_0.format(path=path)
    nonce = str(int(time.time() * 1000))

    if protection != PROTECTION_PUB:
        request_url = "{0}apikey={1}&nonce={2}&".format(request_url, api_key, nonce)

    return request_url, options


class Bittrex(object):
    """
    Used for requesting Bittrex with API key and API secret
    """

    def __init__(self, api_key, api_secret, calls_per_second=1, dispatch=using_requests, using_api=USING_V1_1):
        self.api_key = str(api_key) if api_key is not None else ''
        self.api_secret = str(api_secret) if api_secret is not None else ''
        self.dispatch = dispatch
        self.call_rate = 1.0 / calls_per_second
        self.last_call = None
        self.using_api = using_api
        self.api_dispatch = api_v2_0 if using_api == USING_V2_0 else api_v1_1

    def decrypt(self):
        if encrypted:
            cipher = AES.new(getpass.getpass(
                'Input decryption password (string will not show)'))
            try:
                if isinstance(self.api_key, str):
                    self.api_key = ast.literal_eval(self.api_key)
                if isinstance(self.api_secret, str):
                    self.api_secret = ast.literal_eval(self.api_secret)
            except Exception:
                pass
            self.api_key = cipher.decrypt(self.api_key).decode()
            self.api_secret = cipher.decrypt(self.api_secret).decode()
        else:
            raise ImportError('"pycrypto" module has to be installed')

    def wait(self):
        if self.last_call is None:
            self.last_call = time.time()
        else:
            now = time.time()
            passed = now - self.last_call
            if passed < self.call_rate:
                # print("sleep")
                time.sleep(1.0 - passed)

            self.last_call = time.time()

    def _api_query(self, protection=None, path_dict=None, options=None):
        """
        Queries Bittrex

        :param request_url: fully-formed URL to request
        :type options: dict
        :return: JSON response from Bittrex
        :rtype : dict
        """
        if not options:
            options = {}

        if self.using_api not in path_dict:
            raise Exception('method call not available under API version {}'.format(self.using_api))

        request_url, options = \
            self.api_dispatch(protection=protection, options=options, api_key=self.api_key,
                              path=path_dict[self.using_api])

        request_url += urlencode(options)

        apisign = hmac.new(self.api_secret.encode(),
                           request_url.encode(),
                           hashlib.sha512).hexdigest()

        self.wait()

        return self.dispatch(request_url, apisign)

    def get_markets(self):
        """
        Used to get the open and available trading markets
        at Bittrex along with other meta data.

        1.1 Endpoint: /public/getmarkets
        2.0 Endpoint: /pub/Markets/GetMarkets

        Example ::
            {'success': True,
             'message': '',
             'result': [ {'MarketCurrency': 'LTC',
                          'BaseCurrency': 'BTC',
                          'MarketCurrencyLong': 'Litecoin',
                          'BaseCurrencyLong': 'Bitcoin',
                          'MinTradeSize': 1e-08,
                          'MarketName': 'BTC-LTC',
                          'IsActive': True,
                          'Created': '2014-02-13T00:00:00',
                          'Notice': None,
                          'IsSponsored': None,
                          'LogoUrl': 'https://i.imgur.com/R29q3dD.png'},
                          ...
                        ]
            }

        :return: Available market info in JSON
        :rtype : dict
        """
        return self._api_query(path_dict={
            USING_V1_1: '/public/getmarkets',
            USING_V2_0: '/pub/Markets/GetMarkets'
        }, protection=PROTECTION_PUB)

    def get_currencies(self):
        """
        Used to get all supported currencies at Bittrex
        along with other meta data.

        Endpoint:
        1.1 /public/getcurrencies
        2.0 /pub/Currencies/GetCurrencies

        :return: Supported currencies info in JSON
        :rtype : dict
        """
        return self._api_query(path_dict={
            USING_V1_1: '/public/getcurrencies',
            USING_V2_0: '/pub/Currencies/GetCurrencies'
        }, protection=PROTECTION_PUB)

    def get_ticker(self, market):
        """
        Used to get the current tick values for a market.

        Endpoints:
        1.1 /public/getticker
        2.0 /pub/Currencies/GetCurrencies

        :param market: String literal for the market (ex: BTC-LTC)
        :type market: str
        :return: Current values for given market in JSON
        :rtype : dict
        """
        return self._api_query(path_dict={
            USING_V1_1: '/public/getticker',
            USING_V2_0: '/pub/Currencies/GetCurrencies'
        }, options={'market': market, 'marketname': market}, protection=PROTECTION_PUB)

    def get_market_summaries(self):
        """
        Used to get the last 24 hour summary of all active exchanges

        Endpoint:
        1.1 /public/getmarketsummaries
        2.0 /pub/Market/GetMarketSummaries

        :return: Summaries of active exchanges in JSON
        :rtype : dict
        """
        return self._api_query(path_dict={
            USING_V1_1: '/public/getmarketsummaries',
            USING_V2_0: '/pub/Market/GetMarketSummaries'
        }, protection=PROTECTION_PUB)

    def get_marketsummary(self, market):
        """
        Used to get the last 24 hour summary of all active
        exchanges in specific coin

        Endpoint:
        1.1 /public/getmarketsummary
        2.0 /pub/Market/GetMarketSummary

        :param market: String literal for the market(ex: BTC-XRP)
        :type market: str
        :return: Summaries of active exchanges of a coin in JSON
        :rtype : dict
        """
        return self._api_query(path_dict={
            USING_V1_1: '/public/getmarketsummary',
            USING_V2_0: '/pub/Market/GetMarketSummary'
        }, options={'market': market, 'marketname': market}, protection=PROTECTION_PUB)

    def get_orderbook(self, market, depth_type):
        """
        Used to get retrieve the orderbook for a given market

        Endpoint:
        1.1 /public/getorderbook
        2.0 NO EQUIVALENT

        :param market: String literal for the market (ex: BTC-LTC)
        :type market: str
        :param depth_type: buy, sell or both to identify the type of
            orderbook to return.
            Use constants BUY_ORDERBOOK, SELL_ORDERBOOK, BOTH_ORDERBOOK
        :type depth_type: str
        :return: Orderbook of market in JSON
        :rtype : dict
        """
        return self._api_query(path_dict={
            USING_V1_1: '/public/getorderbook',
        }, options={'market': market, 'type': depth_type}, protection=PROTECTION_PUB)

    def get_market_history(self, market):
        """
        Used to retrieve the latest trades that have occurred for a
        specific market.

        Endpoint:
        1.1 /market/getmarkethistory
        2.0 /pub/Market/GetMarketHistory

        Example ::
            {'success': True,
            'message': '',
            'result': [ {'Id': 5625015,
                         'TimeStamp': '2017-08-31T01:29:50.427',
                         'Quantity': 7.31008193,
                         'Price': 0.00177639,
                         'Total': 0.01298555,
                         'FillType': 'FILL',
                         'OrderType': 'BUY'},
                         ...
                       ]
            }

        :param market: String literal for the market (ex: BTC-LTC)
        :type market: str
        :return: Market history in JSON
        :rtype : dict
        """
        return self._api_query(path_dict={
            USING_V1_1: '/market/getmarkethistory',
            USING_V2_0: '/pub/Market/GetMarketHistory'
        }, options={'market': market, 'marketname': market}, protection=PROTECTION_PUB)

    # def buy_limit(self, market, quantity, rate):
    #     """
    #     Used to place a buy order in a specific market. Use buylimit to place
    #     limit orders Make sure you have the proper permissions set on your
    #     API keys for this call to work
    #
    #     Endpoint: /market/buylimit
    #
    #     :param market: String literal for the market (ex: BTC-LTC)
    #     :type market: str
    #     :param quantity: The amount to purchase
    #     :type quantity: float
    #     :param rate: The rate at which to place the order.
    #         This is not needed for market orders
    #     :type rate: float
    #     :return:
    #     :rtype : dict
    #     """
    #     return self._api_query(path_dict={
    #         USING_V1_1: '',
    #         USING_V2_0: ''
    #     }, options={'market': market,
    #                 'quantity': quantity,
    #                 'rate': rate})
    #
    # def sell_limit(self, market, quantity, rate):
    #     """
    #     Used to place a sell order in a specific market. Use selllimit to place
    #     limit orders Make sure you have the proper permissions set on your
    #     API keys for this call to work
    #
    #     Endpoint: /market/selllimit
    #
    #     :param market: String literal for the market (ex: BTC-LTC)
    #     :type market: str
    #     :param quantity: The amount to purchase
    #     :type quantity: float
    #     :param rate: The rate at which to place the order.
    #         This is not needed for market orders
    #     :type rate: float
    #     :return:
    #     :rtype : dict
    #     """
    #     return self._api_query(path_dict={
    #         USING_V1_1: '',
    #         USING_V2_0: ''
    #     }, options={'market': market,
    #                 'quantity': quantity,
    #                 'rate': rate})

    # def cancel(self, uuid):
    #     """
    #     Used to cancel a buy or sell order
    #
    #     Endpoint: /market/cancel
    #
    #     :param uuid: uuid of buy or sell order
    #     :type uuid: str
    #     :return:
    #     :rtype : dict
    #     """
    #     return self._api_query('cancel', {'uuid': uuid})
    #
    # def get_open_orders(self, market=None):
    #     """
    #     Get all orders that you currently have opened.
    #     A specific market can be requested.
    #
    #     Endpoint: /market/getopenorders
    #
    #     :param market: String literal for the market (ie. BTC-LTC)
    #     :type market: str
    #     :return: Open orders info in JSON
    #     :rtype : dict
    #     """
    #     return self._api_query('getopenorders',
    #                            {'market': market} if market else None)
    #
    def get_balances(self):
        """
        Used to retrieve all balances from your account.

        Endpoint:
        1.1 /account/getbalances
        2.0 /key/balance/getbalances

        Example ::
            {'success': True,
             'message': '',
             'result': [ {'Currency': '1ST',
                          'Balance': 10.0,
                          'Available': 10.0,
                          'Pending': 0.0,
                          'CryptoAddress': None},
                          ...
                        ]
            }


        :return: Balances info in JSON
        :rtype : dict
        """
        return self._api_query(path_dict={
            USING_V1_1: '/account/getbalances',
            USING_V2_0: '/key/balance/getbalances'
        }, protection=PROTECTION_PRV)

    def get_balance(self, currency):
        """
        Used to retrieve the balance from your account for a specific currency

        Endpoint:
        1.1 /account/getbalance
        2.0 /key/balance/getbalance

        Example ::
            {'success': True,
             'message': '',
             'result': {'Currency': '1ST',
                        'Balance': 10.0,
                        'Available': 10.0,
                        'Pending': 0.0,
                        'CryptoAddress': None}
            }


        :param currency: String literal for the currency (ex: LTC)
        :type currency: str
        :return: Balance info in JSON
        :rtype : dict
        """
        return self._api_query(path_dict={
            USING_V1_1: '/account/getbalance',
            USING_V2_0: '/key/balance/getbalance'
        }, options={'currency': currency, 'currencyname': currency}, protection=PROTECTION_PRV)

        # def get_deposit_address(self, currency):
        #     """
        #     Used to generate or retrieve an address for a specific currency
        #
        #     Endpoint: /account/getdepositaddress
        #
        #     :param currency: String literal for the currency (ie. BTC)
        #     :type currency: str
        #     :return: Address info in JSON
        #     :rtype : dict
        #     """
        #     return self._api_query('getdepositaddress', {'currency': currency})
        #
        # def withdraw(self, currency, quantity, address):
        #     """
        #     Used to withdraw funds from your account
        #
        #     Endpoint: /account/withdraw
        #
        #     :param currency: String literal for the currency (ie. BTC)
        #     :type currency: str
        #     :param quantity: The quantity of coins to withdraw
        #     :type quantity: float
        #     :param address: The address where to send the funds.
        #     :type address: str
        #     :return:
        #     :rtype : dict
        #     """
        #     return self._api_query('withdraw',
        #                            {'currency': currency,
        #                             'quantity': quantity,
        #                             'address': address})
        #
        # def get_order_history(self, market=None):
        #     """
        #     Used to retrieve order trade history of account
        #
        #     Endpoint: /account/getorderhistory
        #
        #     :param market: optional a string literal for the market (ie. BTC-LTC).
        #         If omitted, will return for all markets
        #     :type market: str
        #     :return: order history in JSON
        #     :rtype : dict
        #     """
        #     return self._api_query('getorderhistory',
        #                            {'market': market} if market else None)
        #
        # def get_order(self, uuid):
        #     """
        #     Used to get details of buy or sell order
        #
        #     Endpoint: /account/getorder
        #
        #     :param uuid: uuid of buy or sell order
        #     :type uuid: str
        #     :return:
        #     :rtype : dict
        #     """
        #     return self._api_query('getorder', {'uuid': uuid})
        #
        # def get_withdrawal_history(self, currency=None):
        #     """
        #     Used to view your history of withdrawals
        #
        #     Endpoint: /account/getwithdrawalhistory
        #
        #     :param currency: String literal for the currency (ie. BTC)
        #     :type currency: str
        #     :return: withdrawal history in JSON
        #     :rtype : dict
        #     """
        #
        #     return self._api_query('getwithdrawalhistory',
        #                            {'currency': currency} if currency else None)
        #
        # def get_deposit_history(self, currency=None):
        #     """
        #     Used to view your history of deposits
        #
        #     Endpoint: /account/getdeposithistory
        #
        #     :param currency: String literal for the currency (ie. BTC)
        #     :type currency: str
        #     :return: deposit history in JSON
        #     :rtype : dict
        #     """
        #     return self._api_query('getdeposithistory',
        #                            {'currency': currency} if currency else None)
        #
        # def list_markets_by_currency(self, currency):
        #     """
        #     Helper function to see which markets exist for a currency.
        #
        #     Endpoint: /public/getmarkets
        #
        #     Example ::
        #         >>> Bittrex(None, None).list_markets_by_currency('LTC')
        #         ['BTC-LTC', 'ETH-LTC', 'USDT-LTC']
        #
        #     :param currency: String literal for the currency (ex: LTC)
        #     :type currency: str
        #     :return: List of markets that the currency appears in
        #     :rtype: list
        #     """
        #     return [market['MarketName'] for market in self.get_markets()['result']
        #             if market['MarketName'].lower().endswith(currency.lower())]
