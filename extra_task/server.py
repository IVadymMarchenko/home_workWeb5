import asyncio
import logging
import websockets
import names
import aiohttp
from datetime import datetime, timedelta
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK

logging.basicConfig(level=logging.INFO)

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


async def get_exchange(days):
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
    return str(output)


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f'{ws.remote_address} connects')

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f'{ws.remote_address} disconnects')

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            if message=='exchange':
                exchange= await get_exchange(1)
                await self.send_to_clients(exchange)
            elif len(message.split()) == 2 and message.split()[0] == 'exchange':
                await self.send_to_clients('Waiting')
                exchange= await get_exchange(int(message.split()[1]))
                await self.send_to_clients(exchange)
            else:
                await self.send_to_clients(f"{ws.name}: {message}")


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, 'localhost', 8080):
        await asyncio.Future()  # run forever

if __name__ == '__main__':
    asyncio.run(main())