from bspl.protocol import Protocol
from bspl.adapter import Adapter

def create_systems_for_protocol(protocol: Protocol):
    return {
        protocol.name.lower() : {
            "protocol" : protocol,
            "roles" : {
                protocol.roles[role] : role for role in protocol.roles
            }
        }
    }

# Return first role that agent is capable of
def role_capable_of(capabilities, protocol: Protocol):
    roles = protocol.roles
    capabilities_for_role = {}
    for rname, role in roles.items():
        capabilities_for_role[rname] = []
        messages = role.messages()
        for mname, message in messages.items():
            if message.sender == role:
                capabilities_for_role[rname].append(message)           

    for rolename, needed_capabilities in capabilities_for_role.items():
        if all([a.name in capabilities for a in needed_capabilities]):
            return rolename


def setup_adapter(reactions, adapter: Adapter, protocol: Protocol, role):
    messages = protocol.roles[role].messages()
    for mname, message in messages.items():
        if mname in reactions:
             adapter.reaction(message)(reactions[mname])
 