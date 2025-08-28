# Draft MetaProtocol - Protocol participation

### Context

Because agents are able to dynamically participate in protocols they must be able to decide if they want to do that.
If some agent A wants to enact protocol P which also requires an additional agent for role R, agent A should not be able to just
decide that some other agent C must participate. Instead he should ask the other agent and for this we can use a MetaProtocol.

### Logic of MetaProtocol

Conceptually it is a straightforward protocol.
We define twoo parties:

- Initiator: Wants to enact some protocol and is looking for participants
- Candidate: Some other agent that the Initiator wants for the protocol
  The parameters are also straightforward:
- protocol: Represents the protocol that the initiator wants to instantiate
- role: Represents the role that the Candidate should play
- decision: Logic variable to make Accept and Reject mutually exclusive

```
ProtocolParticipation {
    Role Initiator, Candidate
    Parameters protocol, role, decision

    Initiator -> Candidate: OfferRole(out protocol, out role)
    Candidate -> Initiator: Accept(in role, out decision)
    Candidate -> Initiator: Reject(in role, out decision)

}
```

The desired outcome is achieved. The Initiator can now finish preparing the protocol and distribute the needed information. E.g.,
the protocol might still need other roles to be filled and this additional information is needed by all participating agents.

#### Problems

The meta protocol itself is also just a protocol so it has the same basic problems as any other protocol.
To circumvent this we define this single protocol as a basic capability of each agent and that each agent always participates in this protocol.
