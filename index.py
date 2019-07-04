from flask import Flask, request
from flask_restful import Resource, Api
import pymysql
import json
import config
import requests
import asyncio
import struct
import hashlib
import calendar;
import time;
#from requests_http_signature import HTTPSignatureAuth
from binance.client import Client as Client_binance
from bfxapi import Client as Client_bitfinex
from bitmex_websocket import BitMEXWebsocket
from bittrex.bittrex import *
from coinbase.wallet.client import Client as Client_coinbase
import okex.account_api as account
import krakenex

app = Flask(__name__)
api = Api(app)

db = pymysql.connect(host=config.DATABASE_CONFIG['host'],
		user=config.DATABASE_CONFIG['user'],
		password=config.DATABASE_CONFIG['password'],
		db=config.DATABASE_CONFIG['dbname']
	)

key_bitfinex = config.EXCHANGE_CONFIG['bitfinex_apikey']
pkey_bitfinex = config.EXCHANGE_CONFIG['bitfinex_secret']
bitfinex = Client_bitfinex(
		API_KEY=key_bitfinex,
		API_SECRET=pkey_bitfinex,
		logLevel='DEBUG'
	)

ws_bitmex_btc = BitMEXWebsocket(endpoint="https://www.bitmex.com/api/v1", 
	symbol="XBTUSD", 
	api_key=config.EXCHANGE_CONFIG['bitmex_apikey'], 
	api_secret=config.EXCHANGE_CONFIG['bitmex_secret'])

ws_bitmex_eth = BitMEXWebsocket(endpoint="https://www.bitmex.com/api/v1", 
	symbol="ETHUSD", 
	api_key=config.EXCHANGE_CONFIG['bitmex_apikey'], 
	api_secret=config.EXCHANGE_CONFIG['bitmex_secret'])

bittrex = Bittrex(config.EXCHANGE_CONFIG['bittrex_apikey'], 
	config.EXCHANGE_CONFIG['bittrex_secret'])

coinbase = Client_coinbase(config.EXCHANGE_CONFIG['coinbase_apikey'],config.EXCHANGE_CONFIG['coinbase_secret'])

hitbtc_session = requests.session()
hitbtc_session.auth = (config.EXCHANGE_CONFIG['hitbtc_apikey'], config.EXCHANGE_CONFIG['hitbtc_secret'])

accountAPI = account.AccountAPI(config.EXCHANGE_CONFIG['okex_apikey'], config.EXCHANGE_CONFIG['okex_secret'], 
	config.EXCHANGE_CONFIG['okex_passphrase'], True)
#ts = calendar.timegm(time.gmtime())
#Digifinex Hash
#digifinex_hash = hashlib.md5()
#digifinex_params = { 'timestamp': str(ts), 'apiKey': config.EXCHANGE_CONFIG['digifinex_apikey'], 
#	'apiSecret': config.EXCHANGE_CONFIG['digifinex_secret'] }
#digifinex_keys = sorted(digifinex_params.keys())
#digifinex_line = ''
#for key in digifinex_keys:
#	digifinex_line = digifinex_line + digifinex_params[key]
#digifinex_hash.update(digifinex_line.encode('utf-8'))
#digifinex_signed = digifinex_hash.hexdigest()

#FatBTC Hash
#fatbtc_hash = hashlib.md5()
#fatbtc_params = { 'timestamp': str(ts), 'apiKey': config.EXCHANGE_CONFIG['fatbtc_apikey'], 
#	'apiSecret': config.EXCHANGE_CONFIG['fatbtc_secret'] }
#fatbtc_keys = sorted(fatbtc_params.keys())
#fatbtc_line = ''
#for key in fatbtc_keys:
#	fatbtc_line = fatbtc_line + fatbtc_params[key]
#fatbtc_hash.update(fatbtc_line.encode('utf-8'))
#fatbtc_signed = fatbtc_hash.hexdigest()

result_btc = 0
result_eth = 0
bitfinex_btc = 0
bitfinex_eth = 0
bitfinex_others = []

#Bitfinex wallets
async def get_wallets() :
	global result_btc
	global result_eth
	global bitfinex_btc
	global bitfinex_eth
	global bitfinex_others

	wallets_bitfinex = await bitfinex.rest.get_wallets()
	for w in wallets_bitfinex :
		if(w.currency == 'BTC') :
			result_btc += float(w.balance)
			bitfinex_btc = float(w.balance)
		elif(w.currency == 'ETH') :
			result_eth += float(w.balance)
			bitfinex_eth = float(w.balance)
		elif(float(w.balance) > 0) :
			bitfinex_others.append({ 'symbol': w.currency, 'balance': w.balance })


	#print ("Wallets:")
	#[ print (w) for w in wallets ]

class Main(Resource):
	def get(self):
		if(request.args) :
			args = request.args
			method_name = 'balance_' + str(args['argument'])
			method = getattr(self, method_name, lambda: "Invalid method name " + str(args['argument']))
			return method()

		return { 'result': 'No argument' }

		#cursor = db.cursor()
		#cursor.execute("SELECT * FROM arbitrage_processe-s")
		#row_headers=[x[0] for x in cursor.description] #this will extract row headers
		#numrows = cursor.rowcount
		#rv = cursor.fetchall()
		#coins = []
		#for i in rv:
		#	coins.append(dict(zip(row_headers,i)))

		#return json.dumps(coins, indent=4, sort_keys=True, default=str)

	def post(self):
		args = request.args
		method_name = 'balance_' + str(args['argument'])
		method = getattr(self, method_name, lambda: "Invalid")
		return method()

	def balance_bittrex(self):
		return { 'result': 'bittrex' }

class Multi(Resource):	
	def get(self, num):
		return {'result': num*10}

class Balance(Resource):	
	def get(self) :
		global result_btc
		global result_eth

		binance_btc = 0
		binance_eth = 0
		binance_others = []
		bitmex_btc = 0
		bitmex_eth = 0
		bittrex_btc = 0
		bittrex_eth = 0
		bittrex_others = []
		coinbase_btc = 0
		coinbase_eth = 0
		coinbase_others = []
		digifinex_btc = 0
		digifinex_eth = 0
		digifinex_others = []
		fatbtc_btc = 0
		fatbtc_eth = 0
		fatbtc_others = []
		hitbtc_btc = 0
		hitbtc_eth = 0
		hitbtc_others = []
		okex_btc = 0
		okex_eth = 0
		okex_others = []
		kraken_btc = 0
		kraken_eth = 0
		kraken_others = 0

		key_binance = config.EXCHANGE_CONFIG['binance_apikey']
		pkey_binance = config.EXCHANGE_CONFIG['binance_secret']
		client = Client_binance(key_binance, pkey_binance)
		response_binance = client.get_account()
		for item in response_binance["balances"] :
			if(item["asset"] == 'BTC') :
				binance_btc = float(item["free"])
				result_btc += binance_btc
			elif(item["asset"] == 'ETH') :
				binance_eth = float(item["free"])
				result_eth += binance_eth
			elif(float(item["free"]) > 0) :
				binance_others.append({ 'symbol': item["asset"], 'balance': float(item["free"]) })

		bitmex_btc = float(ws_bitmex_btc.funds()['walletBalance'])
		result_btc += bitmex_btc
		bitmex_eth = float(ws_bitmex_eth.funds()['walletBalance'])
		result_eth += bitmex_eth

		bittrex_eth = float(bittrex.get_balance('ETH')['result']['Balance'])
		result_eth += bittrex_eth

		for item in bittrex.get_balances()["result"] :
			if(item['Currency'] == 'BTC') :
				bittrex_btc = float(item['Balance'])
				result_btc += bittrex_btc
			elif(item['Currency'] == 'ETH') :
				bittrex_eth = float(item['Balance'])
				result_eth += bittrex_eth
			elif(float(item['Balance']) > 0) :
				bittrex_others.append({ 'symbol': item['Currency'] , 
					'balance': float(item['Balance']) })

		for item in coinbase.get_accounts()['data'] :
			if(item['currency'] == 'BTC') :
				coinbase_btc = float(item['balance']['amount'])
				result_btc += coinbase_btc
			elif(item['currency'] == 'ETH') :
				coinbase_eth = float(item['balance']['amount'])
				result_eth += coinbase_eth
			elif(float(item['balance']['amount']) > 0) :
				coinbase_others.append({ 'symbol': item['currency'], 'balance': item['balance']['amount'] })

		ts = str(calendar.timegm(time.gmtime()))
		digifinex_signed = self.signed_request(config.EXCHANGE_CONFIG['digifinex_apikey'], 
					config.EXCHANGE_CONFIG['digifinex_secret'], ts)
		response = requests.get('https://openapi.digifinex.vip/v2/myposition?apiKey=' +
			config.EXCHANGE_CONFIG['digifinex_apikey'] + '&timestamp=' + ts + 
			'&sign=' + digifinex_signed).json()

		for key,value in response['free'] :
			if(key == 'btc') :
				digifinex_btc = float(value)
				result_btc += digifinex_btc
			elif(key == 'eth') :
				digifinex_eth = float(value)
				result_eth += digifinex_eth
			else :
				digifinex_others.append({ 'symbol': key, 'balance': float(value) })

		ts = str(calendar.timegm(time.gmtime()))
		'''
		TODO FATBTC
		fatbtc_signed = self.signed_request(config.EXCHANGE_CONFIG['fatbtc_apikey'], 
			config.EXCHANGE_CONFIG['fatbtc_secret'], ts)
		'' 'response = requests.get('https://www.fatbtc.us/m/api/a/accounts/1/' + 
			config.EXCHANGE_CONFIG['fatbtc_apikey'] + '/' + ts + '/MD5/' + fatbtc_signed).json()'' '
		headers = {
		  'Content-Type' : 'application/json',
		  'site_id' : '1',
		  'api_key' : config.EXCHANGE_CONFIG['fatbtc_apikey'],
		  'sign_type' : 'MD5',
		  'timestamp' : ts,
		  'sign' : fatbtc_signed
		}
		response = requests.get('https://www.fatbtc.us/m/api/a/accounts/1/', headers=headers)

		print('FatBTC')
		print(response)'''

		hitbtc_balances = hitbtc_session.get('https://api.hitbtc.com/api/2/account/balance');

		for item in hitbtc_balances.json():
			if item['currency'] == 'BTC' :
				hitbtc_btc = float(item['available'])
				result_btc += hitbtc_btc
			elif item['currency'] == 'ETH' :
				hitbtc_eth = float(item['available'])
				result_eth += hitbtc_eth
			elif float(item['available']) > 0 :
				hitbtc_others.append({ 'symbol': item['currency'], 'balance': item['available'] })

		response = accountAPI.get_wallet()
		for item in response:
			if item['currency'] == 'BTC':
				okex_btc = float(item['available'])
				result_btc += okex_btc
			elif item['currency'] == 'ETH' :
				okex_eth = float(item['available'])
				result_eth += okex_eth
			elif float(item['available']) > 0 :
				okex_others.append({ 'symbol': item['currency'], 'balance': item['available'] })


		k = krakenex.API()
		k.load_key('kraken.key')

		print('Kraken')
		print(k.query_private('Balance'))

		return { 
			'result_btc': result_btc, 
			'result_eth': result_eth, 
			'binance_btc': binance_btc,
			'binance_eth': binance_eth,
			'binance_others' : binance_others,
			'bitfinex_btc': bitfinex_btc, 
			'bitfinex_eth': bitfinex_eth,
			'bitfinex_others': bitfinex_others,
			'bitmex_btc': bitmex_btc,
			'bitmex_eth': bitmex_eth,
			'bittrex_btc': bittrex_btc,
			'bittrex_eth': bittrex_eth,
			'bittrex_others': bittrex_others,
			'coinbase_btc': coinbase_btc,
			'coinbase_eth': coinbase_eth,
			'coinbase_others': coinbase_others,
			'digifinex_btc': digifinex_btc,
			'digifinex_eth': digifinex_eth,
			'digifinex_others': digifinex_others,
			'hitbtc_btc': hitbtc_btc,
			'hitbtc_eth': hitbtc_eth,
			'hitbtc_others': hitbtc_others,
			'fatbtc_btc': fatbtc_btc,
			'fatbtc_eth': fatbtc_eth,
			'fatbtc_others': fatbtc_others,
			'okex_btc': okex_btc,
			'okex_eth': okex_eth,
			'okex_others': okex_others,
			'kraken_btc': kraken_btc,
			'kraken_eth': kraken_eth,
			'kraken_others': kraken_others }

	def signed_request(self, apiKey, secret, ts) :		
		hash = hashlib.md5()
		params = { 'timestamp': ts, 'apiKey': apiKey, 'apiSecret': secret }
		keys = sorted(params.keys())
		line = ''
		for key in keys:
			line = line + params[key]
		hash.update(line.encode('utf-8'))
		signed = hash.hexdigest()
		return signed

api.add_resource(Main, '/')
api.add_resource(Balance, '/balance')
api.add_resource(Multi, '/multi/<int:num>')

async def run():
	await get_wallets()

t = asyncio.ensure_future(run())
asyncio.get_event_loop().run_until_complete(t)
 
if __name__ == '__main__':
	app.run(debug=True)
		