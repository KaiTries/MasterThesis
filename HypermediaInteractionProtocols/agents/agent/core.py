import time
from agents.utils.helpers import *
from bspl.adapter import Adapter

class HypermediaAgent:
    def __init__(self, name, web_id, agent_name, bazaar_uri, self_uri, me, my_roles, body_metadata, capabilities=None, reactions=None):
        self.name = name
        self.web_id = web_id
        self.agent_name = agent_name
        self.bazaar_uri = bazaar_uri
        self.self_uri = self_uri
        self.me = me
        self.my_roles = my_roles
        self.body_metadata = body_metadata
        self.capabilities = capabilities or {}
        self.reactions = reactions or {}
        self.protocol = None
        self.systems = None
        self.agents = None
        self.adapter = None

    def join_workspace(self):
        return postWorkspace(self.bazaar_uri + 'join', WEB_ID=self.web_id, AgentName=self.agent_name)

    def leave_workspace(self):
        return postWorkspace(self.bazaar_uri + 'leave', WEB_ID=self.web_id, AgentName=self.agent_name)

    def update_body(self):
        return updateBody(self.bazaar_uri + 'artifacts/body_' + self.agent_name, WEB_ID=self.web_id, AgentName=self.agent_name, metadata=self.body_metadata)

    def setup_protocol_and_systems(self, protocol_name):
        self.protocol = getProtocol(self.bazaar_uri, protocol_name)
        self.agents = getAgents(self.bazaar_uri, self.self_uri, self.my_roles, self.me)
        self.systems = create_systems_for_protocol(protocol=self.protocol)

    def create_adapter(self):
        self.adapter = Adapter(self.my_roles[0], systems=self.systems, agents=self.agents)

    def register_reactions(self):
        setup_adapter(reactions=self.reactions, adapter=self.adapter, protocol=self.protocol, role=self.my_roles[0])

    def run(self, protocol_name, initial_message_func=None, initial_message_args=None, wait_before_send=5):
        self.join_workspace()
        self.update_body()
        self.setup_protocol_and_systems(protocol_name)
        print(self.agents)
        self.create_adapter()
        self.register_reactions()
        if initial_message_func:
            time.sleep(wait_before_send)
            initial_message = initial_message_func(**(initial_message_args or {}))
            self.adapter.start(self.adapter.send(initial_message))
        else:
            self.adapter.start()
        self.leave_workspace()