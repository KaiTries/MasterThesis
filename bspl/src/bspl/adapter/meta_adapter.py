from bspl.protocol import Message, Protocol

from .core import Adapter
from .system_store import SystemStore, System
from .. import load
import uuid

role_negotiation_protocol = """
RoleNegotiation {
    roles Initiator, Candidate
    parameters, out uuid key, out protocolName key, out systemName key, out sender, out proposedRole, out accept, out reject, out enactmentSpecs

    Initiator -> Candidate: OfferRole[out uuid key, out protocolName key , out systemName key, out sender, out proposedRole]

    Candidate -> Initiator: Accept[in uuid key, in protocolName key, in systemName key, in proposedRole, out accept]
    Candidate -> Initiator: Reject[in uuid key, in protocolName key, in systemName key, in proposedRole, out reject]

    Initiator -> Candidate: SystemDetails[in uuid key, in protocolName key, in systemName key, in accept, out enactmentSpecs]
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


class Negotiation:
    def __init__(self, system_name, uuid):
        self.system_name = system_name
        self.uuid = uuid


class MetaAdapter(Adapter):
    meta_protocol = role_negotiation

    def __init__(self, name, systems=None, agents=None, capabilities=None, debug=False):
        super().__init__(name=name, systems=systems, agents=agents, debug=debug)
        if capabilities is None:
            capabilities = set()
        self.proposed_systems = SystemStore({})
        self.negotiations_proposed_systems_map: dict[str, list[Negotiation]] = {}  # map of proposed system name to negotiation system name
        self.capabilities = capabilities
        self.capable_roles = set()
        self.setup_generic_meta_protocol_handlers()

    ########################################################
    ##########  Meta Protocol Generic Handlers    ##########
    ########################################################
    def reject_handler(self):
        """
        When a Candidate rejects a role offer this function is called
        """
        async def _reject_handler(msg: Message):
            candidate = msg.meta['system'].split("::")[-1]
            # TODO: Need better way to handle reactors correctly
            if candidate == self.name:
                self.info(f"candidate does not need to react to own reject message!")
                return msg
            self.info(f"Role negotiation rejected: {msg}")
            return msg
        return _reject_handler

    def accept_handler(self):
        """
        When a Candidate accepts a role offer this function is called
        """
        async def _accept_handler(msg: Message):
            candidate = msg.meta['system'].split("::")[-1]
            # TODO: Need better way to handle reactors correctly
            if candidate == self.name:
                self.info(f"candidate does not need to react to own accept message!")
                return msg
            self.info(f"Role proposal accepted by {candidate}")
            proposed_system = msg['systemName']
            system = self.proposed_systems.get_system(proposed_system)
            system.roles[msg['proposedRole']] = candidate

            if system.is_well_formed():
                self.info(f"System {proposed_system} is well-formed with roles {system.roles}, sharing details")
                self.add_system(proposed_system, system.to_dict())
                await self.share_system_details(proposed_system)
            return msg
        return _accept_handler

    def role_proposal_handler(self):
        """
        When a Candidate receives a role offer this function is called
        Currently accepts a role if we are capable
        """
        async def _role_proposal_handler(msg: Message):
            candidate = msg.meta['system'].split("::")[-1]
            # TODO: Need better way to handle reactors correctly
            if candidate != self.name:
                self.info(f"Initiator doesnt answer own message!")
                return msg
            proposed_role = msg['proposedRole']
            if proposed_role in self.capable_roles:
                self.info(f"Accepting role proposal: {msg}")
                await self.send(
                    self.meta_protocol.messages["Accept"](
                        uuid=msg['uuid'],
                        system=msg.system,
                        protocolName=msg['protocolName'],
                        systemName=msg['systemName'],
                        proposedRole=msg['proposedRole'],
                        accept=True,
                    )
                )
            else:
                self.info(f"Rejecting role proposal: {msg}")
                await self.send(
                    self.meta_protocol.messages["Reject"](
                        uuid=msg['uuid'],
                        system=msg.system,
                        protocolName=msg['protocolName'],
                        systemName=msg['systemName'],
                        proposedRole=msg['proposedRole'],
                        reject=True,
                    )
                )
            return msg
        return _role_proposal_handler

    def system_details_handler(self):
        """
        When a candidate receives a system details message this function is called
        """
        async def _system_details_handler(msg: Message):
            candidate = msg.meta['system'].split("::")[-1]
            # TODO: Need better way to handle reactors correctly
            if candidate != self.name:
                self.info(f"Initiator already knows system details")
                return msg
            self.info(f"Received system details: {msg}")
            system = msg['enactmentSpecs']
            system['protocol'] = self.protocols[msg['protocolName']]
            self.add_system(msg['systemName'], system)
            return msg

        return _system_details_handler

    def setup_generic_meta_protocol_handlers(self):
        self.reactors["RoleNegotiation/Reject"] = [self.reject_handler()]
        self.reactors["RoleNegotiation/Accept"] = [self.accept_handler()]
        self.reactors["RoleNegotiation/OfferRole"] = [self.role_proposal_handler()]
        self.reactors["RoleNegotiation/SystemDetails"] = [self.system_details_handler()]

    def propose_system(self, system_name, system_dict) -> str:
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
        for negotiation in negotiations:
            msg = self.meta_protocol.messages["SystemDetails"](
                uuid=negotiation.uuid,
                system=negotiation.system_name,
                systemName=system_name,
                protocolName=system.protocol.name,
                accept=True,
                enactmentSpecs=system.to_dict_special(),
            )
            await self.send(msg)


    async def initiate_protocol(self, initial_message, params: dict):
        await self.send(self.messages[initial_message](**params))

    async def offer_roles(self, proposed_system, proposed_system_name, agents):
        for role, agent_name in proposed_system['roles'].items():
            if agent_name is None:
                for agent in agents:
                    if role in agent.roles:
                        await self.offer_role_for_system(proposed_system_name, role, agent.name)

    async def offer_role_for_system(self, system_name, role, candidate):
        meta_protocol_system = get_system_for_meta_protocol(self.name, candidate)
        meta_protocol_system_name = f"RoleNegotiation::{role}::{candidate}"
        negotiation_id = new_uuid()

        self.add_system(meta_protocol_system_name, meta_protocol_system)
        self.negotiations_proposed_systems_map[system_name].append(Negotiation(meta_protocol_system_name, negotiation_id))

        protocol_name = self.proposed_systems.systems[system_name].protocol.name

        msg = self.meta_protocol.messages["OfferRole"](
            uuid=negotiation_id,
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

    def add_protocol(self, protocol: Protocol):
        """Add a new protocol to the adapter at runtime."""
        if protocol.name not in self.protocols:
            self.protocols[protocol.name] = protocol
            self.inject(protocol)
            for message in protocol.messages.values():
                self.messages[message.qualified_name] = message
            return self.check_capable_roles(protocol)
        else:
            self.warning(f"Protocol {protocol.name} already exists in adapter.")


    def check_capable_roles(self, protocol: Protocol):
        roles = protocol.roles
        capabilities_for_role = {}
        for rname, role in roles.items():
            capabilities_for_role[rname] = []
            messages = role.messages()
            for mname, message in messages.items():
                if message.sender == role:
                    capabilities_for_role[rname].append(message)
        roles_capable = set()
        for role_name, needed_capabilities in capabilities_for_role.items():
            if all([a.name in self.capabilities for a in needed_capabilities]):
                roles_capable.add(role_name)
                self.capable_roles.add(role_name)
        self.info(f"Capable roles: {', '.join(self.capable_roles)}")
        return roles_capable