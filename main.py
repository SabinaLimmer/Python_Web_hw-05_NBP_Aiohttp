import platform
import aiohttp
import asyncio
import datetime
import sys

class ExchangeRateProvider:
    async def get_exchange_rates(self, currency, days, session):
        raise NotImplementedError("Subclasses must implement this method.")

class NBPExchangeRateProvider(ExchangeRateProvider):
    async def get_exchange_rates(self, currency, days, session):
        base_url = "http://api.nbp.pl/api/exchangerates/rates/c"
        result = []

        for day_offset in range(int(days)):
            date = datetime.date.today() - datetime.timedelta(days=day_offset)
            formatted_date = date.strftime("%d.%m.%Y")

            url = f"{base_url}/{currency}/last/{day_offset + 1}/?format=json"
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    rates = {
                        formatted_date: {
                            currency: {
                                'sale': data['rates'][0]['ask'],
                                'purchase': data['rates'][0]['bid']
                            }
                        }
                    }
                    result.append(rates)
                else:
                    print(f"Error fetching data for {formatted_date}. Status: {response.status}")

        return result

class ExchangeRateCollector:
    def __init__(self, providers):
        self.providers = providers

    async def collect_rates(self, currencies, days, session):
        result = []
        for currency in currencies:
            for provider in self.providers:
                rates = await provider.get_exchange_rates(currency, days, session)
                result.extend(rates)
        return result

async def main(days):
    async with aiohttp.ClientSession() as session:
        nbp_provider = NBPExchangeRateProvider()
        collector = ExchangeRateCollector([nbp_provider])

        currencies = ["EUR", "USD"]
        result = await collector.collect_rates(currencies, days, session)
        print(result)

if __name__ == "__main__":
    if platform.system() == 'Windows':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    if len(sys.argv) != 2:
        print("Usage: python main.py <number_of_days>")
        sys.exit(1)

    try:
        days = int(sys.argv[1])
    except ValueError:
        print("Invalid input. Please provide a valid number of days.")
        sys.exit(1)

    if days <= 0:
        print("Number of days must be greater than zero.")
        sys.exit(1)

    asyncio.run(main(days))
