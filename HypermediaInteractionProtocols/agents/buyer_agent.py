from bspl.adapter import MetaAdapter
from bspl.protocol import Message
from helpers import *
import time

logger = logging.getLogger("buyer")
NAME = "BuyerAgent"
WEB_ID = 'http://localhost:8011'
BAZAAR_URI = 'http://localhost:8080/workspaces/bazaar/'
SELF = [('127.0.0.1',8011)]

adapter = MetaAdapter(name=NAME, systems={}, agents={NAME: SELF}, debug=False)

def get_body_metadata():
    return f"""
    @prefix td: <https://www.w3.org/2019/wot/td#>.
    @prefix hctl: <https://www.w3.org/2019/wot/hypermedia#> .
    @prefix htv: <http://www.w3.org/2011/http#> .

    <#artifact> 
        td:hasActionAffordance [ a td:ActionAffordance;
        td:name "kikoAdapter";
        td:hasForm [
            htv:methodName "GET";
            hctl:hasTarget <http://127.0.0.1:8011/>;
            hctl:forContentType "text/plain";
            hctl:hasOperationType td:invokeAction;
        ]
    ].
    """


@adapter.reaction("RoleNegotiation/Reject")
async def reject_handler(msg: Message):
    adapter.info(f"Role negotiation rejected: {msg}")
    return msg

@adapter.reaction("RoleNegotiation/Accept")
async def role_accepted_handler(msg):
    adapter.info(f"Role proposal accepted: {msg}")
    candidate = msg.meta['system'].split("::")[-1]
    proposed_system = msg['systemName']
    system = adapter.proposed_systems.get_system(proposed_system)
    system.roles[msg['proposedRole']] = candidate

    if system.is_well_formed():
        adapter.info(f"System {proposed_system} is well-formed with roles {system.roles}, sharing details")
        adapter.add_system(proposed_system, system.to_dict())
        await adapter.share_system_details(proposed_system)
    return msg

@adapter.reaction("Buy/Give")
async def give_reaction(msg):
    adapter.info(f"Buy order {msg['buyID']} for item {msg['item']} with amount: {msg['money']}$ successful")
    return msg

async def initiate_protocol(initial_message):
    buy_id = str(int(time.time()))
    item_id = "item123"
    money = 100
    await adapter.send(adapter.messages[initial_message](
        system="BuySystem",
        itemID=item_id,
        buyID=buy_id,
        money=money
    ))

async def main():
    adapter.start_in_loop()
    success, artifact_address = joinWorkspace(BAZAAR_URI,WEB_ID=WEB_ID, AgentName=NAME, metadata=get_body_metadata())
    if not success:
        adapter.logger.error("Could not join the bazaar workspace")
        exit(1)
    protocol = getProtocol(BAZAAR_URI,"Buy")
    adapter.add_protocol(protocol)
    agents = getAgents(BAZAAR_URI, artifact_address)
    for agent in agents:
        adapter.upsert_agent(agent.name, agent.addresses)
    await asyncio.sleep(5)
    adapter.propose_system("BuySystem", {
        "protocol": protocol,
        "roles": {
            "Buyer": NAME,
            "Seller": None
        }
    })
    await adapter.offer_role_for_system("BuySystem", "Seller", "bazaar_agent")
    await asyncio.sleep(5)
    await initiate_protocol("Buy/Pay")
    await asyncio.sleep(5)
    success = leaveWorkspace(BAZAAR_URI,WEB_ID=WEB_ID,AgentName=NAME)
    pass

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
