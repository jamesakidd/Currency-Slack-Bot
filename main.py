import slack
import os
import json
import re
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, Response
import requests
from slackeventsapi import SlackEventAdapter

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
    if len(params) != 5:
        response = {
            "response_type": "ephemeral",
            "text": "Invalid command, proper usage is: <value> <currency code> = ? <currency code>"
        }
        requests.post(data['response_url'], json=response)

    baseValue = float(re.sub(r'[^\d.]+', '', params[0]))

    exchangeURL = 'https://v6.exchangerate-api.com/v6/{key}/pair/{baseCode}/{exchangeCode}'.format(
        key=os.environ['EXCHANGE_KEY'], baseCode=params[1].upper(), exchangeCode=params[4].upper())
    exchangeDict = json.loads(json.dumps(requests.get(exchangeURL).json()))
    response = {
        "response_type": "in_channel",
        "text": "{baseVal} {baseCurr} is equal to {exVal} {exCurr}".format(baseVal=round(baseValue,2), baseCurr=params[1].upper(), exVal=round(baseValue / exchangeDict["conversion_rate"], 2), exCurr=params[4].upper())
    }
    requests.post(data['response_url'], json=response)

    return ''

if __name__ == "__main__":
    app.run(debug=False)
