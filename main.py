import asyncio
import aiohttp
import platform
from datetime import datetime, timedelta
import sys
# the program starting after command -> py main.py 1-10
DAYS=sys.argv[1]

async def get_url(date):
    url=f'https://api.privatbank.ua/p24api/exchange_rates?json&date={date}'
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as response:
                if response.status==200:
                    html=await response.json()
                    return html
                else:
                    print(f'Error status {response.status} for {url}')
        except aiohttp.ClientConnectorError as err:
            print(f'Connection error {url}, {err}')


async def get_session(days):
    tasks = []
    for i in range(days):
        data = (datetime.now() - timedelta(days=i)).strftime("%d.%m.%Y")
        tasks.append(get_url(data))
    result= await asyncio.gather(*tasks)

    output = []
    for data in result:
        item = {data['date']: {}}
        if "exchangeRate" in data:
            for rate in data["exchangeRate"]:
                if rate['currency'] == 'USD':
                    item[data['date']]['USD'] = {
                        'sale': rate['saleRateNB'],
                        'purchase': rate['purchaseRateNB']
                    }
                elif rate['currency'] == 'EUR':
                    item[data['date']]['EUR'] = {
                        'sale': rate['saleRateNB'],
                        'purchase': rate['purchaseRateNB']
                    }
        output.append(item)
    return output

async def main():
    if platform.system() == 'Windows' and int(DAYS)<=10:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        r  = await get_session(int(DAYS))
        for i in r:
            print(i)
    else:
        print('Error')


if __name__=='__main__':
    asyncio.run(main())





