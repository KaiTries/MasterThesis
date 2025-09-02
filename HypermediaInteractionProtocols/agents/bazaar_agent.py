from flask import Flask, request, jsonify
from rdflib import Graph, URIRef
from rdflib.namespace import RDF
from bspl.adapter import Adapter, MetaAdapter
import requests
# threading and queue for coordination
import threading
import logging
from helpers import *
# Should go into the bazaar and wait there
# Should be subscribed to the bazaar workspace 
# Must maintain his systems and agents table for kiko

JACAMO_BODY = 'https://purl.org/hmas/jacamo/Body'
HMAS_AGENT = 'https://purl.org/hmas/Agent'
BAZAAR = 'http://localhost:8080/workspaces/bazaar'

ME = [('127.0.0.1',8010)]
NAME = "BazaarAgent"
agents = {NAME : ME}
adapter = MetaAdapter(NAME, systems={}, agents=agents, debug=True)
logger = logging.getLogger("BazaarAgent")
app = Flask(__name__)

@adapter.reaction("Buy/Pay")
async def give(msg):
        print(f"Received buy oder for {msg['buyID']} for a {msg['itemID']}")
        await adapter.send(adapter.protocols["Buy"].messages["Give"](
            item=msg['itemID'],
            **msg.payload
        )
        )
        return msg

@app.route('/callback', methods=['POST'])
def callback():
    logger.info(f"Workspace changed - updating agents list")
    global adapter
    g = Graph()
    turtle_data = request.data.decode('utf-8')
    g.parse(data=turtle_data, format='turtle')

    agents_local = set()
    for subj in g.subjects(RDF.type, URIRef(JACAMO_BODY)):
        # do not care about own body
        if 'body_bazaar_agent' in str(subj):
            continue
        agents_local.add(str(subj))


    for agent in agents_local:
        addAgent(agent)


    return "OK", 200


def addAgent(agent_body_url):
    response = requests.get(agent_body_url)
    new_agent = Agent(agent_body_url)
    new_agent.parse_agent(response.text)
    print(new_agent)
    adapter.upsert_agent(agent_body_url, new_agent.addresses)



def setupWebsubCallback():
    requestUrl = "http://localhost:8080/hub/"

    callback = "http://localhost:8082/callback"
    topic = "http://localhost:8080/workspaces/bazaar/artifacts/"
    mode = "subscribe"

    payload = {
        "hub.callback": callback,
        "hub.mode": mode,
        "hub.topic": topic
    }

    response = requests.post(requestUrl, json=payload)
    return response.status_code


def joinBazaar():
    return True


def setSystems(protocol):
    return {
        protocol.name: {
            "protocol": protocol,
            "roles": {}
        }
    }





def flask_thread():
    app.run(host='localhost', port=8082)

if __name__ == '__main__':
    success = joinBazaar()
    success = setupWebsubCallback()

    # Start Flask in a background thread
    flask_t = threading.Thread(target=flask_thread, daemon=True)
    flask_t.start()
    adapter.start()

