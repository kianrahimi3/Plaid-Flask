import os
import json
import asyncio
import datetime
from datetime import date
import plaid
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.link_token_transactions import LinkTokenTransactions
from plaid.model.item_get_request import ItemGetRequest
from plaid.model.institutions_get_by_id_request import InstitutionsGetByIdRequest
from plaid.model.transactions_sync_request import TransactionsSyncRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from plaid.model.transfer_create_request import TransferCreateRequest
from plaid.model.transfer_authorization_create_request import TransferAuthorizationCreateRequest
from plaid.model.transfer_type import TransferType
from plaid.model.transfer_network import TransferNetwork
from plaid.model.ach_class import ACHClass
from plaid.model.bank_transfer_user import BankTransferUser
from plaid.model.transfer_authorization_user_in_request import TransferAuthorizationUserInRequest


from flask import Flask, render_template, g, Blueprint, jsonify, request, redirect, url_for

from server import client, PLAID_COUNTRY_CODES

views = Blueprint(__name__, "views")

access_token = None
item_id = None


@views.route("/")
@views.route("/<data>")
def index(data=None):
    return render_template("index.html", data=data)

@views.route("/user-accounts")
async def user_accounts():
    account_data = await get_accounts()
    return render_template("accounts.html", data=account_data)

@views.route("/<account>/transaction-data")
async def transaction_data(account):
    transaction_data = await get_transactions(account)
    return render_template("transactions.html", data=transaction_data)

@views.route("/transfers")
async def transfers(data=None):
    data = request.args.get("data")
    if data is None:
        data = await get_accounts()
    return render_template("transfer.html", data=data)


#server = Blueprint(__name__, "server")

#@server.route("/")
#def index():
    
#    return render_template("test.html")


@views.route("/create_link_token", methods=['POST'])
def create_link_token():
    # Get the client_user_id by searching for the current user
    #user = User.find(...)
    client_user_id = "1234"#user.id

    # Create a link_token for the given user
    request = LinkTokenCreateRequest(
            products=[Products("auth")],
            client_name="Plaid Test App",
            country_codes=[CountryCode('US')],
            #redirect_uri='https://domainname.com/oauth-page.html',
            language='en',
            #webhook='https://webhook.example.com',
            user=LinkTokenCreateRequestUser(
                client_user_id=client_user_id
            )
        )
    response = client.link_token_create(request)

    # Send the data to the client
    return jsonify(response.to_dict())



@views.route('/exchange_public_token', methods=['POST'])
async def exchange_public_token():
    global access_token
    public_token = request.form['public_token']
    item_request = ItemPublicTokenExchangeRequest(
      public_token=public_token
    )
    response = client.item_public_token_exchange(item_request)

    # These values should be saved to a persistent database and
    # associated with the currently signed-in user
    access_token = response['access_token']
    item_id = response['item_id']

    #index(response)
    #return jsonify({'public_token_exchange': 'complete'})
    
    return render_template("index.html", data=response)

    



# Retrieve an Item's accounts
@views.route('/accounts', methods=['GET'])
async def get_accounts():
  global access_token
  try:
      request = AccountsGetRequest(
          access_token=access_token
      )
      response = client.accounts_get(request)
  except plaid.ApiException as e:
      response = json.loads(e.body)
      return jsonify({'error': {'status_code': e.status, 'display_message':
                      response['error_message'], 'error_code': response['error_code'], 'error_type': response['error_type']}})
  
  print(response.to_dict())
  return response.to_dict()
  #return jsonify(response.to_dict())
  #return render_template("index.html", data=response.to_dict())


@views.route('/api/item', methods=['GET'])
def item():
    try:
        request = ItemGetRequest(access_token=access_token)
        response = client.item_get(request)
        request = InstitutionsGetByIdRequest(
            institution_id=response['item']['institution_id'],
            country_codes=list(map(lambda x: CountryCode(x), PLAID_COUNTRY_CODES))
        )
        institution_response = client.institutions_get_by_id(request)
        pretty_print_response(response.to_dict())
        pretty_print_response(institution_response.to_dict())
        return jsonify({'error': None, 'item': response.to_dict()[
            'item'], 'institution': institution_response.to_dict()['institution']})
    except plaid.ApiException as e:
        error_response = format_error(e)
        return jsonify(error_response)
    
import time
async def get_transactions(account):
    response = None
    START_DATE = date(2020, 1, 1)
    END_DATE = datetime.datetime.now().date()
    num_retries = 20

    account_list = []
    account_list.append(account)

    for i in range(num_retries):
        try:
            options = TransactionsGetRequestOptions(
                account_ids=account_list
            )
            """
                if count is not None:
                    options.count = count
                if offset is not None:
                    options.offset = offset
                if account_ids is not None:
                    options.account_ids = account_ids
            """
            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=START_DATE,
                end_date=END_DATE,
                options=options
                
            )
            response = client.transactions_get(request)
        
        except plaid.ApiException as e:
            response = json.loads(e.body)
            if response['error_code'] == 'PRODUCT_NOT_READY':
                time.sleep(5)
                continue
            else:
                raise e
        break
    return response

from_account = None
to_account = None

@views.route("/transfer-money", methods=["POST"])
def transfer_money():
    data = transfer_authorization_create()
    if data["decision"]:
        if data['decision'] == 'approved':
            data = transfer_create_request(data["id"])
            return redirect( url_for('views.transfers', data=data) )

    data = {"decision": "not approved"}
    return redirect( url_for('views.transfers', data=data) )

@views.route("/transfer/authorization/create")
def transfer_authorization_create():
    global from_account
    global to_account
    from_account = request.form.get('from')
    to_account = request.form.get('to')
    amount = request.form.get("amount")
    #recurring = request.form.get("recurring")

    api_request = TransferAuthorizationCreateRequest(
        access_token=access_token,
        account_id=to_account,
        type=TransferType("debit"),
        network=TransferNetwork("ach"),
        amount=amount,
        user=TransferAuthorizationUserInRequest(legal_name='Kian Rahimi'),
        ach_class=ACHClass("ccd")
    )
    response = client.transfer_authorization_create(api_request)
    
    return response["authorization"].to_dict()

@views.route("/transfer/create")
def transfer_create_request(auth_id):
    global access_token
    global to_account
    #to_account = request.form.get("to")

    request = TransferCreateRequest(
        access_token=access_token,
        account_id=to_account,
        authorization_id=auth_id,
        description="payment"
    )
    response = client.transfer_create(request)
    return response["transfer"]


"""
@views.route('/api/transfer/create', methods=['POST'])
def transfer_create():
    global access_token
    request = TransferCreateRequest(
        access_token=access_token,
        account_id=,
        authorization_id=,
        description=,
    )
    response = client.transfer_create(request)
    transfer = response["transfer"]

    return "hello"
"""



def pretty_print_response(response):
  print(json.dumps(response, indent=2, sort_keys=True, default=str))

def format_error(e):
    response = json.loads(e.body)
    return {'error': {'status_code': e.status, 'display_message':
                        response['error_message'], 'error_code': response['error_code'], 'error_type': response['error_type']}}