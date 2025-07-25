from rdflib import Graph


# workspace graph representing bazaar
g = Graph().parse("test_bazaar.ttl", format="turtle")

# sparql query that looks for all offers that have:
# offer price currency protocol endpoint
q = open("query.rq").read()
#for row in g.query(q):
#    print(f"{row.offer} costs {row.price}{row.currency} - useProtocol {row.protocol} at endpoint {row.endpoint}")



g2 = Graph().parse("workspace.ttl", format="turtle")
q2 = open("query_2.rq").read()
for row in g2.query(q2):
    print(row)