from flask import Flask, render_template
from datetime import datetime, timedelta
import plaid
import os
import dotenv
from plaid.api import plaid_api
from plaid.model.products import Products

from pathlib import Path
from views import views
#from server import server

# add .env variables
def empty_to_none(field):
    value = os.getenv(field)
    if value is None or len(value) == 0:
        return None
    return value

BASE_DIR = Path(__file__).resolve().parent.parent

dotenv_file = os.path.join(BASE_DIR, ".env")
if os.path.isfile(dotenv_file):
    dotenv.load_dotenv(dotenv_file)


CLIENT_ID = os.getenv("PLAID_CLIENT_ID")#os.environ["PLAID_CLIENT_ID"]
SECRET = os.getenv("PLAID_SECRET")#os.environ["PLAID_SECRET"]
COUNTRY_CODES = os.getenv('PLAID_COUNTRY_CODES', 'US').split(',')
PLAID_REDIRECT_URI = empty_to_none('PLAID_REDIRECT_URI')

PLAID_PRODUCTS = os.getenv('PLAID_PRODUCTS', 'transactions').split(',')
PRODUCTS = []
for product in PLAID_PRODUCTS:
    PRODUCTS.append(Products(product))




app = Flask(__name__)
#app.debug = True
app.register_blueprint(views)


if __name__ == "__main__":
    app.run(debug=True)