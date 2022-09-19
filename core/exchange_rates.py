from djmoney.contrib.exchange.backends.base import BaseExchangeBackend


class ExchangeRateAPIBackend(BaseExchangeBackend):
    name = 'ExchangeRateAPIBackend'
    url = 'https://api.exchangeratesapi.io/latest'

    def get_params(self):
        return {'base': 'JPY'}

    def get_rates(self, **kwargs):
        response = self.get_response(**kwargs)
        return self.parse_json(response)['rates']
