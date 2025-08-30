from flask import Flask, request, jsonify
from rdflib import Graph, URIRef
from rdflib.namespace import RDF
import bspl
from bspl.adapter import Adapter
import requests
from agents.utils.helpers import *
# threading and queue for coordination
import threading
import queue
import logging
# Should go into the bazaar and wait there
# Should be subscribed to the bazaar workspace 
# Must maintain his systems and agents table for kiko

JACAMO_BODY = 'https://purl.org/hmas/jacamo/Body'
HMAS_AGENT = 'https://purl.org/hmas/Agent'

BAZAAR = 'http://localhost:8080/workspaces/bazaar'

ME = [('127.0.0.1',8010)]
MY_ROLES = ['Seller']

agents = {}
adapter = None

# Adapter control
adapter = None
adapter_control_queue = queue.Queue()

# Restore agents_in_bazaar
agents_in_bazaar = {}



app = Flask(__name__)

logger = logging.getLogger("agent")

# Instead of running Adapter in a thread, signal main thread to restart it
def request_adapter_restart(new_adapter):
    adapter_control_queue.put(new_adapter)


@app.route('/callback', methods=['POST'])
def callback():
    logger.info(f"Workspace changed - updating agents list")
    global adapter
    global agents
    g = Graph()
    turtle_data = request.data.decode('utf-8')
    g.parse(data=turtle_data, format='turtle')

    agents_local = set()
    for subj in g.subjects(RDF.type, URIRef(JACAMO_BODY)):
        # do not care about own body
        if 'body_bazaar_agent' in str(subj):
            continue
        agents_local.add(str(subj))

    to_remove = set(agents_in_bazaar) - agents_local
    for agent in to_remove:
        agents_in_bazaar.pop(agent)

    for agent in agents_local:
        if agent not in agents_in_bazaar:
            logger.info(f"new agent found: {agent}")
            agents_in_bazaar[agent] = False
            addAgent(agent)
        else:
            logger.info(f'skipping agent {agent}')


    updateAgents(ME, MY_ROLES)
    new_adapter = Adapter('Seller',systems=systems, agents=agents)
    addReactors(new_adapter, protocol)
    request_adapter_restart(new_adapter)
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
    logger.info(f"agent list for MAS: {agents}")
    
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




def flask_thread():
    app.run(host='localhost', port=8082)

if __name__ == '__main__':
    success = joinBazaar()
    success = setupWebsubCallback()
    protocol = getProtocol(BAZAAR, "Buy")
    systems = create_systems_for_protocol(protocol=protocol)
    updateAgents(ME, MY_ROLES)

    # Start Flask in a background thread
    flask_t = threading.Thread(target=flask_thread, daemon=True)
    flask_t.start()

    # Initial Adapter
    adapter = Adapter('Seller', systems=systems, agents=agents)
    addReactors(adapter, protocol)
    while True:
        # Start or restart Adapter as needed
        adapter.start()
        # Wait for a new adapter to be requested
        new_adapter = adapter_control_queue.get()
        print("Restarting Adapter...")
        adapter.stop()
        adapter = new_adapter
        addReactors(adapter,protocol=protocol)
