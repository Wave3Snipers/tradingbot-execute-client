# built-in
import traceback
from time import sleep
from random import randrange
import ssl
# 3rd party
import asyncio
import websockets
import ccxt
# custom
from utils import *

DEBUG = get_env_var_bool("DEBUG", True)

if DEBUG:
    exchange = ccxt.binance()
else:
    exchange = ccxt.binance({
        'apiKey': API_KEY,
        'secret': API_SECRET,
    })

def retry(func, *args, **kwargs):
    for attempt in range(10):
        try:
            return func(*args, **kwargs)
        except Exception:
            logger.error(f'Request failed. Trying again after sleep (attempt {attempt}/10)')
            logger.error(traceback.format_exc())
            sleep(2)
    return None
    
    
async def place(is_buy, symbol):
    if DEBUG:
        if is_buy:
            logger.info(f"DEBUG - Buy {symbol}")
        else:
            logger.info(f"DEBUG - Sell {symbol}")
        return
    
    if is_buy:
        # handle buy
        if check_stop_buy_file():
            logger.error(f'{symbol} Stop detected. Ignoring buy signals.')
            return
        if check_stop_buy_allow_dca_file():
            logger.error(f'{symbol} Stop with allow DCA detected.')
            if symbol not in bought_coin_qty:
                return
                
        buy_rcpt = retry(exchange.create_market_buy_order_with_cost, symbol, QTY_USDT)
        if not buy_rcpt:
            logger.error(f'{symbol} Failed to place buy order after all attempts exhausted..')
            return

        if symbol in bought_coin_qty:
            bought_coin_qty[symbol] = buy_rcpt['filled'] + bought_coin_qty[symbol]
        else:
            bought_coin_qty[symbol] = buy_rcpt['filled']
        
        logger.info(f"{symbol} Bought {buy_rcpt['filled']}. Total coin amount: {bought_coin_qty[symbol]}" )
    else:
        # handle sell
        if symbol in bought_coin_qty:
            sell_rcpt = retry(exchange.create_market_sell_order, symbol, bought_coin_qty[symbol])
            if not sell_rcpt:
                logger.error(f'{symbol} Failed to place sell order after all attempts exhausted..')
                return

            logger.info(f"{symbol} Sold {sell_rcpt['filled']}" )
            bought_coin_qty.pop(symbol, None)
            
        else:
            logger.error("Data missing: bought qty. Can't sell ")

    
async def ws_handler(uri):
    ssl_context = ssl._create_unverified_context() # skips server certificate validation. note: this means connection can be MiTM 
    async with websockets.connect(uri, ssl=ssl_context,extra_headers={"Authorization": f"{AUTHORIZATION}"}) as websocket:
        logger.info("Connected to server, waiting for signals...")
        while (True):
            try:
                msg = await asyncio.wait_for(websocket.recv(), timeout=30)
                if DEBUG:
                    logger.info(f"Received from WS server : {msg}")
                    
                o = ujson.loads(msg)
                if 's' in o:
                    if o['s'] == 'B':
                        if o['t'] in config_symbols:
                            logger.info(f"Received buy signal {o['t']}")
                            await place(True, o['t'])
                    elif o['s'] == 'S':
                        if o['t'] in config_symbols:
                            logger.info(f"Received sell signal {o['t']}")
                            await place(False, o['t'])
                    else:
                        logger.error("Invalid message")
                    
                    save_status(bought_coin_qty)

            except TimeoutError:
                await websocket.ping()


if __name__ == "__main__":
    logger.info('Starting..')
    bought_coin_qty = load_status()
    exchange.fetch_ohlcv('BTC/USDT', '1m')
    
    while True:
        try:
            if DEBUG:
                asyncio.run(ws_handler('wss://host.docker.internal:3000'))
            else:
                asyncio.run(ws_handler(WS))
        except Exception as e:
            sec = randrange(20, 70)
            if hasattr(e, 'status_code'):
                if e.status_code == 403:
                    logger.error('Invalid license')
                    break
                if e.status_code == 409:
                    logger.error('Conflict')
                    break
                else:
                    logger.error(f'Error: {e.status_code}')
            else:
                logger.error(f"Connection failed, retry in {sec} seconds")
                logger.error(e)

            sleep(sec)