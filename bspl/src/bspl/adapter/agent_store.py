

# simple data class for the agent
class Agent:
    def __init__(self, name: str, addresses: list[tuple[str, int]]):
        self.name = name
        self.addresses = addresses


# simple in-memory store for agents
# manages adding and updating agents
class AgentStore:
    def __init__(self, agents: dict[str, list[tuple[str, int]]]):
        self.agents = {}
        for name, addresses in agents.items():
            self.agents[name] = Agent(name, addresses)


    def get_agent(self, name: str) -> Agent | None:
        return self.agents.get(name)

    def upsert_agent(self, name: str, addresses: list[tuple[str, int]]) -> Agent:
        if name in self.agents:
            agent = self.agents[name]
            existing_addresses = set(agent.addresses)
            new_addresses = set(addresses)
            combined_addresses = list(existing_addresses.union(new_addresses))
            agent.addresses = combined_addresses
            return agent
        else:
            agent = Agent(name, addresses)
            self.agents[name] = agent
            return agent