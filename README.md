# Repo for my Masterthesis on interaction protocols in hypermedia environments

## Immediate TODOs

- [ ] Implement simple Agent that reasons on BSPL protocol if it can do role
- - [ ] Agents know which atomic messsages they can send
- [ ] Check Ontology

## Scenario

Some user agent wants to buy a rug from some store. There exist two stores; the bazaar and the supermarket.
A storeclerk agent exists in both stores. The rug can be bought from either store, but the interaction is slightly different.
In the bazaar the interaction entails some negotiation about the price, whereas in the store it is fixed.

**Goal**

The user agent should be able to buy the rug from either store. He must achieve this without prior knowledge of the _environment_.
Meaning the _protocols_, _agents_ and other _artifacts_ are not known at compile time and must be discovered at runtime.

## Main questions to answer

### BSPL protocol extensions

- [ ] BSPL Ontology so that it can be used in knowledge graphs
- [ ] Possible semantic extensions to allow linking -> a GoodRelations:Offer might want to say bspl:usesProtocol
- [ ] Translator that does BSPL <-> RDF

#### BSPL Ontology

[current ontology](https://github.com/KaiTries/MasterThesis/blob/main/testing/bspl.ttl)

[Buy protocol expressed as RDF](https://github.com/KaiTries/MasterThesis/blob/main/testing/buy.ttl)

### Agent

- [ ] Allow agents to find new protocols -> enable hypermedia controls
- [ ] Agents need to know what roles other agents are capable off -> agent representation
- [ ] Agents also need to reason on new protocols -> Can they particpate in them? Can they enact some role?

### Environment

- [x] need Hypermedia environment where agents can live -> Yggdrasil

### Other questions

## Useful resources

- [collection of ontologies](https://lov.linkeddata.es/dataset/lov)
- [GoodRelations ontology](https://www.heppnetz.de/projects/goodrelations/primer/)
