import ccxt
import pandas as pd
import numpy as np
import time
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig( # Configurar o logger para gravar em um arquivo
   level=logging.INFO,
   format='%(asctime)s %(levelname)s: %(message)s',
   handlers=[
       logging.FileHandler('arbitrage_bot.log'),
       logging.StreamHandler()  # Também exibir no console
   ]
)
api_keys = { # Configurações das exchanges
   'binance': {
       'apiKey': os.getenv('API_KEY_TESTE_BINANCE'),
       'secret': 'SEU_API_SECRET_BINANCE'
   },
   'kraken': {
       'apiKey': 'SEU_API_KEY_KRAKEN',
       'secret': 'SEU_API_SECRET_KRAKEN'
   }
}
# Inicializar exchanges
exchanges = {
   'binance': ccxt.binance({
       'apiKey': api_keys['binance']['apiKey'],
       'secret': api_keys['binance']['secret'],
       'enableRateLimit': True,
   }),
   'kraken': ccxt.kraken({
       'apiKey': api_keys['kraken']['apiKey'],
       'secret': api_keys['kraken']['secret'],
       'enableRateLimit': True,
   })
}
symbol = 'BTC/USDT' # Par de moedas a ser negociado
log_df = pd.DataFrame(columns=['timestamp', 'level', 'message']) # DataFrame para armazenar os logs

def add_log_to_df(level, message): # Função para adicionar log ao DataFrame
   global log_df
   new_log = pd.DataFrame({'timestamp': [pd.Timestamp.now()], 'level': [level], 'message': [message]})
   log_df = pd.concat([log_df, new_log], ignore_index=True)
   log_df.to_excel('arbitrage_bot_logs.xlsx', index=False) # Salvar o DataFrame em um arquivo Excel

def fetch_price(exchange, symbol): # Função para buscar o preço de uma criptomoeda em uma exchange
   ticker = exchanges[exchange].fetch_ticker(symbol)
   return ticker['last']

def get_trade_fee(exchange, symbol, side): # Função para obter a taxa de transação
   market = exchanges[exchange].markets[symbol]
   fee = market['taker'] if side == 'taker' else market['maker']
   return fee

def get_balance(exchange, currency): # Função para obter saldo disponível
   balance = exchanges[exchange].fetch_balance()
   return balance['free'][currency]

def arbitrage(): # Função para executar arbitragem
   arbitrage_threshold = 0.002  # 0.2%
   amount = 0.01  # Ajuste conforme necessário
   while True:
       try:
           binance_price = fetch_price('binance', symbol)
           kraken_price = fetch_price('kraken', symbol)
           binance_fee = get_trade_fee('binance', symbol, 'taker')
           kraken_fee = get_trade_fee('kraken', symbol, 'taker')
           # Identificar oportunidades de arbitragem
           if binance_price < kraken_price * (1 - arbitrage_threshold - kraken_fee - binance_fee): # Comprar na Binance e vender na Kraken
               usdt_balance = get_balance('binance', 'USDT')
               btc_balance = get_balance('kraken', 'BTC')
               if usdt_balance >= binance_price * amount and btc_balance >= amount:
                   message = f"Arbitragem encontrada: Comprar na Binance por {binance_price} e vender na Kraken por {kraken_price}"
                   logging.info(message)
                   add_log_to_df('INFO', message)
                   exchanges['binance'].create_market_buy_order(symbol, amount)
                   exchanges['kraken'].create_market_sell_order(symbol, amount)
               else:
                   message = "Saldo insuficiente para executar a arbitragem."
                   logging.warning(message)
                   add_log_to_df('WARNING', message)
           elif kraken_price < binance_price * (1 - arbitrage_threshold - binance_fee - kraken_fee): # Comprar na Kraken e vender na Binance
               usdt_balance = get_balance('kraken', 'USDT')
               btc_balance = get_balance('binance', 'BTC')
               if usdt_balance >= kraken_price * amount and btc_balance >= amount:
                   message = f"Arbitragem encontrada: Comprar na Kraken por {kraken_price} e vender na Binance por {binance_price}"
                   logging.info(message)
                   add_log_to_df('INFO', message)
                   exchanges['kraken'].create_market_buy_order(symbol, amount)
                   exchanges['binance'].create_market_sell_order(symbol, amount)
               else:
                   message = "Saldo insuficiente para executar a arbitragem."
                   logging.warning(message)
                   add_log_to_df('WARNING', message)
           # Esperar alguns segundos antes de verificar novamente
           time.sleep(10)
       except Exception as e:
           message = f"Erro: {e}"
           logging.error(message)
           add_log_to_df('ERROR', message)
           time.sleep(10)
if __name__ == "__main__":
   arbitrage()