from ..protocol import Protocol

class System:
    def __init__(self, name: str, protocol: Protocol, roles: dict[str, str]):
        self.name = name
        self.protocol = protocol
        self.roles = roles  # role name to agent name mapping

    def is_well_formed(self):
        # Check that all roles in the protocol are assigned to agents
        for role in self.protocol.roles:
            if role not in self.roles or self.roles[role] is None:
                return False
        return True

    def to_dict(self):
        return {
            "protocol": self.protocol,
            "roles": self.roles
        }

    def to_dict_special(self):
        return {
            "protocol": self.protocol.name,
            "roles": self.roles
        }

class SystemStore:
    def __init__(self, systems: dict):
        self.systems: dict[str, System] = {}
        for name, system in systems.items():
            self.systems[name] = System(name, system['protocol'], system['roles'])


    def get_system(self, name: str) -> System | None:
        return self.systems.get(name)

    def add_system_dict(self, name: str, system: dict):
        if name in self.systems:
            raise ValueError(f"System with name {name} already exists.")
        self.systems[name] = System(name, system['protocol'], system['roles'])

    def add_system(self, name: str, system: System):
        if name in self.systems:
            raise ValueError(f"System with name {name} already exists.")
        self.systems[name] = system

