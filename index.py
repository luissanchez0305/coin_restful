from flask import Flask, request
from flask_restful import Resource, Api
import pymysql
import json
import config
import requests
import asyncio
import struct
#from requests_http_signature import HTTPSignatureAuth
from binance.client import Client as Client_binance
from bfxapi import Client as Client_bitfinex
from bitmex_websocket import BitMEXWebsocket

app = Flask(__name__)
api = Api(app)

db = pymysql.connect(host=config.DATABASE_CONFIG['host'],
		user=config.DATABASE_CONFIG['user'],
		password=config.DATABASE_CONFIG['password'],
		db=config.DATABASE_CONFIG['dbname']
	)

key_bitfinex = config.EXCHANGE_CONFIG['bitfinex_apikey']
pkey_bitfinex = config.EXCHANGE_CONFIG['bitfinex_secret']
bfx = Client_bitfinex(
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

result_btc = 0
result_eth = 0
binance_btc = 0
binance_eth = 0
bitfinex_btc = 0
bitfinex_eth = 0
bitmex_btc = 0
bitmex_eth = 0

#Bitfinex wallets
async def get_wallets() :
	global result_btc
	global result_eth
	global bitfinex_btc
	global bitfinex_eth

	wallets_bitfinex = await bfx.rest.get_wallets()
	for w in wallets_bitfinex :
		if(w.currency == 'BTC') :
			result_btc += float(w.balance)
			bitfinex_btc = float(w.balance)
		if(w.currency == 'ETH') :
			result_eth += float(w.balance)
			bitfinex_eth = float(w.balance)

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
	def get(self):
		global result_btc
		global result_eth	
		global bitmex_btc
		global bitmex_eth

		key_binance = config.EXCHANGE_CONFIG['binance_apikey']
		pkey_binance = config.EXCHANGE_CONFIG['binance_secret']
		client = Client_binance(key_binance, pkey_binance)
		response_binance = client.get_account()
		for coin in response_binance["balances"] :
			if(coin["asset"] == 'BTC') :
				result_btc += float(coin["free"])
				binance_btc = float(coin["free"])
			if(coin["asset"] == 'ETH') :
				result_eth += float(coin["free"])
				binance_eth = float(coin["free"])

		result_btc += float(ws_bitmex_btc.funds()['walletBalance'])
		bitmex_btc = float(ws_bitmex_btc.funds()['walletBalance'])
		result_eth += float(ws_bitmex_eth.funds()['walletBalance'])
		bitmex_eth = float(ws_bitmex_eth.funds()['walletBalance'])

		return { 
			'result_btc': result_btc, 
			'result_eth': result_eth, 
			'binance_btc': binance_btc,
			'binance_eth': binance_eth,
			'bitfinex_btc': bitfinex_btc, 
			'bitfinex_eth': bitfinex_eth,
			'bitmex_btc': bitmex_btc,
			'bitmex_eth': bitmex_eth }

api.add_resource(Main, '/')
api.add_resource(Balance, '/balance')
api.add_resource(Multi, '/multi/<int:num>')

async def run():
	await get_wallets()

t = asyncio.ensure_future(run())
asyncio.get_event_loop().run_until_complete(t)
 
if __name__ == '__main__':
	app.run(debug=True)
		