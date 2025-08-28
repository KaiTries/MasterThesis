# Draft for the Metamodel - Discovery and Enactment of Interaction Protocols in Dynamically Open Settings

## Metamodel Draft

## simpler

The simple Idea is that entities exist in the hypermedia space, which is separated into workspace.
Workspaces tell us which protocols care available in the context of locality.
Entities in the workspace might reference protocols through semantic annotations.
A protocol consists of roles and messages, a role can be enacted by an agent.

```mermaid
graph

 %% --- Hypermedia layer ---
 A[HypermediaSpace]
 B[Workspace]
 C[Entity]
 D[Agent]
 E[SemanticAnnotation]

 %% workspace
 A -->|hosts| B
 B -->|contains| C

 %% Entities
 E -->|annotates| C

 %% AgentBody
 D --> |is-a| C


 %% --- Protocol specification (BSPL) ---
 F[Protocol]
 G[Role]
 H[Message]

 F -->|defines| G
 F -->|declares| H
 G -->|sendes/receives| H
 G -->|enactedBy| D

 %% --- Cues for in-context discovery ---
 I[Signifier]

 B -->|exposes| I
 I -->|linksTo| F
 E -->|references| F

```

The simple metamodel can describe the discovery of protocols, but fails to describe the dynamic binding of agents to roles,
as well as the role negotiation

## Metamodel - Only RoleBinding

```mermaid
classDiagram

%% --- Core actors & intents ---
class AgentBody {
  +id
  +capabilities : Set<MessageName>
}
class Goal {
  +id
  +description
}
AgentBody "1" o-- "0..*" Goal : pursues

%% --- Protocol to be enacted ---
class ProtocolSpec {
  +name
  +language = "BSPL"
}
class Role {
  +name
}
class Message {
  +name
}
ProtocolSpec "1" o-- "*" Role : defines
ProtocolSpec "1" o-- "*" Message : declares
Role "*" <-- "*" Message : sends/receives  %% informational (enactability check)

%% --- Binding problem definition ---
class BindingSession {
  +id
  +state : Draft|Soliciting|Resolving|Committed|Aborted
  +initiatorId
}
class RoleRequirement {
  +min : int
  +max : int
  +selfEligible : bool  // initiator may enact this role?
}
BindingSession "1" --> "1" ProtocolSpec : for
BindingSession "1" o-- "*" RoleRequirement : needs
RoleRequirement "*" --> "1" Role : role

%% --- Candidate discovery & offers (meta-protocol exchanges) ---
class RoleRequest {
  +id
  +deadline?
  +criteria? : JSON
}
class RoleOffer {
  +id
  +score? : number
  +evidence? : CapabilityProof
}
class CapabilityProof {
  +summary
}

BindingSession "1" o-- "*" RoleRequest : broadcasts
RoleRequest "*" --> "1" RoleRequirement : targets
AgentBody "0..*" --> "0..*" RoleOffer : submits
RoleOffer "*" --> "1" RoleRequest : answers
RoleOffer "0..1" --> "1" CapabilityProof : proves

%% --- Resolution & commitments ---
class SelectionPolicy {
  +name
  +logic? : reference
}
class BindingProposal {
  +id
}
class Acceptance {
  +timestamp
}
class Rejection {
  +reason?
}
class RoleBinding {
  +id
}
class ProtocolInstance {
  +id
}

BindingSession "1" --> "0..1" SelectionPolicy : uses
BindingSession "1" o-- "0..*" BindingProposal : proposes
BindingProposal "*" --> "*" RoleOffer : includes
BindingProposal "1" o-- "*" RoleBinding : resultsIn(when accepted)
RoleBinding "*" --> "1" RoleRequirement : satisfies
RoleBinding "*" --> "1" AgentBody : enactedBy
RoleBinding "*" --> "1" Role : as

%% accept/reject handshake on proposals
BindingProposal "1" o-- "0..*" Acceptance : onAllParties
BindingProposal "1" o-- "0..*" Rejection : anyParty

%% when all requirements met, instantiate protocol
BindingSession "1" --> "0..1" ProtocolInstance : spawns(when committed)
ProtocolSpec "1" <-- "0..*" ProtocolInstance : enacts
```

## Maybe still too complicated

```mermaid
classDiagram

 %% --- Hypermedia layer ---
 class HypermediaSpace {
    +uri
 }
 class Workspace {
   +uri
 }
 class Entity {
   +kind // artifact, agentBody, etc...
 }
 class AgentBody {
   +uri
   +capabilities : Set<MessageName>
 }
 class HypermediaControl {
   +rel
   +method
   +target
 }
 class SemanticAnnotation {
   +property
   +value
 }

 %% workspace
 HypermediaSpace "1" o-- "*" Workspace : hosts
 Workspace "*" o-- "*" Workspace : contains
 Workspace "1" o-- "*" Entity : contains
 Workspace "0..*" o-- "0..*" HypermediaControl : advertises

 %% Entities
 Entity "0..*" o-- "0..*" SemanticAnnotation : annotates

 %% AgentBody
 AgentBody "0..*" o-- "0..*" HypermediaControl : offers
 Entity <|-- AgentBody : is-a


 %% --- Protocol specification (BSPL/IOSE) ---
 class ProtocolSpec {
   +name
   +language = "BSPL"
 }
 class Role {
   +name
   +goalHints?  // semantic cues for role choice
 }
 class Message {
   +name
   +schema
   +in~out~nil : Direction
 }

 ProtocolSpec "1" o-- "*" Role : defines
 ProtocolSpec "1" o-- "*" Message : declares
 Role "*" <-- "*" Message : sends/receives

 %% --- Discovery + Binding + Enactment ---
 class ProtocolInstance {
   +id
   +state = Active|Completed|Failed
 }
 class RoleBinding {
   +id
 }
 class MetaProtocol {
   +name = "RoleBindingProtocol"
 }

 Workspace "1" o-- "*" ProtocolInstance : occursIn
 ProtocolSpec "1" <-- "*" ProtocolInstance : enacts
 ProtocolInstance "1" o-- "*" RoleBinding : has
 RoleBinding "*" --> "1" Role : bindsTo
 RoleBinding "*" --> "1" AgentBody : enactedBy
 MetaProtocol "1" --> "*" RoleBinding : negotiates

 %% --- Cues for in-context discovery ---
 class Signifier {
   +type  // "protocol-catalog" ...
   +href
 }
 Workspace "0..*" o-- "0..*" Signifier : exposes
 ProtocolSpec "0..*" o-- "0..*" Signifier : linksTo
 SemanticAnnotation "0..*" --> "0..*" ProtocolSpec : references
 HypermediaControl "0..*" --> "0..*" Message : triggers



```
