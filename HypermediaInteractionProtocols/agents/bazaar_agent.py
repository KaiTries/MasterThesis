from flask import Flask, request, jsonify
from rdflib import Graph, URIRef
from rdflib.namespace import RDF
import bspl
from bspl.adapter import Adapter
import requests
from helpers import getProtocol
# Should go into the bazaar and wait there
# Should be subscribed to the bazaar workspace 
# Must maintain his systems and agents table for kiko

JACAMO_BODY = 'https://purl.org/hmas/jacamo/Body'
HMAS_AGENT = 'https://purl.org/hmas/Agent'

BAZAAR = 'http://localhost:8080/workspaces/bazaar'

ME = [('127.0.0.1',8010)]
MY_ROLES = ['Seller']

agents_in_bazaar = {}
agents = {}



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
    updateAgents(ME, MY_ROLES)
    return "OK", 200


def addAgent(agent_body_url):
    response = requests.get(agent_body_url)
    if response.status_code != 200:
        return
    agent_body = Graph()
    agent_body.parse(data=response.content.decode('utf-8'), format='turtle')    

    for subj in agent_body.subjects(RDF.type, URIRef(HMAS_AGENT)):
        split_uri = str(subj).removeprefix('http://').split(':')
        agents_in_bazaar[agent_body_url] = (split_uri[0], int(split_uri[1]))




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
        protocol.name : {
            "protocol": protocol,
            "roles" : {}
        }
    }


def updateAgents(me, my_roles):
    agents.clear()
    for role in my_roles:
        agents[role] = me

    for agent in agents_in_bazaar:
        agents['Buyer'] = agents_in_bazaar[agent]
    print(agents)
    
def updateRoles(protocol, systems):
    for role in protocol.roles:
        systems[protocol.name]["roles"][protocol.roles[role]] = role





def addReactors(adapter, protocol):
    async def give(msg):
        print(f"Received buy oder for {msg['buyID']} for a {msg['itemID']}")
        await adapter.send(protocol.module.Give(
            item=msg['itemID'],
            **msg.payload
        ))
    adapter.reaction(protocol.module.Pay)(give)



if __name__ == '__main__':
    success = joinBazaar()
    success = setupWebsubCallback()
    protocol = getProtocol(BAZAAR).export('Buy')
    systems = setSystems(protocol=protocol)
    updateAgents(ME, MY_ROLES)
    updateRoles(protocol,systems)
    print(systems)
    print(agents)
    adapter = Adapter('Seller',systems=systems, agents=agents)
    addReactors(adapter, protocol)

    if success == 200:
        app.run(host='localhost', port=8082)
        adapter.start()
