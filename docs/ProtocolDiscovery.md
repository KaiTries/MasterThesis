# Protocol Discovery - Approaches
Agents are situated in the hypermedia environment and need to discover protocols to interact with other agents.

How should agents discover protocols through hypermedia? Two approaches to consider:
- Discover the full protocol specification upfront
- Discover affordances for sending out individual messages as the interaction progresses


### Full Protocol Specification
In this approach the agent will discover the full protocol specification upfront.

#### Example
An agent finds his goal artifact and sees that to obtain it he needs to use protocol X. 
The agent then finds the full specification and starts from there.

#### Pros
- Can utilize the existing BSPL tooling for protocol enactment.
- Entire protocol allows us to reason on the interaction.
- We can decide which role we **can** play, based on the protocol specification.
- Simple to implement. Only need to return the protocol specification.

#### Cons
- Need a way to link from the goal artifact to the protocol specification.
- Need a way to also link to the starting point of the protocol enactment.
- Need a way to link role to desired goal.


### Affordance Discovery
In this approach the agent will discover affordances for sending out individual messages as the interaction progresses.

#### Example
An agent find his goal artifact. Some affordance is available to send out a message.
The agent sends out the message. New affordances are discovered as a result of the message sent.

#### Pros
- Directly link to the start of the protocol enactment.
- Less upfront knowledge needed.
- Gives us the role of the agent since it will be the one sending the initial message.
  - Would need to dynamically figure out the roles of other agents as the interaction progresses.
- More distributed. Each entity can provide affordances for the messages it can handle.
- More flexible. New affordances can be added without changing the protocol specification.
- More aligned with HATEOS.

#### Cons
- Can't utilize the existing BSPL tooling for protocol enactment.
- Don't think it aligns with the BSPL model very well.
  - Would need to incrimentally build the protocol instance (and specification) as the interaction progresses.
- How would we find out which protocol we are enacting and which role we and other agents are playing?
- Harder to reason on the interaction.
- We can only decide which role we **want** to play, based on the affordance
- Harder to implement. Multiple resources might have to change their representations to reflect new affordances.


### Conclusion
I think the Full Protocol Specification approach is the better solution. 
It aligns better with the BSPL model and allows us to utilize existing tooling.
It is also simpler to implement and reason on. I do not see any major drawbacks with this approach,
as we need some additional semantics either way. 