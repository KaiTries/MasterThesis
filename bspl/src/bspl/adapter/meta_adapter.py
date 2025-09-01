from .core import Adapter
from .system_store import SystemStore, System
from .. import load
import uuid

role_negotiation_protocol = """
RoleNegotiation {
    roles Initiator, Candidate
    parameters, out protocolName key, out systemName key, out sender, out proposedRole, out accept, out reject, out enactmentSpecs

    Initiator -> Candidate: OfferRole[out protocolName key , out systemName key, out sender, out proposedRole]

    Candidate -> Initiator: Accept[in protocolName key, in systemName key, in proposedRole, out accept]
    Candidate -> Initiator: Reject[in protocolName key, in systemName key, in proposedRole, out reject]

    Initiator -> Candidate: SystemDetails[in protocolName key, in systemName key, in accept, out enactmentSpecs]
}
"""


role_negotiation_sp = load(role_negotiation_protocol)
role_negotiation = role_negotiation_sp.protocols['RoleNegotiation']


def get_system_for_meta_protocol(initiator, candidate):
    system = {
            "protocol": role_negotiation,
            "roles": {
                "Initiator": initiator,
                "Candidate": candidate
            }
        }
    return system


def new_uuid():
    return str(uuid.uuid4())


class MetaAdapter(Adapter):
    meta_protocol = role_negotiation

    def __init__(self, name, systems=None, agents=None, debug=False):
        super().__init__(name=name, systems=systems, agents=agents, debug=debug)
        self.proposed_systems = SystemStore({})
        self.negotiations_proposed_systems_map = {}  # map of proposed system name to negotiation system name

    def propose_system(self, system_name, system_dict):
        if system_name in self.proposed_systems.systems:
            raise ValueError(f"System with name {system_name} already proposed.")
        self.proposed_systems.add_system_dict(system_name, system_dict)
        self.negotiations_proposed_systems_map[system_name] = []
        return system_name

    async def share_system_details(self, system_name):
        """
        At this point the proposed system is well-formed, and we have an agent for all roles
        Now we need to share this with all agents involved
        This means that we finish all the role negotiation protocols
        """
        if system_name not in self.proposed_systems.systems:
            raise ValueError(f"System with name {system_name} not found in proposed systems.")
        system = self.proposed_systems.systems[system_name]
        negotiations = self.negotiations_proposed_systems_map.get(system_name, [])
        for negotiation_system_name in negotiations:
            msg = self.meta_protocol.messages["SystemDetails"](
                system=negotiation_system_name,
                systemName=system_name,
                protocolName=system.protocol.name,
                accept=True,
                enactmentSpecs=system.to_dict_special(),
            )
            await self.send(msg)

    async def offer_role_for_system(self, system_name, role, candidate):
        meta_protocol_system = get_system_for_meta_protocol(self.name, candidate)
        meta_protocol_system_name = f"RoleNegotiation::{role}::{candidate}"
        self.add_system(meta_protocol_system_name, meta_protocol_system)
        self.negotiations_proposed_systems_map[system_name].append(meta_protocol_system_name)

        protocol_name = self.proposed_systems.systems[system_name].protocol.name

        msg = self.meta_protocol.messages["OfferRole"](
            system=meta_protocol_system_name,
            systemName=system_name,
            protocolName=protocol_name,
            sender={"agent": self.name, "address": self.addresses},
            proposedRole=role,
        )
        await self.send(msg)

    async def receive(self, data):
        if not isinstance(data, dict):
            self.warning("Data does not parse to a dictionary: {}".format(data))
            return

        schema = data.get('schema', '')
        if schema.startswith("RoleNegotiation/OfferRole"):
            payload = data.get('payload', {})
            initiator = payload.get('sender', {})
            initiator_name = initiator.get('agent', '')
            initiator_address = initiator.get('address', [])
            sys_id = data.get('meta', {}).get('system','')
            self.upsert_agent(initiator_name, [(initiator_address[0][0], initiator_address[0][1])])
            if sys_id not in self.systems.systems:
                new_system = get_system_for_meta_protocol(initiator_name, self.name)
                self.add_system(sys_id, new_system)

        await super().receive(data)