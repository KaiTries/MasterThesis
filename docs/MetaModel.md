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


%% --- Target protocol (referenced only) ---
class ProtocolSpec { +name }
class Role { +name }
ProtocolSpec "1" o-- "*" Role : defines

%% --- Agents ---
class Agent { +id }

%% --- Metaprotocol definition (simple & universal) ---
class MetaProtocol {
  +name = "RoleOffer"
  +universallyKnown = true
}
class MP_Role { +name /* Initiator | Candidate */ }
class MP_Message { +name /* OfferRole | Accept | Reject */ }

MetaProtocol "1" o-- "*" MP_Role : defines
MetaProtocol "1" o-- "*" MP_Message : declares
MP_Role "*" <-- "*" MP_Message : sends/receives

%% --- Runtime artifacts/messages ---
class OfferRole {
  +id
  +protocol : ProtocolSpec
  +role : Role
  +from : Agent  // Initiator
  +to : Agent    // Candidate
}
class Accept { +timestamp }
class Reject { +reason? }

%% --- Outcome on acceptance ---
class RoleBinding { +id }

%% --- Relations / flow ---
Agent "1" --> "0..*" OfferRole : sends(OfferRole)
OfferRole "1" --> "1" ProtocolSpec : about
OfferRole "1" --> "1" Role : asks_for
Agent "0..*" --> "0..*" Accept : sends(Accept)
Agent "0..*" --> "0..*" Reject : sends(Reject)
Accept "*" --> "1" OfferRole : of
Reject "*" --> "1" OfferRole : of

%% acceptance yields a binding
Accept "1" --> "1" RoleBinding : yields
RoleBinding "*" --> "1" Role : as
RoleBinding "*" --> "1" Agent : enactedBy  %% the Candidate
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
