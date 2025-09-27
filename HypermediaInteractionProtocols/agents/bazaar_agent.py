from flask import Flask, request, jsonify
from bspl.adapter import Adapter, MetaAdapter
import threading
from helpers import *

# =================================================================
# Configuration
# =================================================================
JACAMO_BODY = 'https://purl.org/hmas/jacamo/Body'
HMAS_AGENT = 'https://purl.org/hmas/Agent'
BAZAAR = 'http://localhost:8080/workspaces/bazaar'

ME = [('127.0.0.1',8010)]
NAME = "BazaarAgent"
agents = {NAME : ME}
adapter = MetaAdapter(NAME, systems={}, agents=agents, debug=True)

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
    for subj in g.subjects(RDF.type, URIRef(JACAMO_BODY)):
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
# Meta Adapter Configuration
# We need to write the reactions for role negotiation ourselves
# since the decision is up to agent's policy
# We do not need to write the initial message sending code
# since it is already implemented
# in the MetaAdapter class.
#
# This agent accepts all role offers if he knows the protocol
# =================================================================
@adapter.reaction("RoleNegotiation/OfferRole")
async def offer_role_reaction(msg):
    proposed_protocol = msg['protocolName']
    if proposed_protocol in msg.adapter.protocols:
        adapter.info(f"Accepting role proposal: {msg}")
        await adapter.send(
            adapter.meta_protocol.messages["Accept"](
                uuid=msg['uuid'],
                system=msg.system,
                protocolName=msg['protocolName'],
                systemName=msg['systemName'],
                proposedRole=msg['proposedRole'],
                accept=True,
            )
        )
    else:
        adapter.info(f"Rejecting role proposal: {msg}")
        await adapter.send(
            adapter.meta_protocol.messages["Reject"](
                uuid=msg['uuid'],
                system=msg.system,
                protocolName=msg['protocolName'],
                systemName=msg['systemName'],
                proposedRole=msg['proposedRole'],
                reject=True,
            )
        )
    return msg

@adapter.reaction("RoleNegotiation/SystemDetails")
async def system_details_handler(msg ):
    adapter.info(f"Received system details: {msg}")
    system = msg['enactmentSpecs']
    system['protocol'] = adapter.protocols[msg['protocolName']]
    adapter.add_system(msg['systemName'],system)
    return msg


# =================================================================
# Capabilities
# Here we write the messages that the agent can handle
# It is possible to just bind to messages without also binding to protocols
# e.g. just to "Give" and not "Buy/Give". TODO: not fully tested yet.
# =================================================================
@adapter.reaction("Buy/Pay")
async def give(msg):
        adapter.info(f"Received buy oder for {msg['buyID']} for a {msg['itemID']}")
        await adapter.send(adapter.messages["Buy/Give"](
            item=msg['itemID'],
            **msg.payload
        )
        )
        return msg




# =================================================================
# Main function - Seller Agent Logic
# 1. Join Bazaar
#      In this case just return True because we already added its body via the config file for the environment
#      Just to showcase that that could work as well (check buyer for actual joining)
# 2. Setup WebSub callback to monitor changes in the Bazaar workspace
#      This agent actively monitors its surroundings and automatically adds agents that appear in the workspace
# 3. Add the Buy protocol to the adapter
# 4. Start Flask in a background thread to handle WebSub callbacks
# 5. Start the adapter to listen for incoming messages

# This agent will just sit idle in the bazaar and if someone wants to buy something, it can sell it to them.
# This is achieved through dynamic role binding via the meta protocol and then the agents capability.
# =================================================================
def joinBazaar():
    return True

if __name__ == '__main__':
    success = joinBazaar()
    success = setup_websub_callback()
    protocol = get_protocol(BAZAAR, "Buy")
    adapter.add_protocol(protocol)

    # Start Flask in a background thread
    flask_t = threading.Thread(target=flask_thread, daemon=True)
    flask_t.start()
    adapter.start()

