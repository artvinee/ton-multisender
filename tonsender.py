import asyncio
import random
from tonsdk.contract.wallet import Wallets, WalletVersionEnum
from tonsdk.utils import to_nano, bytes_to_b64str
import aiohttp


# Settings
#---------------------------------
SENDER_SEED_PHRASE = ''  # v4r2 only
SENDER_ADDRESS = ''  # v4r2 only
AMOUNT = [0.11, 0.13]  # ton
USE_API_KEY = True  # or False, but much more latency and possible overload of the non-key api,
# get api key from @tonapibot (mainnet only)
API_KEY = ''
# --------------------------------

async def send_ton_to_address(recipient_address, session):
    mnemonics = SENDER_SEED_PHRASE.split(' ')

    version = WalletVersionEnum.v4r2

    mnemonics, pub_k, priv_k, wallet = Wallets.from_mnemonics(mnemonics=mnemonics, version=version, workchain=0)

    if USE_API_KEY == True and API_KEY != '':
        get_url = f'https://toncenter.com/api/v3/wallet?address={SENDER_ADDRESS}&api_key={API_KEY}'
        post_url = f'https://toncenter.com/api/v3/message?api_key={API_KEY}'
    else:
        get_url = f'https://toncenter.com/api/v3/wallet?address={SENDER_ADDRESS}'
        post_url = f'https://toncenter.com/api/v3/message'

    async with session.get(get_url) as resp:
        if resp.status == 200:
            r = await resp.json()
            if r['seqno']:
                seqnoo = r['seqno']
            else:
                seqnoo = 0
        else:
            print(f'Error for {recipient_address}: {resp.status}')

    amount = round(random.uniform(AMOUNT[0], AMOUNT[1]), 6)

    query = wallet.create_transfer_message(to_addr=recipient_address,
                                           amount=to_nano(float(amount), 'ton'),
                                           seqno=int(seqnoo)
                                           )

    boc = bytes_to_b64str(query["message"].to_boc(False))

    json = {
        "boc": str(boc)
    }
    async with session.post(post_url, json=json) as resp:
        if resp.status == 200:
            print(f'{amount} TON was sent to {recipient_address}.')


async def main():
    with open('wallets.txt', 'r') as f:
        recipient_addresses = [line.strip() for line in f.readlines()]

    async with aiohttp.ClientSession() as session:
        for recipient_address in recipient_addresses:
            if USE_API_KEY is True and API_KEY != '':
                await send_ton_to_address(recipient_address, session)
                await asyncio.sleep(random.uniform(0.5, 0.8))
            else:
                await send_ton_to_address(recipient_address, session)
                await asyncio.sleep(random.uniform(1, 2))


if __name__ == "__main__":
    asyncio.run(main())