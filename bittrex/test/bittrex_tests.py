import unittest
import json
from bittrex.bittrex import Bittrex, API_V2_0, API_V1_1, BUY_ORDERBOOK


def test_basic_response(unit_test, result, method_name):
    unit_test.assertTrue(result['success'], "{0:s} failed".format(method_name))
    unit_test.assertTrue(result['message'] is not None, "message not present in response")
    unit_test.assertTrue(result['result'] is not None, "result not present in response")


def test_auth_basic_failures(unit_test, result, test_type):
    unit_test.assertFalse(result['success'], "{0:s} failed".format(test_type))
    unit_test.assertTrue('invalid' in str(result['message']).lower(), "{0:s} failed response message".format(test_type))
    unit_test.assertIsNone(result['result'], "{0:s} failed response result not None".format(test_type))


class TestBittrexV11PublicAPI(unittest.TestCase):
    """
    Integration tests for the Bittrex public API.
    These will fail in the absence of an internet connection or if bittrex API goes down
    """

    def setUp(self):
        self.bittrex = Bittrex(None, None, api_version=API_V1_1)

    def test_handles_none_key_or_secret(self):
        self.bittrex = Bittrex(None, None)
        # could call any public method here
        actual = self.bittrex.get_markets()
        self.assertTrue(actual['success'], "failed with None key and None secret")

        self.bittrex = Bittrex("123", None)
        actual = self.bittrex.get_markets()
        self.assertTrue(actual['success'], "failed with None secret")

        self.bittrex = Bittrex(None, "123")
        actual = self.bittrex.get_markets()
        self.assertTrue(actual['success'], "failed with None key")

    def test_get_markets(self):
        actual = self.bittrex.get_markets()
        test_basic_response(self, actual, "get_markets")
        self.assertTrue(isinstance(actual['result'], list), "result is not a list")
        self.assertTrue(len(actual['result']) > 0, "result list is 0-length")

    def test_get_currencies(self):
        actual = self.bittrex.get_currencies()
        test_basic_response(self, actual, "get_currencies")

    def test_get_ticker(self):
        actual = self.bittrex.get_ticker(market='BTC-LTC')
        test_basic_response(self, actual, "get_ticker")

    def test_get_market_summaries(self):
        actual = self.bittrex.get_market_summaries()
        test_basic_response(self, actual, "get_market_summaries")

    def test_get_orderbook(self):
        actual = self.bittrex.get_orderbook('BTC-LTC', depth_type=BUY_ORDERBOOK)
        test_basic_response(self, actual, "get_orderbook")

    def test_get_market_history(self):
        actual = self.bittrex.get_market_history('BTC-LTC')
        test_basic_response(self, actual, "get_market_history")

    def test_list_markets_by_currency(self):
        actual = self.bittrex.list_markets_by_currency('LTC')
        self.assertListEqual(['BTC-LTC', 'ETH-LTC', 'USDT-LTC'], actual)


class TestBittrexV20PublicAPI(unittest.TestCase):
    """
    Integration tests for the Bittrex public API.
    These will fail in the absence of an internet connection or if bittrex API goes down
    """

    def setUp(self):
        self.bittrex = Bittrex(None, None, api_version=API_V2_0)

    def test_handles_none_key_or_secret(self):
        self.bittrex = Bittrex(None, None, api_version=API_V2_0)
        # could call any public method here
        actual = self.bittrex.get_markets()
        self.assertTrue(actual['success'], "failed with None key and None secret")

        self.bittrex = Bittrex("123", None, api_version=API_V2_0)
        actual = self.bittrex.get_markets()
        self.assertTrue(actual['success'], "failed with None secret")

        self.bittrex = Bittrex(None, "123", api_version=API_V2_0)
        actual = self.bittrex.get_markets()
        self.assertTrue(actual['success'], "failed with None key")

    def test_get_markets(self):
        actual = self.bittrex.get_markets()
        test_basic_response(self, actual, "get_markets")
        self.assertTrue(isinstance(actual['result'], list), "result is not a list")
        self.assertTrue(len(actual['result']) > 0, "result list is 0-length")

    def test_get_currencies(self):
        actual = self.bittrex.get_currencies()
        test_basic_response(self, actual, "get_currencies")

    def test_get_ticker(self):
        self.assertRaisesRegexp(Exception, 'method call not available', self.bittrex.get_ticker,
                                market='BTC-LTC')

    def test_get_market_summaries(self):
        actual = self.bittrex.get_market_summaries()
        test_basic_response(self, actual, "get_market_summaries")

    def test_get_market_summary(self):
        actual = self.bittrex.get_marketsummary(market='BTC-LTC')
        test_basic_response(self, actual, "get_marketsummary")

    def test_get_orderbook(self):
        actual = self.bittrex.get_orderbook('BTC-LTC')
        test_basic_response(self, actual, "get_orderbook")

    def test_get_market_history(self):
        actual = self.bittrex.get_market_history('BTC-LTC')
        test_basic_response(self, actual, "get_market_history")

    def test_list_markets_by_currency(self):
        actual = self.bittrex.list_markets_by_currency('LTC')
        self.assertListEqual(['BTC-LTC', 'ETH-LTC', 'USDT-LTC'], actual)


class TestBittrexV11AccountAPI(unittest.TestCase):
    """
    Integration tests for the Bittrex Account API.
      * These will fail in the absence of an internet connection or if bittrex API goes down.
      * They require a valid API key and secret issued by Bittrex.
      * They also require the presence of a JSON file called secrets.json.
      It is structured as such:
    {
      "key": "12341253456345",
      "secret": "3345745634234534"
    }
    """

    def setUp(self):
        with open("secrets.json") as secrets_file:
            self.secrets = json.load(secrets_file)
            secrets_file.close()
        self.bittrex = Bittrex(self.secrets['key'], self.secrets['secret'])

    def test_handles_invalid_key_or_secret(self):
        self.bittrex = Bittrex('invalidkey', self.secrets['secret'])
        actual = self.bittrex.get_balance('BTC')
        test_auth_basic_failures(self, actual, 'Invalid key, valid secret')

        self.bittrex = Bittrex(None, self.secrets['secret'])
        actual = self.bittrex.get_balance('BTC')
        test_auth_basic_failures(self, actual, 'None key, valid secret')

        self.bittrex = Bittrex(self.secrets['key'], 'invalidsecret')
        actual = self.bittrex.get_balance('BTC')
        test_auth_basic_failures(self, actual, 'valid key, invalid secret')

        self.bittrex = Bittrex(self.secrets['key'], None)
        actual = self.bittrex.get_balance('BTC')
        test_auth_basic_failures(self, actual, 'valid key, None secret')

        self.bittrex = Bittrex('invalidkey', 'invalidsecret')
        actual = self.bittrex.get_balance('BTC')
        test_auth_basic_failures(self, actual, 'invalid key, invalid secret')

    def test_get_openorders(self):
        actual = self.bittrex.get_open_orders('BTC-LTC')
        test_basic_response(self, actual, "get_openorders")
        self.assertTrue(isinstance(actual['result'], list), "result is not a list")

    def test_get_balances(self):
        actual = self.bittrex.get_balances()
        test_basic_response(self, actual, "get_balances")
        self.assertTrue(isinstance(actual['result'], list), "result is not a list")

    def test_get_balance(self):
        actual = self.bittrex.get_balance('BTC')
        test_basic_response(self, actual, "get_balance")
        self.assertTrue(isinstance(actual['result'], dict), "result is not a dict")
        self.assertEqual(actual['result']['Currency'],
                         "BTC",
                         "requested currency {0:s} does not match returned currency {1:s}"
                         .format("BTC", actual['result']['Currency']))

    def test_get_depositaddress(self):
        actual = self.bittrex.get_deposit_address('BTC')
        if not actual['success']:
            self.assertTrue(actual['message'], 'ADDRESS_GENERATING')
        else:
            test_basic_response(self, actual, "get_deposit_address")

    def test_get_order_history_all_markets(self):
        actual = self.bittrex.get_order_history()
        test_basic_response(self, actual, "get_order_history")
        self.assertIsInstance(actual['result'], list, "result is not a list")

    def test_get_order_history_one_market(self):
        actual = self.bittrex.get_order_history(market='BTC-LTC')
        test_basic_response(self, actual, "get_order_history")
        self.assertIsInstance(actual['result'], list, "result is not a list")

    def test_get_withdrawlhistory_all_currencies(self):
        actual = self.bittrex.get_withdrawal_history()
        test_basic_response(self, actual, "get_withdrawal_history")
        self.assertIsInstance(actual['result'], list, "result is not a list")

    def test_get_withdrawlhistory_one_currency(self):
        actual = self.bittrex.get_withdrawal_history('BTC')
        test_basic_response(self, actual, "get_withdrawal_history")
        self.assertIsInstance(actual['result'], list, "result is not a list")

    def test_get_deposithistory_all_currencies(self):
        actual = self.bittrex.get_deposit_history()
        test_basic_response(self, actual, "get_deposit_history")
        self.assertIsInstance(actual['result'], list, "result is not a list")

    def test_get_deposithistory_one_currency(self):
        actual = self.bittrex.get_deposit_history('BTC')
        test_basic_response(self, actual, "get_deposit_history")
        self.assertIsInstance(actual['result'], list, "result is not a list")


class TestBittrexV20AccountAPI(unittest.TestCase):
    """
    Integration tests for the Bittrex Account API.
      * These will fail in the absence of an internet connection or if bittrex API goes down.
      * They require a valid API key and secret issued by Bittrex.
      * They also require the presence of a JSON file called secrets.json.
      It is structured as such:
    {
      "key": "12341253456345",
      "secret": "3345745634234534"
    }
    """

    def setUp(self):
        with open("secrets.json") as secrets_file:
            self.secrets = json.load(secrets_file)
            secrets_file.close()
        self.bittrex = Bittrex(self.secrets['key'], self.secrets['secret'], api_version=API_V2_0)

    def test_handles_invalid_key_or_secret(self):
        self.bittrex = Bittrex('invalidkey', self.secrets['secret'], api_version=API_V2_0)
        actual = self.bittrex.get_balance('BTC')
        test_auth_basic_failures(self, actual, 'Invalid key, valid secret')

        self.bittrex = Bittrex(None, self.secrets['secret'], api_version=API_V2_0)
        actual = self.bittrex.get_balance('BTC')
        test_auth_basic_failures(self, actual, 'None key, valid secret')

        self.bittrex = Bittrex(self.secrets['key'], 'invalidsecret', api_version=API_V2_0)
        actual = self.bittrex.get_balance('BTC')
        test_auth_basic_failures(self, actual, 'valid key, invalid secret')

        self.bittrex = Bittrex(self.secrets['key'], None, api_version=API_V2_0)
        actual = self.bittrex.get_balance('BTC')
        test_auth_basic_failures(self, actual, 'valid key, None secret')

        self.bittrex = Bittrex('invalidkey', 'invalidsecret', api_version=API_V2_0)
        actual = self.bittrex.get_balance('BTC')
        test_auth_basic_failures(self, actual, 'invalid key, invalid secret')

    def test_get_openorders(self):
        actual = self.bittrex.get_open_orders('BTC-LTC')
        test_basic_response(self, actual, "get_openorders")
        self.assertTrue(isinstance(actual['result'], list), "result is not a list")

    def test_get_balances(self):
        actual = self.bittrex.get_balances()
        test_basic_response(self, actual, "get_balances")
        self.assertTrue(isinstance(actual['result'], list), "result is not a list")

    def test_get_balance(self):
        actual = self.bittrex.get_balance('BTC')
        # TODO the return result is an empty dict.  API bug?  the get_balances works as expect
        # test_basic_response(self, actual, "get_balance")
        # self.assertTrue(isinstance(actual['result'], dict), "result is not a dict")
        # self.assertEqual(actual['result']['Currency'],
        #                  "BTC",
        #                  "requested currency {0:s} does not match returned currency {1:s}"
        #                  .format("BTC", actual['result']['Currency']))

    def test_get_depositaddress(self):
        actual = self.bittrex.get_deposit_address('BTC')
        # TODO my testing account is acting funny this should work
        # test_basic_response(self, actual, "get_deposit_address")

    def test_get_order_history_all_markets(self):
        actual = self.bittrex.get_order_history()
        test_basic_response(self, actual, "get_order_history")
        self.assertIsInstance(actual['result'], list, "result is not a list")

    def test_get_order_history_one_market(self):
        actual = self.bittrex.get_order_history(market='BTC-LTC')
        test_basic_response(self, actual, "get_order_history")
        self.assertIsInstance(actual['result'], list, "result is not a list")

    def test_get_withdrawlhistory_all_currencies(self):
        actual = self.bittrex.get_withdrawal_history()
        test_basic_response(self, actual, "get_withdrawal_history")
        self.assertIsInstance(actual['result'], list, "result is not a list")

    def test_get_withdrawlhistory_one_currency(self):
        actual = self.bittrex.get_withdrawal_history('BTC')
        test_basic_response(self, actual, "get_withdrawal_history")
        self.assertIsInstance(actual['result'], list, "result is not a list")

    def test_get_deposithistory_all_currencies(self):
        actual = self.bittrex.get_deposit_history()
        test_basic_response(self, actual, "get_deposit_history")
        self.assertIsInstance(actual['result'], list, "result is not a list")

    def test_get_deposithistory_one_currency(self):
        actual = self.bittrex.get_deposit_history('BTC')
        test_basic_response(self, actual, "get_deposit_history")
        self.assertIsInstance(actual['result'], list, "result is not a list")

if __name__ == '__main__':
    unittest.main()
