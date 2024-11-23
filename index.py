import os
import ccxt
import pandas as pd
import numpy as np
import time
import logging
from dotenv import load_dotenv

load_dotenv() # Carregar variáveis de ambiente do arquivo .env

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
       'secret': os.getenv('SECRET_KEY_TESTE_BINANCE')
   },
   'kraken': {
       'apiKey': os.getenv('API_KEY_TESTE_KRAKEN'),
       'secret': os.getenv('SECRET_KEY_TESTE_KRAKEN')
   }
}

exchanges = { # Inicializar exchanges
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

def check_login(exchange, name): # Função para verificar o login
   try:
       # Tentar buscar o saldo da conta
       balance = exchange.fetch_balance()
       logging.info(f"Login na {name} bem-sucedido. Saldo disponível: {balance['free']}")
       return True
   except ccxt.AuthenticationError:
       logging.error(f"Erro de autenticação na {name}. Verifique suas credenciais de API.")
       return False
   except Exception as e:
       logging.error(f"Erro ao acessar a {name}: {e}")
       return False

symbol = 'BTC/USDT' # Par de moedas a ser negociado

log_df = pd.DataFrame(columns=['timestamp', 'level', 'message']) # DataFrame para armazenar os logs

def add_log_to_df(level, message): # Função para adicionar log ao DataFrame
   global log_df
   new_log = pd.DataFrame({'timestamp': [pd.Timestamp.now()], 'level': [level], 'message': [message]})
   log_df = pd.concat([log_df, new_log], ignore_index=True)
  
   log_df.to_excel('arbitrage_bot_logs.xlsx', index=False)  # Salvar o DataFrame em um arquivo Excel

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

def simulate_order(exchange, order_type, symbol, amount): # Função para simular uma ordem de compra
   logging.info(f"Simulação de {order_type} order na {exchange} para {amount} de {symbol}")
   add_log_to_df('INFO', f"Simulação de {order_type} order na {exchange} para {amount} de {symbol}")
   # Adicionar lógica de simulação, como ajustar saldos fictícios

def arbitrage(): # Função para executar arbitragem
   arbitrage_threshold = 0.001  # 0.2%
   amount = 0.01  # Ajuste conforme necessário
   while True:
       try:
           binance_price = fetch_price('binance', symbol)
           print('binance: ',binance_price)
           kraken_price = fetch_price('kraken', symbol)
           print('kraken: ',kraken_price)
           binance_fee = get_trade_fee('binance', symbol, 'taker')
           kraken_fee = get_trade_fee('kraken', symbol, 'taker')
           # Identificar oportunidades de arbitragem
           
        #    print(kraken_price * (1 - arbitrage_threshold - kraken_fee - binance_fee),'calculo binance < kraken')
        #    print(binance_price * (1 - arbitrage_threshold - binance_fee - kraken_fee),'calculo kraken < binance')
           if binance_price < kraken_price * (1 - arbitrage_threshold - kraken_fee - binance_fee):
               # Simular compra na Binance e venda na Kraken
               logging.info(f"Arbitragem encontrada: Comprar na Binance por {binance_price} e vender na Kraken por {kraken_price}")
               simulate_order('binance', 'compra', symbol, amount)
               simulate_order('kraken', 'venda', symbol, amount)
           elif kraken_price < binance_price * (1 - arbitrage_threshold - binance_fee - kraken_fee):
               # Simular compra na Kraken e venda na Binance
               logging.info(f"Arbitragem encontrada: Comprar na Kraken por {kraken_price} e vender na Binance por {binance_price}")
               simulate_order('kraken', 'compra', symbol, amount)
               simulate_order('binance', 'venda', symbol, amount)
          
           time.sleep(10)  # Esperar alguns segundos antes de verificar novamente
       except Exception as e:
           logging.error(f"Erro: {e}")
           add_log_to_df('ERROR', f"Erro: {e}")
           time.sleep(5)
if __name__ == "__main__":
   if check_login(exchanges['binance'], 'Binance') and check_login(exchanges['kraken'], 'Kraken'):
       arbitrage()
   else:
       logging.error("Login falhou em uma ou mais exchanges. Verifique suas credenciais de API.")