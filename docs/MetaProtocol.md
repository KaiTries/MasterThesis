# Draft MetaProtocol - Protocol participation

### Context

Because agents are able to dynamically participate in protocols they must be able to decide if they want to do that.
If some agent A wants to enact protocol P which also requires an additional agent for role R, agent A should not be able to just
decide that some other agent C must participate. Instead, they should ask the other agent to participate and for that we can use a MetaProtocol.

### Logic of MetaProtocol

Conceptually it is a straightforward protocol. We define two parties:
- Initiator: Wants to enact some protocol and is looking for participants
- Candidate: Some other agent that the Initiator wants for the protocol
  
The parameters are needed so that the agents can correctly assign the wanted protocol enactment to their respective systems:
- protocolName: Represents the protocol that the initiator wants to instantiate
- systemName: Represents the system that the wanted enactment entails
- sender: Metadata of the Initiator
- proposedRole: Role that the Initiator wants the Candidate to play
- accept / reject: Decision variables
- enactmentSpecs: Representation of the fully formed system. Enough information for Candidate to successfully participate in wanted protocol

#### RoleNegotiation MetaProtocol in BSPL
```
RoleNegotiation {
    roles Initiator, Candidate
    parameters, out protocolName key, out systemName key, out sender, out proposedRole, out accept, out reject, out enactmentSpecs

    Initiator -> Candidate: OfferRole[out protocolName key , out systemName key, out sender, out proposedRole]

    Candidate -> Initiator: Accept[in protocolName key, in systemName key, in proposedRole, out accept]
    Candidate -> Initiator: Reject[in protocolName key, in systemName key, in proposedRole, out reject]

    Initiator -> Candidate: SystemDetails[in protocolName key, in systemName key, in accept, out enactmentSpecs]
}
```

The desired outcome is achieved. The Initiator can now finish preparing the protocol and distribute the needed information. E.g.,
the protocol might still need other roles to be filled and this additional information is needed by all participating agents.

#### Caveats
The meta protocol itself is also just a protocol so it has the same basic problems as any other protocol.
To circumvent this we define this single protocol as a basic capability of each agent and that each agent always participates in this protocol.
This is achieved through the MetaAdapter, which already implements the basic functionality and the rolenegotiation protocol. Any agent that
uses the MetaAdapter as its BSPL adapter can understand the MetaProtocol.
