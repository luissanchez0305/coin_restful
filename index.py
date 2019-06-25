from flask import Flask, request
from flask_restful import Resource, Api
import pymysql
import json
import config

app = Flask(__name__)
api = Api(app)

db = pymysql.connect(host=config.DATABASE_CONFIG['host'],
	user=config.DATABASE_CONFIG['user'],
	password=config.DATABASE_CONFIG['password'],
	db=config.DATABASE_CONFIG['dbname'])

class Coins(Resource):
	def get(self):
		cursor = db.cursor()
		cursor.execute("SELECT * FROM arbitrage_processes")
		row_headers=[x[0] for x in cursor.description] #this will extract row headers
		numrows = cursor.rowcount
		rv = cursor.fetchall()
		coins = []
		for i in rv:
			coins.append(dict(zip(row_headers,i)))

		return json.dumps(coins, indent=4, sort_keys=True, default=str)

	def post(self):
		some_json = request.get_json()
		return {'you sent': some_json}, 201

class Multi(Resource):	
	def get(self, num):
		return {'result': num*10}

api.add_resource(Coins, '/')
api.add_resource(Multi, '/multi/<int:num>')

if __name__ == '__main__':
	app.run(debug=True)
		