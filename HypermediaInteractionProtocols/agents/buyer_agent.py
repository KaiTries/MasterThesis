from bspl.adapter import MetaAdapter
from bspl.protocol import Message
from helpers import *
from semantics_helper import *
import time

# =================================================================
# Configuration
# =================================================================
NAME = "BuyerAgent"
WEB_ID = 'http://localhost:8011'
BAZAAR_URI = 'http://localhost:8080/workspaces/bazaar/'
GOAL_ITEM = 'http://localhost:8080/workspaces/bazaar/artifacts/rug#artifact'
SELF = [('127.0.0.1',8011)]

adapter = MetaAdapter(name=NAME, systems={}, agents={NAME: SELF}, capabilities={"Pay",}, debug=False)

def get_body_metadata():
    return f"""
    @prefix td: <https://www.w3.org/2019/wot/td#>.
    @prefix hctl: <https://www.w3.org/2019/wot/hypermedia#> .
    @prefix htv: <http://www.w3.org/2011/http#> .

    <#artifact> 
        td:hasActionAffordance [ a td:ActionAffordance;
        td:name "sendMessage";
        td:hasForm [
            htv:methodName "GET";
            hctl:hasTarget <http://127.0.0.1:8011/>;
            hctl:forContentType "text/plain";
            hctl:hasOperationType td:invokeAction;
        ]
    ].
    """




# =================================================================
# Capabilities
# Here we write the messages that the agent can handle
# It is possible to just bind to messages without also binding to protocols
# e.g. just to "Give" and not "Buy/Give". TODO: not fully tested yet.
# =================================================================
@adapter.reaction("Give")
async def give_reaction(msg):
    adapter.info(f"Buy order {msg['buyID']} for item {msg['item']} with amount: {msg['money']}$ successful")
    return msg

# =================================================================
# Function that returns needed parameters to execute the first message of the buy protocol
# Currently these mappings are known but could be found in the hypermedia space as well
# TODO: Agent should learn this from somewhere
# =================================================================
def generate_buy_params(system_id: str, item_name: str, money: int):
    return {
        "system" : system_id,
        "itemID" : item_name,
        "buyID" : str(int(time.time())),
        "money" : money
    }


# =================================================================
# Main function - Buyer Agent Logic
# 1. The agent joins the bazaar workspace
# 2. The agent gets the protocol needed from goal item
#    TODO: currently given goal item directly
# 3. The agent adds the protocol to its known protocols (not as a system simply as a protocol)
# 4. The agent gets the agents present in the workspace and adds them to its address book
# 5. The agent proposes a system with itself as Buyer and the rest of the roles unassigned
#    TODO: Should be part of MetaAdapter. If we have semantics that give us our role we can use that.
# 6. The agent offers the Seller role to all agents present in the workspace that can enact it
# 7. If the system is well-formed (i.e. all roles assigned and we shared system details) we initiate the protocol
#    TODO: Should be part of MetaAdapter. Need info on initial message to send
# 8. The agent leaves the workspace and shuts down
# =================================================================
async def main():
    adapter.start_in_loop()
    success, artifact_address = join_workspace(BAZAAR_URI, web_id=WEB_ID, agent_name=NAME, metadata=get_body_metadata())
    if not success:
        adapter.logger.error("Could not join the bazaar workspace")
        success = leave_workspace(BAZAAR_URI, web_id=WEB_ID, agent_name=NAME)
        adapter.info(f"Left bazaar workspace - {success}")
        exit(1)
    adapter.info(f"Successfully joined workspace, received artifact uri - {artifact_address}")

    protocol_name = get_protocol_name_from_goal_two(BAZAAR_URI, GOAL_ITEM)
    if protocol_name is None:
        adapter.logger.error(f"No protocol found for goal item {GOAL_ITEM}")
        leave_workspace(BAZAAR_URI, web_id=WEB_ID, agent_name=NAME)
        adapter.info(f"Left bazaar workspace - {success}")
        exit(1)
    adapter.info(f"Found protocol {protocol_name} for goal item {GOAL_ITEM}")

    protocol = get_protocol(BAZAAR_URI, protocol_name)
    adapter.add_protocol(protocol)

    agents = get_agents(BAZAAR_URI, artifact_address)
    for agent in agents:
        adapter.upsert_agent(agent.name, agent.addresses)
    await asyncio.sleep(5)

    system_dict = {
        "protocol": protocol,
        "roles": {
        "Buyer": NAME,
        "Seller": None
        }
    }
    proposed_system_name = adapter.propose_system("BuySystem", system_dict)
    await adapter.offer_roles(system_dict, proposed_system_name, agents)

    # TODO: avoid infinite loop when all candidate reject
    # while not adapter.proposed_systems.get_system(proposed_system_name).is_well_formed():
    #  adapter.info("System not well-formed, cannot initiate protocol")
    #   await asyncio.sleep(5)

    await asyncio.sleep(5)
    if adapter.proposed_systems.get_system(proposed_system_name).is_well_formed():
        await asyncio.sleep(5)
        await adapter.initiate_protocol("Buy/Pay", generate_buy_params(proposed_system_name, "rug", 10))
        await asyncio.sleep(5)
        await adapter.initiate_protocol("Buy/Pay", generate_buy_params(proposed_system_name, "rug", 20))
        await asyncio.sleep(5)
    else:
        adapter.info("System not well-formed, cannot initiate protocol")
    success = leave_workspace(BAZAAR_URI, web_id=WEB_ID, agent_name=NAME)
    pass

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
