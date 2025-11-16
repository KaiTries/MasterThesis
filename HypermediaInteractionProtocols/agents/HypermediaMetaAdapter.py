"""
HypermediaMetaAdapter - Unified agent abstraction combining BSPL protocol enactment
with hypermedia discovery and workspace interaction.

This adapter extends MetaAdapter to provide:
- Automatic workspace registration and Thing Description management
- Built-in agent and protocol discovery
- Seamless integration of hypermedia semantics with protocol enactment
- Self-describing agent capabilities through RDF metadata
"""

import asyncio
from typing import Optional
from bspl.adapter import MetaAdapter
from bspl.protocol import Protocol
import HypermediaTools


class HypermediaMetaAdapter(MetaAdapter):
    """
    A MetaAdapter with integrated hypermedia capabilities.

    This adapter automatically manages:
    - Workspace membership (join/leave)
    - Thing Description generation and updates
    - Agent discovery in the workspace
    - Protocol discovery through semantic links
    - Role advertisement to other agents
    """
    Counter = 0

    def __init__(
        self,
        name: str,
        workspace_uri: str = None,
        base_uri: str = None,
        goal_artifact_uri: str = None,
        goal_artifact_class: str = None,
        goal_type: str = None,
        web_id: str = None,
        adapter_endpoint: str = None,
        capabilities: set = None,
        systems: dict = None,
        agents: dict = None,
        debug: bool = False,
        auto_join: bool = True,
        auto_discover_workspace: bool = False,
        auto_reason_role: bool = True
    ):
        """
        Initialize HypermediaMetaAdapter.

        Args:
            name: Agent's name
            workspace_uri: URI of the workspace to join (if known)
            base_uri: Base URI to start workspace discovery from (alternative to workspace_uri)
            goal_artifact_uri: Goal artifact URI for workspace discovery (URI-based discovery)
            goal_artifact_class: Goal artifact RDF class for workspace discovery (class-based discovery)
            goal_type: Agent's goal type for role reasoning (e.g., gr:Buy, gr:Sell)
            web_id: Agent's web identifier
            adapter_endpoint: Port number for the BSPL adapter endpoint
            capabilities: Set of message names this agent can send
            systems: Initial systems (usually empty for dynamic agents)
            agents: Initial agent address book (can be empty)
            debug: Enable debug logging
            auto_join: Automatically join workspace on initialization
            auto_discover_workspace: Automatically discover workspace from base_uri + goal
            auto_reason_role: Automatically reason which role to take in protocols

        Discovery modes (when auto_discover_workspace=True):
            1. URI-based: Provide base_uri + goal_artifact_uri
            2. Class-based: Provide base_uri + goal_artifact_class (most autonomous!)

        Role reasoning (when auto_reason_role=True):
            Agent reasons which role to take based on goal_type and capabilities.
            Example: goal_type=gr:Buy + capabilities={Pay} → automatically takes Buyer role

        Note:
            Either workspace_uri OR (base_uri + goal_artifact_uri/goal_artifact_class) must be provided.
            Class-based discovery is the most autonomous - agent only needs to know the semantic
            type of artifact it wants, not the exact URI.
        """
        self.base_uri = base_uri
        self.goal_artifact_uri = goal_artifact_uri
        self.goal_artifact_class = goal_artifact_class
        self.goal_type = goal_type
        self.auto_reason_role = auto_reason_role
        self.web_id = web_id
        self.adapter_endpoint = adapter_endpoint
        self.artifact_address = None
        self._joined = False

        systems = systems or {}
        agents = agents or {name: [('127.0.0.1', int(adapter_endpoint))]}
        capabilities = capabilities or set()

        super().__init__(
            name=name,
            systems=systems,
            agents=agents,
            capabilities=capabilities,
            debug=debug
        )


        # Auto-discover workspace if requested
        if auto_discover_workspace and base_uri:
            if goal_artifact_class:
                discovered_workspace, discovered_artifact = self.discover_workspace_by_class(
                    base_uri, goal_artifact_class
                )
                if discovered_workspace:
                    self.workspace_uri = discovered_workspace
                    self.goal_artifact_uri = discovered_artifact
                    self.info(f"Discovered workspace: {discovered_workspace}")
                    self.info(f"Discovered artifact: {discovered_artifact}")
                else:
                    raise ValueError(f"Could not discover workspace for artifact class: {goal_artifact_class}")
            elif goal_artifact_uri:
                # URI-based discovery
                discovered_workspace = self.discover_workspace(base_uri, goal_artifact_uri)
                if discovered_workspace:
                    self.workspace_uri = discovered_workspace
                else:
                    raise ValueError(f"Could not discover workspace for goal artifact: {goal_artifact_uri}")
            else:
                raise ValueError("auto_discover_workspace requires either goal_artifact_uri or goal_artifact_class")
        else:
            # Use provided workspace_uri or set to None
            self.workspace_uri = workspace_uri

        # Auto-join workspace if requested
        if auto_join:
            if not self.workspace_uri:
                self.logger.error("Cannot auto-join: no workspace_uri available. Set workspace_uri or enable auto_discover_workspace.")
            else:
                success, artifact_address = self.join_workspace()
                if not success:
                    self.logger.error("Failed to join workspace during initialization")

    def join_workspace(self) -> tuple[bool, Optional[str]]:
        """
        Join the workspace and register agent presence.

        Returns:
            Tuple of (success: bool, artifact_address: str | None)
        """
        metadata = self._generate_thing_description()
        success, artifact_address = HypermediaTools.join_workspace(
            self.workspace_uri,
            self.web_id,
            self.name,
            metadata
        )

        if success:
            self.artifact_address = artifact_address
            self._joined = True
            self.info(f"Successfully joined workspace at {artifact_address}")
        else:
            self.warning("Failed to join workspace")

        return success, artifact_address

    def leave_workspace(self) -> bool:
        """
        Leave the workspace and unregister agent presence.

        Returns:
            True if successful, False otherwise
        """
        if not self._joined:
            self.warning("Not currently joined to workspace")
            return False

        success = HypermediaTools.leave_workspace(
            self.workspace_uri,
            self.web_id,
            self.name
        )

        if success:
            self._joined = False
            self.artifact_address = None
            self.info("Successfully left workspace")
        else:
            self.warning("Failed to leave workspace")

        return success

    def discover_agents(self) -> list[HypermediaTools.HypermediaAgent]:
        """
        Discover all agents in the workspace.
        Automatically adds discovered agents to the address book.

        Returns:
            List of HypermediaAgent objects
        """
        if not self._joined or not self.artifact_address:
            self.warning("Must join workspace before discovering agents")
            return []

        agents = HypermediaTools.get_agents(self.workspace_uri, self.artifact_address)

        # Automatically add to address book
        for agent in agents:
            self.upsert_agent(agent.name, agent.addresses)
            self.info(f"Discovered agent: {agent.name} with roles {agent.roles}")

        return agents

    def discover_protocol(self, protocol_name: str = None) -> Optional[Protocol]:
        """
        Discover and load a protocol from the workspace.
        Automatically adds the protocol to the adapter.

        Args:
            protocol_name: Optional specific protocol name to load

        Returns:
            Protocol object or None if not found
        """
        try:
            protocol = HypermediaTools.get_protocol(self.workspace_uri, protocol_name)
            if self.get_protocol(protocol.name) == None:
                self.add_protocol(protocol)
                self.info(f"Discovered and added protocol: {protocol.name}")
            return protocol
        except Exception as e:
            self.warning(f"Failed to discover protocol: {e}")
            return None

    def discover_workspace(self, base_uri: str, goal_artifact_uri: str, max_depth: int = 5) -> Optional[str]:
        """
        Discover which workspace contains a goal artifact by crawling from base URI.
        This implements true hypermedia-driven workspace discovery.

        Args:
            base_uri: Base URI to start crawling from (e.g., "http://localhost:8080/")
            goal_artifact_uri: URI of the goal artifact
            max_depth: Maximum depth to search (default: 5)

        Returns:
            URI of workspace containing the artifact, or None if not found
        """
        self.info(f"Starting workspace discovery from {base_uri}")
        workspace_uri = HypermediaTools.discover_workspace_for_goal(
            base_uri,
            goal_artifact_uri,
            max_depth
        )

        if workspace_uri:
            self.info(f"Discovered workspace: {workspace_uri}")
        else:
            self.warning(f"Could not discover workspace for artifact: {goal_artifact_uri}")

        return workspace_uri

    def discover_workspace_by_class(
        self,
        base_uri: str,
        artifact_class: str,
        max_depth: int = 5
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Discover which workspace contains an artifact of a specific RDF class.
        This is the most autonomous form of discovery - the agent only needs to know
        the semantic type of thing it's looking for, not the exact URI.

        Example:
            # Agent only knows it wants a rug (ex:Rug class)
            workspace, rug_uri = adapter.discover_workspace_by_class(
                "http://localhost:8080/",
                "http://example.org/Rug"
            )

        Args:
            base_uri: Base URI to start crawling from
            artifact_class: Full URI of the RDF class to search for
            max_depth: Maximum depth to search (default: 5)

        Returns:
            Tuple of (workspace_uri, artifact_uri) or (None, None) if not found
        """
        self.info(f"Starting class-based workspace discovery from {base_uri}")
        self.info(f"Looking for artifact of class: {artifact_class}")

        workspace_uri, artifact_uri = HypermediaTools.discover_workspace_by_artifact_class(
            base_uri,
            artifact_class,
            max_depth,
        )

        if workspace_uri and artifact_uri:
            self.info(f"Discovered workspace: {workspace_uri}")
            self.info(f"Discovered artifact: {artifact_uri}")
        else:
            self.warning(f"Could not discover workspace for artifact class: {artifact_class}")

        return workspace_uri, artifact_uri

    def discover_protocol_for_goal(self, goal_item_uri: str) -> Optional[Protocol]:
        """
        Discover protocol needed for a goal item through semantic reasoning.
        Uses GoodRelations ontology to find offerings and linked protocols.

        Args:
            goal_item_uri: URI of the goal item/artifact

        Returns:
            Protocol object or None if not found
        """
        # Try to find protocol name from goal item
        protocol_name = HypermediaTools.get_protocol_name_from_goal_offering(
            self.workspace_uri,
            goal_item_uri
        )

        if not protocol_name:
            self.warning(f"No protocol found for goal item: {goal_item_uri}")
            return None

        self.info(f"Found protocol '{protocol_name}' for goal item")
        return self.discover_protocol(protocol_name)

    def reason_my_role(self, protocol: Protocol, verbose: bool = None) -> Optional[str]:
        """
        Reason which role this agent should take in a protocol based on its goal and capabilities.

        This implements semantic role reasoning - the agent determines its role based on:
        1. Its goal (e.g., gr:Buy to acquire, gr:Sell to provide)
        2. Its capabilities (e.g., {"Pay"} means can send Pay messages)
        3. The protocol's role semantics (which role matches the goal + capabilities)

        Example:
            protocol = adapter.discover_protocol_for_goal(artifact_uri)
            my_role = adapter.reason_my_role(protocol)
            # Returns: "Buyer" (if goal=gr:Buy and capabilities={Pay})

        Args:
            protocol: The protocol to reason about
            verbose: Print reasoning steps (default: uses debug setting)

        Returns:
            Role name that best matches, or None if:
            - No goal_type configured
            - No role semantics available
            - No compatible role found
        """
        if not self.goal_type:
            self.warning("Cannot reason role: no goal_type specified")
            self.info("Set goal_type parameter (e.g., goal_type='http://purl.org/goodrelations/v1#Buy')")
            return None

        if verbose is None:
            verbose = self.debug

        self.info(f"Reasoning role for protocol: {protocol.name}")
        self.info(f"  My goal: {self.goal_type}")
        self.info(f"  My capabilities: {self.capabilities}")

        # Get protocol description URI (where role semantics are served)
        # Protocol descriptions contain the RDF metadata including role semantics
        protocol_uri = f"http://localhost:8005/protocol_descriptions/{protocol.name.lower()}_protocol"

        # Reason the role
        role = HypermediaTools.reason_role_for_goal(
            protocol_uri,
            self.goal_type,
            self.capabilities,
            verbose=verbose
        )

        if role:
            self.info(f"Reasoned my role: {role}")
        else:
            self.warning("Could not reason appropriate role for this protocol")
            self.info("Possible reasons:")
            self.info("  - No role semantics available for protocol")
            self.info("  - Goal/capability mismatch with available roles")
            self.info("  - Missing required capabilities")

        return role

    def advertise_roles(self) -> bool:
        """
        Update Thing Description to advertise roles this agent can enact.
        Should be called after protocols are added.

        Returns:
            True if successful, False otherwise
        """
        if not self._joined or not self.artifact_address:
            self.warning("Must join workspace before advertising roles")
            return False

        if not self.capable_roles:
            self.warning("No capable roles to advertise")
            return False

        # Get all protocol names for capable roles
        protocol_names = set()
        for protocol in self.protocols.values():
            if any(role in self.capable_roles for role in protocol.roles.keys()):
                protocol_names.add(protocol.name)

        # Generate and upload role metadata for each protocol
        success = True
        for protocol_name in protocol_names:
            # Get roles for this specific protocol
            protocol = self.protocols[protocol_name]
            roles_for_protocol = [
                role for role in protocol.roles.keys()
                if role in self.capable_roles
            ]

            if roles_for_protocol:
                metadata = HypermediaTools.generate_role_metadata(
                    self.artifact_address,
                    roles_for_protocol,
                    protocol_name
                )

                status = HypermediaTools.update_body(
                    self.artifact_address,
                    self.web_id,
                    self.name,
                    metadata
                )

                if status == 200:
                    self.info(f"Advertised roles {roles_for_protocol} for protocol {protocol_name}")
                else:
                    self.warning(f"Failed to advertise roles for {protocol_name}")
                    success = False

        return success

    async def discover_and_propose_system(
        self,
        protocol_name: str,
        system_name: str,
        my_role: str,
        goal_item_uri: Optional[str] = None
    ) -> Optional[str]:
        """
        High-level workflow: discover everything needed and propose a system.

        1. Optionally discover protocol from goal item
        2. Discover agents in workspace
        3. Propose system with self in specified role
        4. Offer remaining roles to capable agents

        Args:
            protocol_name: Name of protocol to enact (ignored if goal_item_uri provided)
            system_name: Name for the proposed system
            my_role: Role this agent will take
            goal_item_uri: Optional goal item to discover protocol from

        Returns:
            Proposed system name or None if failed
        """
        # Discover protocol
        if goal_item_uri:
            protocol = self.discover_protocol_for_goal(goal_item_uri)
            if not protocol:
                return None
        else:
            protocol = self.discover_protocol(protocol_name)
            if not protocol:
                return None

        # Discover agents
        agents = self.discover_agents()
        if not agents:
            self.warning("No other agents discovered in workspace")

        # Build system dict with self in specified role
        system_dict = {
            "protocol": protocol,
            "roles": {role: None for role in protocol.roles.keys()}
        }
        system_dict["roles"][my_role] = self.name


        # Propose system
        system_name = system_name + str(self.Counter)
        self.Counter+=1
        proposed_name = self.propose_system(system_name, system_dict)
        self.info(f"Proposed system '{proposed_name}' for protocol {protocol.name}")

        # Offer roles to discovered agents
        await self.offer_roles(system_dict, proposed_name, agents)

        return proposed_name
    
    async def just_propose_system(
        self,
        protocol_name: str,
        system_name: str,
        my_role: str,
        goal_item_uri: Optional[str] = None 
    ):
        protocol = self.get_protocol(protocol_name=protocol_name)
        # Discover agents
        agents = self.discover_agents()
        if not agents:
            self.warning("No other agents discovered in workspace")

        # Build system dict with self in specified role
        system_dict = {
            "protocol": protocol.name,
            "roles": {role: None for role in protocol.roles.keys()}
        }
        system_dict["roles"][my_role] = self.name


        # Propose system
        system_name = system_name + str(self.Counter)
        self.Counter+=1
        proposed_name = self.propose_system(system_name, system_dict)
        self.info(f"Proposed system '{proposed_name}' for protocol {protocol.name}")

        # Offer roles to discovered agents
        await self.offer_roles(system_dict, proposed_name, agents)

        return proposed_name

    async def wait_for_system_formation(
        self,
        system_name: str,
        timeout: float = 30.0,
        check_interval: float = 0.5
    ) -> bool:
        """
        Wait for a proposed system to become well-formed.

        Args:
            system_name: Name of the proposed system
            timeout: Maximum time to wait in seconds
            check_interval: How often to check in seconds

        Returns:
            True if system is well-formed, False if timeout
        """
        elapsed = 0.0
        while elapsed < timeout:
            system = self.proposed_systems.get_system(system_name)
            if system and system.is_well_formed():
                self.info(f"System '{system_name}' is well-formed!")
                return True

            await asyncio.sleep(check_interval)
            elapsed += check_interval

        self.warning(f"System '{system_name}' did not become well-formed within {timeout}s")
        return False

    def _generate_thing_description(self) -> str:
        """
        Generate the initial Thing Description for this agent.
        Includes the sendMessage action affordance for BSPL adapter.

        Returns:
            RDF/Turtle string
        """
        return HypermediaTools.generate_body_metadata(self.adapter_endpoint)

    def __enter__(self):
        """Context manager support for automatic workspace cleanup."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Automatically leave workspace when context exits."""
        if self._joined:
            self.leave_workspace()
        return False

    async def __aenter__(self):
        """Async context manager support."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Automatically leave workspace when async context exits."""
        if self._joined:
            self.leave_workspace()
        return False


# =============================================================================
# Convenience Factory Functions
# =============================================================================

def create_hypermedia_agent(
    name: str,
    workspace_uri: str,
    adapter_endpoint: int,
    capabilities: set,
    web_id: str = None,
    debug: bool = False,
    auto_join: bool = True
) -> HypermediaMetaAdapter:
    """
    Convenience factory for creating a HypermediaMetaAdapter with common defaults.

    Args:
        name: Agent's name
        workspace_uri: URI of the workspace to join
        adapter_endpoint: Port number for the adapter
        capabilities: Set of message names this agent can send
        web_id: Agent's web ID (defaults to http://localhost:{port})
        debug: Enable debug logging
        auto_join: Automatically join workspace on creation

    Returns:
        Initialized HypermediaMetaAdapter
    """
    web_id = web_id or f"http://localhost:{adapter_endpoint}"

    return HypermediaMetaAdapter(
        name=name,
        workspace_uri=workspace_uri,
        web_id=web_id,
        adapter_endpoint=str(adapter_endpoint),
        capabilities=capabilities,
        debug=debug,
        auto_join=auto_join
    )
