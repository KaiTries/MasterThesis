from flask import Flask, request, jsonify
from rdflib import Graph, URIRef
from rdflib.namespace import RDF
import bspl
from bspl.adapter import Adapter
import requests
import threading
# Should go into the bazaar and wait there
# Should be subscribed to the bazaar workspace 
# Must maintain his systems and agents table for kiko

JACAMO_BODY = 'https://purl.org/hmas/jacamo/Body'
HMAS_AGENT = 'https://purl.org/hmas/Agent'

buy = bspl.load_file("buy.bspl").export("Buy")
from Buy import Buyer, Seller


agents = {
    "Seller" : [('localhost', 8081)]
}
systems = {
    "Buy": {
        "protocol": buy,
        "roles": {
            Buyer: "Buyer",
            Seller: "Seller"
        }
    }
}


agents_in_bazaar = {}

app = Flask(__name__)


@app.route('/callback', methods=['POST'])
def callback():
    g = Graph()
    turtle_data = request.data.decode('utf-8')
    g.parse(data=turtle_data, format='turtle')

    agents = set()
    for subj in g.subjects(RDF.type, URIRef(JACAMO_BODY)):
        # do not care about own body
        if 'body_bazaar_agent' in str(subj):
            continue
        agents.add(str(subj))

    to_remove = set(agents_in_bazaar) - agents
    for agent in to_remove:
        agents_in_bazaar.pop(agent)

    for agent in agents:
        if agent not in agents_in_bazaar:
            print(f'new agent {agent}')
            agents_in_bazaar[agent] = False
            addAgent(agent)
        else:
            print(f'skipping agent {agent}')


    print(agents_in_bazaar)
    return "OK", 200


def addAgent(agent_body_url):
    response = requests.get(agent_body_url)
    if response.status_code != 200:
        return
    agent_body = Graph()
    agent_body.parse(data=response.content.decode('utf-8'), format='turtle')    

    for subj in agent_body.subjects(RDF.type, URIRef(HMAS_AGENT)):
        split_uri = str(subj).removeprefix('http://').split(':')
        agents_in_bazaar[agent_body_url] = (split_uri[0], split_uri[1])

        agents['Buyer'] = (split_uri[0], int(split_uri[1]))
    



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


def runKiko():
    adapter = Adapter("Seller", systems=systems, agents=agents)

if __name__ == '__main__':
    success = joinBazaar()
    if not success:
        exit(1)
    success = setupWebsubCallback()

    if success == 200:
        app.run(host='localhost', port=8082)
        adapter = Adapter("Seller", systems=systems, agents=agents)

