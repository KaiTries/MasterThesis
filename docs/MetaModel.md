# Draft for the Metamodel - Discovery and Enactment of Interaction Protocols in Dynamically Open Settings

## Metamodel Draft

## simpler

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
 class Agent {
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
 Workspace "1" o-- "*" Entity : contains
 Workspace "0..*" o-- "0..*" HypermediaControl : advertises

 %% Entities
 Entity "0..*" o-- "0..*" SemanticAnnotation : annotates

 %% AgentBody
 Agent "0..*" o-- "0..*" HypermediaControl : offers
 Entity <|-- Agent : is-a


 %% --- Protocol specification (BSPL/IOSE) ---
 class Protocol {
   +name
 }
 class Role {
   +name
 }
 class Message {
   +name
 }

 Protocol "1" o-- "*" Role : defines
 Protocol "1" o-- "*" Message : declares
 Role "*" <-- "*" Message : sends/receives

 class MetaProtocol {
   +name = "RoleBindingProtocol"
 }

 Role "*" --> "1" AgentBody : enactedBy

 %% --- Cues for in-context discovery ---
 class Signifier {
   +href
 }
 Workspace "0..*" o-- "0..*" Signifier : exposes
 Protocol "0..*" o-- "0..*" Signifier : linksTo
 SemanticAnnotation "0..*" --> "0..*" Protocol : references
 HypermediaControl "0..*" --> "0..*" Message : triggers

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
