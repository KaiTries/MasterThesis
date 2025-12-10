"""
Refactored Bazaar Agent (Seller) using HypermediaMetaAdapter.

This demonstrates a simplified seller agent implementation using HypermediaMetaAdapter.
The agent automatically:
- Joins the workspace
- Advertises its capabilities
- Responds to role offers
- Handles protocol messages

Compare with bazaar_agent.py to see the improvements.
"""

from HypermediaMetaAdapter import HypermediaMetaAdapter
from flask import Flask, request
from HypermediaTools import get_model, JACAMO, RDF, HypermediaAgent
import requests
import uuid

# =================================================================
# Configuration
# =================================================================
WORKSPACE_URI = 'http://localhost:8080/workspaces/supermarket/'
NAME = "supermarket_agent"
ADAPTER_PORT = 8013

# Create adapter with hypermedia capabilities
adapter = HypermediaMetaAdapter(
    name=NAME,
    workspace_uri=WORKSPACE_URI,
    web_id=f'http://localhost:{ADAPTER_PORT}',
    adapter_endpoint=str(ADAPTER_PORT),
    capabilities={"Give", "AcceptHandShake"},  # This agent can send Give messages
    debug=True,
    auto_join=True  # Automatically join workspace
)


# =================================================================
# Flask app for WebSub callbacks (Optional)
# =================================================================
app = Flask(__name__)


def flask_thread():
    """Run Flask in background for workspace notifications."""
    app.run(host='localhost', port=8082)


@app.route('/callback', methods=['POST'])
def callback():
    """
    Handle workspace change notifications via WebSub.
    Automatically discovers new agents when they join.
    """
    turtle_data = request.data.decode('utf-8')
    g = get_model(turtle_data)

    # Find new agents in workspace
    agents_local = set()
    for subj in g.subjects(RDF.type, JACAMO.Body):
        # Don't add self
        if 'body_bazaar_agent' not in str(subj):
            agents_local.add(str(subj))

    # Discover and add new agents
    for agent_uri in agents_local:
        add_agent(agent_uri)

    return "OK", 200


def add_agent(agent_body_url: str):
    """
    Parse and add a newly discovered agent.

    Args:
        agent_body_url: URI of the agent's body artifact
    """
    response = requests.get(agent_body_url)
    new_agent = HypermediaAgent(agent_body_url)
    new_agent.parse_agent(response.text)

    if new_agent.name and new_agent.addresses:
        adapter.upsert_agent(new_agent.name, new_agent.addresses)
        adapter.info(f"Auto-discovered agent: {new_agent.name}")


def setup_websub_callback():
    """
    Subscribe to workspace changes via WebSub.
    Returns HTTP status code.
    """
    request_url = "http://localhost:8080/hub/"
    callback_uri = "http://localhost:8082/callback"
    topic = "http://localhost:8080/workspaces/bazaar/artifacts/"

    payload = {
        "hub.callback": callback_uri,
        "hub.mode": "subscribe",
        "hub.topic": topic
    }

    response = requests.post(request_url, json=payload)
    return response.status_code


# =================================================================
# Capabilities - Message handlers
# =================================================================
@adapter.enabled("Buy/Give")
async def send_give(msg):
    """
    Automatically send Give message when enabled after receiving Pay.
    This is the core business logic for the seller.
    """
    adapter.info(f"Received payment for {msg['itemID']}, preparing to send item...")
    # Bind the 'item' parameter with the requested item
    return msg.bind(item=msg['itemID'])

@adapter.enabled("BuyTwo/AcceptHandShake")
async def send_give(msg):
    """
    Automatically send Give message when enabled after receiving Pay.
    This is the core business logic for the seller.
    """
    adapter.info(f"Accepting handshake")
    id = str(uuid.uuid4())
    # Bind the 'item' parameter with the requested item
    return msg.bind(buyID=id)
# =================================================================
# Main Function
# =================================================================
def main():
    """
    Main seller agent logic:
    1. Discover and add Buy protocol
    2. Advertise roles this agent can enact
    3. Start listening for messages
    4. (Optional) Monitor workspace for new agents
    """
    # Discover protocol from workspace
    protocol = adapter.discover_protocol("BuyTwo")
    if not protocol:
        adapter.logger.error("Could not discover Buy protocol")
        adapter.leave_workspace()
        return

    # Advertise which roles we can enact
    adapter.advertise_roles()

    # (Optional) Setup WebSub for automatic agent discovery
    # Uncomment to enable:
    # setup_websub_callback()
    # flask_t = threading.Thread(target=flask_thread, daemon=True)
    # flask_t.start()

    adapter.info("Supermarket agent ready and waiting for buyers...")

    # Start the adapter (blocking)
    adapter.start()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        adapter.info("Shutting down...")
        adapter.leave_workspace()
