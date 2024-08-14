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


global seqno


async def initialization_wallet():
    mnemonics = SENDER_SEED_PHRASE.split(' ')

    version = WalletVersionEnum.v4r2

    mnemonics, pub_k, priv_k, wallet = Wallets.from_mnemonics(mnemonics=mnemonics, version=version, workchain=0)
    return wallet


async def send(session, wallet, recipient_address, seqnoo, post_url):
    amount = round(random.uniform(AMOUNT[0], AMOUNT[1]), 4)

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
            print(f'Successfully created transaction. Sending {amount} TON to {recipient_address}...')
            return True, amount
        else:
            return False, None


async def wait_for_seqno_change(session, get_url, seqno):
    if USE_API_KEY is True and API_KEY != '':
        delay = 0.3
    else:
        delay = 2

    while True:
        await asyncio.sleep(delay)
        if seqno == 0:
            info = await get_wallet_info(session, get_url)
            if info['status'] == 'uninit':
                await asyncio.sleep(delay)
                continue
            else:
                if info['seqno'] > seqno:
                    return True
                else:
                    await asyncio.sleep(delay)
                    continue
        else:
            info = await get_wallet_info(session, get_url)
            if info['seqno'] > seqno:
                return True
            else:
                await asyncio.sleep(delay)
                continue


async def get_wallet_info(session, get_url):
    async with session.get(get_url) as response:
        if response.status == 200:
            return await response.json()
        else:
            print(f'Error getting wallet info: {response.status}, {response.text}, {await response.json()}')
        return None


async def main():
    global seqno
    if USE_API_KEY is True and API_KEY != '':
        get_url = f'https://toncenter.com/api/v3/wallet?address={SENDER_ADDRESS}&api_key={API_KEY}'
        post_url = f'https://toncenter.com/api/v3/message?api_key={API_KEY}'
    else:
        get_url = f'https://toncenter.com/api/v3/wallet?address={SENDER_ADDRESS}'
        post_url = f'https://toncenter.com/api/v3/message'

    with open('wallet.txt', 'r') as f:
        recipient_addresses = [line.strip() for line in f.readlines()]

    wallet = await initialization_wallet()

    async with aiohttp.ClientSession() as session:
        info = await get_wallet_info(session, get_url)
        await asyncio.sleep(1)
        if info['status'] == 'uninit':
            seqno = 0
        else:
            seqno = info['seqno']

        for recipient_address in recipient_addresses:
            if USE_API_KEY is True and API_KEY != '':
                sending, amount = await send(session, wallet, recipient_address, seqno, post_url)
                if sending is True:
                    change = await wait_for_seqno_change(session, get_url, seqno)
                    if change:
                        seqno += 1
                    else:
                        raise Exception(f"Error with {recipient_address}.")
                    print(f'{amount} TON was sent to {recipient_address}.')
                await asyncio.sleep(0.1)
            else:
                sending, amount = await send(session, wallet, recipient_address, seqno, post_url)
                await asyncio.sleep(2)
                if sending is True:
                    change = await wait_for_seqno_change(session, get_url, seqno)
                    if change:
                        seqno += 1
                    else:
                        raise Exception(f"Error with {recipient_address}.")
                    print(f'{amount} TON was sent to {recipient_address}.')
                await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
