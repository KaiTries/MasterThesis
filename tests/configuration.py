import bspl

protocol_sp = bspl.load_file('protocol.bspl')
protocol = protocol_sp.protocols['Protocol']

role_negotiation_sp = bspl.load_file('RoleNegotiation.bspl')
role_negotiation = role_negotiation_sp.protocols['RoleNegotiation']


# build up system for a protocol
# returns valid system for specific protocol instantiation
class SystemBuilder:
    def __init__(self, protocol_spec):
        self.protocol = protocol_spec
        self.system = {}
        self.agents = {}
        self._seed_system()
        self._seed_agents()

    def _seed_system(self):
        self.system = {
            self.protocol.name: {
                "protocol": self.protocol,
                "roles": {

                }
            }
        }

    def _seed_agents(self):
        for role in self.protocol.roles:
            self.system[self.protocol.name]["roles"][role] = None

    def add_agent_for_role(self, role, agent):
        self.system[self.protocol.name]["roles"][role] = agent

    def build(self):
        return self.system[self.protocol.name]