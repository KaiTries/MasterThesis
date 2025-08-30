import time
from agents.agent.hypermedia import *
from bspl.adapter import Adapter
import logging

logger = logging.getLogger("agent")

class HypermediaAgent:
    def __init__(self, name, web_id, agent_name, workspace_uri, self_uri, me, my_roles = {}, body_metadata = None, capabilities=None, reactions=None):
        self.name = name
        self.web_id = web_id
        self.agent_name = agent_name
        self.my_workspace = workspace_uri
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
        logger.info("Joining workspace")
        return postWorkspace(self.my_workspace + 'join', WEB_ID=self.web_id, AgentName=self.agent_name)

    def leave_workspace(self):
        logger.info("Leaving workspace")
        return postWorkspace(self.my_workspace + 'leave', WEB_ID=self.web_id, AgentName=self.agent_name)

    def update_body(self):
        logger.info("Updating body representation")
        return updateBody(self.my_workspace + 'artifacts/body_' + self.agent_name, WEB_ID=self.web_id, AgentName=self.agent_name, metadata=self.body_metadata)

    def setup_protocol_and_systems(self, protocol_name):
        self.protocol = getProtocol(self.my_workspace, protocol_name)
        role_for_protocol = role_capable_of(capabilities=self.capabilities, protocol=self.protocol)
        self.my_roles[protocol_name] = role_for_protocol
        logger.info(f"Setting {role_for_protocol} as my role for {protocol_name}")
        if not role_for_protocol:
            raise Exception("No suitable role found for agent's capabilities in protocol.")
        self.agents = getAgents(self.my_workspace, self.self_uri, self.my_roles[protocol_name], self.me)
        self.systems = create_systems_for_protocol(protocol=self.protocol)


    def create_adapter(self, protocol_name):
        self.adapter = Adapter(self.my_roles[protocol_name], systems=self.systems, agents=self.agents)

    def register_reactions(self, protocol_name):
        setup_adapter(reactions=self.reactions, adapter=self.adapter, protocol=self.protocol, role=self.my_roles[protocol_name])

    def run(self, protocol_name, initial_message_func=None, initial_message_args=None, wait_before_send=3):
        self.join_workspace()
        self.update_body()
        self.setup_protocol_and_systems(protocol_name)
        self.create_adapter(protocol_name)
        self.register_reactions(protocol_name)
        if initial_message_func:
            time.sleep(wait_before_send)
            initial_message = initial_message_func(**(initial_message_args or {}))
            self.adapter.start(self.adapter.send(initial_message))
        else:
            self.adapter.start()
        self.leave_workspace()