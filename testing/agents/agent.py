from MetaAdapter import MetaAdapter



class Agent:
    def __init__(self, name, addresses):
        self.name = name
        self.addresses = addresses
        self.adapter = MetaAdapter(name=name, systems={}, agents={name: addresses})

    async def offer_role(self):
        await self.adapter.offer_role()



    def start_in_loop(self):
        print(f"[{self.name}] Starting agent with addresses: {self.addresses}")
        self.adapter.start_in_loop()


    def stop(self):
        print(f"[{self.name}] Stopping agent.")
        return self.adapter.stop()