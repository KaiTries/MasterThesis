from rdflib import Graph, Namespace

g = Graph()
g.parse("bazaar.ttl", format="turtle")

gr = Namespace("http://purl.org/goodrelations/v1#")
schema = Namespace("http://schema.org/")
bspl = Namespace("https://purl.org/bspl#")

q = """
PREFIX gr:      <http://purl.org/goodrelations/v1#>
PREFIX schema:  <http://schema.org/>
PREFIX bspl:    <https://purl.org/bspl#>

SELECT ?offer ?price ?currency ?protocol ?endpoint
WHERE {
  ?offer a gr:Offering ;
         gr:hasPriceSpecification [
           gr:hasCurrencyValue ?price ;
           gr:hasCurrency ?currency
         ] ;
         schema:potentialAction ?act .
  ?act bspl:usesProtocol ?protocol ;
       schema:target/schema:urlTemplate ?endpoint .
}
"""

for row in g.query(q):
    print(row)

from rdflib import Graph
g = Graph().parse("bazaar.ttl", format="turtle")
q = open("query.rq").read()
for row in g.query(q):
    print(row)
