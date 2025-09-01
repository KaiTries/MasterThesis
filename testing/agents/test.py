import asyncio
import configuration

import agent_a
import agent_b
import agent_c
import agent_d



def buildInitialSystem(protocol: dict) -> dict:
    systemBuilder = configuration.SystemBuilder(protocol_spec=protocol)
    systemBuilder.add_agent_for_role("A", "AgentA")
    systemBuilder.add_agent_for_role("B", "AgentB")
    systemBuilder.add_agent_for_role("C", "AgentC")
    return systemBuilder.build()

def buildEmptySystem(protocol: dict) -> dict:
    systemBuilder = configuration.SystemBuilder(protocol_spec=protocol)
    return systemBuilder.build()

def buildSecondSystem(protocol: dict) -> dict:
    systemBuilder = configuration.SystemBuilder(protocol_spec=protocol)
    systemBuilder.add_agent_for_role("A", "AgentA")
    systemBuilder.add_agent_for_role("B", "AgentB")
    systemBuilder.add_agent_for_role("C", "AgentD")
    return systemBuilder.build()

async def metaProtcolTest():
    agent_a.adapter.start_in_loop()
    agent_b.adapter.start_in_loop()
    agent_c.adapter.start_in_loop()
    await asyncio.sleep(1)

    # assume b and c know the application protocol
    agent_b.adapter.add_protocol(configuration.protocol)
    agent_c.adapter.add_protocol(configuration.protocol)
    # agents find each other
    agent_a.adapter.upsert_agent(agent_b.NAME, agent_b.SELF)
    agent_a.adapter.upsert_agent(agent_c.NAME, agent_c.SELF)
    agent_b.adapter.upsert_agent(agent_a.NAME, agent_a.SELF)
    agent_c.adapter.upsert_agent(agent_a.NAME, agent_a.SELF)
    agent_b.adapter.upsert_agent(agent_c.NAME, agent_c.SELF)
    agent_c.adapter.upsert_agent(agent_b.NAME, agent_b.SELF)

    await asyncio.sleep(1)
    async def initiate_protocol(id, item):
        await agent_a.adapter.send(
            configuration.protocol.messages["GiveItem"](
                id=id,
                item=item
            )
        )

    # Agent a creates a protocol system that achieves its goals
    proposed_system = configuration.SystemBuilder(protocol_spec=configuration.protocol)
    proposed_system.add_agent_for_role("A", "AgentA") # itself
    system_name = agent_a.adapter.propose_system("ProtocolInstanceX", proposed_system.build())

    # Agent a offers roles to other agents
    await agent_a.adapter.offer_role_for_system(system_name,"B", agent_b.NAME)
    await agent_a.adapter.offer_role_for_system(system_name,"C", agent_c.NAME)


    await asyncio.sleep(4)

    # agent a can now initiate the protocol
    await initiate_protocol(1, 'apple')

    await asyncio.sleep(4)







async def timeline():
    print("======================================================")
    print("Short demo showcasing handling of dynamic environments")
    print("======================================================")

    agent_a.adapter.start_in_loop()
    agent_b.adapter.start_in_loop()
    agent_c.adapter.start_in_loop()

    system = buildInitialSystem(configuration.protocol)

    agent_a.adapter.add_system("Protocol1", system)
    agent_b.adapter.add_system("Protocol1", system)
    agent_c.adapter.add_system("Protocol1", system)

    agent_a.adapter.upsert_agent("AgentB", agent_b.SELF)
    agent_a.adapter.upsert_agent("AgentC", agent_c.SELF)

    agent_b.adapter.upsert_agent("AgentA", agent_a.SELF)
    agent_b.adapter.upsert_agent("AgentC", agent_c.SELF)

    agent_c.adapter.upsert_agent("AgentA", agent_a.SELF)
    agent_c.adapter.upsert_agent("AgentB", agent_b.SELF)

    await  asyncio.sleep(1)

    async def initiate_protocol(id, item):
        await agent_a.adapter.send(
            configuration.protocol.messages["GiveItem"](
                id=id,
                item=item
            )
        )

    await initiate_protocol(1, 'apple')

    await asyncio.sleep(5)

    print("============================================")
    await agent_c.adapter.stop()
    if True:
        await asyncio.sleep(1)

        secondSystem = buildSecondSystem(configuration.protocol)
        agent_d.adapter.start_in_loop()

        agent_d.adapter.add_system("Protocol1", secondSystem)
        agent_d.adapter.upsert_agent("AgentA", agent_a.SELF)
        agent_d.adapter.upsert_agent("AgentB", agent_b.SELF)
        agent_a.adapter.upsert_agent("AgentD", agent_d.SELF)
        agent_b.adapter.upsert_agent("AgentD", agent_d.SELF)

        agent_a.adapter.reassign_role("Protocol1","C", "AgentD")
        agent_b.adapter.reassign_role("Protocol1", "C", "AgentD")

        await asyncio.sleep(1)

        await initiate_protocol(2, 'ball')

        await asyncio.sleep(5)

if __name__ == '__main__':
    # asyncio.run(timeline())
    asyncio.run(metaProtcolTest())
