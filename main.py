import slack
import os
import json
import re
import requests
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
from slackeventsapi import SlackEventAdapter
from babel.numbers import get_currency_symbol

print('bot running')
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(
    os.environ['SIGNING_SECRET'], '/slack/events', app)
client = slack.WebClient(token=os.environ['SLACK_TOKEN'])
BOT_ID = client.api_call("auth.test")['user_id']


@app.route('/currency', methods=['POST'])
def currency():
    data = request.form
    params = data.get('text').split()
    response = {}
    if (len(params) != 5 or params[2] != '=' or params[3] != '?'):
        response = {
            "response_type": "ephemeral",
            "text": "Invalid command, proper usage is: <value> <currency code> = ? <currency code>"
        }
        requests.post(data['response_url'], json=response)
        return ''

    try:
        baseCurrency = params[1].upper()
        convertCurrency = params[4].upper()
        baseSymbol = get_currency_symbol(baseCurrency, locale='en_US')
        exchangeSymbol = get_currency_symbol(convertCurrency, locale='en_US')
        baseValue = float(re.sub(r'[^\d.]+', '', params[0]))
    except:
        response = {
            "response_type": "ephemeral",
            "text": "Invalid command, '{}' is not a valid value".format(params[0])
        }
        requests.post(data['response_url'], json=response)
        return ''

    exchangeURL = 'https://v6.exchangerate-api.com/v6/{key}/pair/{baseCode}/{exchangeCode}'.format(
        key=os.environ['EXCHANGE_KEY'], baseCode=baseCurrency, exchangeCode=convertCurrency)
    exchangeDict = json.loads(json.dumps(requests.get(exchangeURL).json()))    

    if(exchangeDict["result"] == "error" ):
        response = {
            "response_type": "ephemeral",
            "text": exchangeDict["error-type"]
        }
        requests.post(data['response_url'], json=response)

    else:
        conRate = exchangeDict["conversion_rate"]
        exchangeValue = baseValue * conRate

        response = {
            "response_type": "in_channel",
            "text": "{baseVal} {baseCurr} is equal to {exVal} {exCurr}".format(
            baseVal="{sym}{baseVal:,.2f}".format(sym= baseSymbol,baseVal=baseValue), 
            baseCurr=baseCurrency, exVal="{exSym}{exval:,.2f}".format(exSym=exchangeSymbol, 
            exval=exchangeValue),
            exCurr=convertCurrency)
        }
        requests.post(data['response_url'], json=response)

    return ''

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=5000)
