import asyncio
from multiprocessing.dummy import Pool
from sys import stderr

import aiofiles
import aiohttp
from loguru import logger
from pyuseragents import random as random_useragent
from web3.auto import w3

logger.remove()
logger.add(stderr, format="<white>{time:HH:mm:ss}</white>"
                          " | <level>{level: <8}</level>"
                          " | <cyan>{line}</cyan>"
                          " - <white>{message}</white>")

headers = {
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,'
              'image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-language': 'ru,en;q=0.9,vi;q=0.8,es;q=0.7,cy;q=0.6'
}


def format_keys(value: str) -> str:
    if value.startswith('0x'):
        return value

    return f'0x{value}'


class Main:
    @staticmethod
    async def get_address(private_key: str) -> str:
        while True:
            try:
                address = w3.to_checksum_address(w3.eth.account.from_key(private_key).address)

                return address

            except Exception as error:
                logger.error(f'{private_key} | Ошибка при получении баланса: {error}')

    async def main_work(self,
                        private_key: str) -> None:
        address = await self.get_address(private_key=private_key)

        async with aiohttp.ClientSession(headers={
            **headers,
            'user-agent': random_useragent()
        }) as session:
            while True:
                try:
                    async with session.get(f'https://api.arbdoge.ai/arb/eligibility/{address}') as r:
                        if (await r.json())['data']['isEligible']:
                            if (await r.json())['data']['hasClaimed']:
                                logger.info(f'{private_key} | Already Claimed')

                                async with aiofiles.open('claimed.txt', 'a', encoding='utf-8-sig') as f:
                                    await f.write(f'{private_key}\n')

                            else:
                                logger.success(f'{private_key} | Eligible')

                                async with aiofiles.open('eligible.txt', 'a', encoding='utf-8-sig') as f:
                                    await f.write(f'{private_key}\n')

                        else:
                            logger.error(f'{private_key} | Not Eligible')

                            async with aiofiles.open('not_eligible.txt', 'a', encoding='utf-8-sig') as f:
                                await f.write(f'{private_key}\n')

                    return

                except Exception as error:
                    logger.error(f'{private_key} | Ошибка при проверки доступности дропа: {error}')


def wrapper(private_key: str) -> None:
    try:
        asyncio.run(MainObj.main_work(private_key=private_key))

    except Exception as error:
        logger.error(f'{private_key} | Unexpected Error: {error}')


if __name__ == '__main__':
    MainObj = Main()

    with open('accounts.txt', 'r', encoding='utf-8-sig') as file:
        accounts_list = [format_keys(value=row.strip()) for row in file]

    logger.info(f'Успешно загружено {len(accounts_list)} аккаунтов')
    threads = int(input('\nThreads: '))
    print('')

    with Pool(processes=threads) as executor:
        executor.map(wrapper, accounts_list)

    logger.success('Работа успешно завершена')
    input('\nPress Enter To Exit..')
