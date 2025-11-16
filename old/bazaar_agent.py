from flask import Flask, request, jsonify
from bspl.adapter import Adapter, MetaAdapter
import threading
import time
from HypermediaTools import (
    join_workspace,
    leave_workspace,
    get_protocol,
    generate_body_metadata,
    generate_role_metadata,
    update_body,
    get_model,
    HypermediaAgent,
    JACAMO,
    RDF
)
from rdflib import Graph, URIRef
import requests

# =================================================================
# Configuration
# =================================================================
BAZAAR = 'http://localhost:8080/workspaces/bazaar/'
WEB_ID = 'http://localhost:8010'
NAME = "bazaar_agent"
ADAPTER_ENDPOINT = 8010
BODY_METADATA = generate_body_metadata(str(ADAPTER_ENDPOINT))
CAPABILITIES = {"Give",}

# BSPL Adapter own specifications
ME = [('127.0.0.1',ADAPTER_ENDPOINT)] # own address for endpoint
agents = {NAME : ME} # agent address book only know myself
adapter = MetaAdapter(NAME, systems={}, agents=agents, debug=True, capabilities=CAPABILITIES)

# =================================================================
# Flask app for WebSub callback
# =================================================================
app = Flask(__name__)

def flask_thread():
    app.run(host='localhost', port=8082)

@app.route('/callback', methods=['POST'])
def callback():
    global adapter
    # adapter.info(f"Workspace changed - updating agents list")
    g = Graph()
    turtle_data = request.data.decode('utf-8')
    g.parse(data=turtle_data, format='turtle')

    agents_local = set()
    for subj in g.subjects(RDF.type, JACAMO.Body):
        # do not care about own body
        if 'body_bazaar_agent' in str(subj):
            continue
        agents_local.add(str(subj))


    for agent in agents_local:
        add_agent(agent) # not necessary - if we receive role offer through metaprotocol, initiator is added

    return "OK", 200

def add_agent(agent_body_url):
    response = requests.get(agent_body_url)
    new_agent = HypermediaAgent(agent_body_url)
    new_agent.parse_agent(response.text)
    if new_agent.name is None or len(new_agent.addresses) == 0:
        print("Agent Description not complete, not adding to known agents")
        return
    adapter.upsert_agent(new_agent.name, new_agent.addresses)

def setup_websub_callback():
    request_url = "http://localhost:8080/hub/"

    callback_uri = "http://localhost:8082/callback"
    topic = "http://localhost:8080/workspaces/bazaar/artifacts/"
    mode = "subscribe"

    payload = {
        "hub.callback": callback_uri,
        "hub.mode": mode,
        "hub.topic": topic
    }

    response = requests.post(request_url, json=payload)
    return response.status_code


# =================================================================
# Capabilities
# Here we write the messages that the agent can handle
# It is possible to just bind to messages without also binding to protocols
# e.g. just to "Give" and not "Buy/Give". TODO: not fully tested yet.
# =================================================================
#@adapter.reaction("Pay")
async def give(msg):
        adapter.info(f"Received buy oder for {msg['buyID']} for a {msg['itemID']}")
        await adapter.send(adapter.messages["Buy/Give"](
            item=msg['itemID'],
            **msg.payload
        )
        )
        return msg

@adapter.enabled("Buy/AcceptHandShake")
async def send_accept_handshake(msg):
    adapter.info(f"Received handshake for {msg['firstID']}")
    return msg.bind(buyID=str(int(time.time())))


@adapter.enabled("Buy/Give")
async def send_give(msg):
        adapter.info(f"Received buy oder for {msg['buyID']} for a {msg['itemID']}")
        return msg.bind(item=msg['itemID'])


# =================================================================
# Main function - Seller Agent Logic
# 1. Join Bazaar
# 2. NOT ACTIVATED (uncomment line 112) Setup WebSub callback to monitor changes in the Bazaar workspace
#      This agent actively monitors its surroundings and automatically adds agents that appear in the workspace
# 3. Add the Buy protocol to the adapter
# 4. Start Flask in a background thread to handle WebSub callbacks
# 5. Start the adapter to listen for incoming messages
if __name__ == '__main__':
    code, address = join_workspace(BAZAAR, web_id=WEB_ID, agent_name=NAME, metadata=BODY_METADATA)
    if not code:
        adapter.logger.error("Could not join the bazaar workspace")
        success = leave_workspace(BAZAAR, web_id=WEB_ID, agent_name=NAME)
        adapter.info(f"Left bazaar workspace - {code}")
        exit(1)

    # success = setup_websub_callback() # uncomment for automatically adding new agents in env

    protocol = get_protocol(BAZAAR)
    new_roles = adapter.add_protocol(protocol)

    roles_rdf = generate_role_metadata(address, new_roles, protocol.name)
    response = update_body(address, web_id=WEB_ID, agent_name=NAME, metadata=roles_rdf)

    # Start Flask in a background thread
    flask_t = threading.Thread(target=flask_thread, daemon=True)
    flask_t.start()
    adapter.start()

