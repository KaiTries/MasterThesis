from rdflib import Graph
import requests
from helpers import *

def get_query_protocol_for_item(goal_item: str) -> str:
    return f"""
PREFIX gr:   <http://purl.org/goodrelations/v1#>
PREFIX bspl: <https://purl.org/bspl#>
PREFIX schema: <http://schema.org/>
PREFIX ex: <http://example.com/> 

SELECT ?offering ?action ?protocol WHERE {{
  ?offering a gr:Offering ;
      gr:includesObject ?taq ;
      schema:potentialAction ?action .

  ?action a schema:BuyAction ;
    schema:target ?protocol .

  ?taq a gr:TypeAndQuantityNode ;
      gr:typeOfGood <{goal_item}> .
}}
"""

def get_protocol_name_from_goal(workspace_uri: str, goal_item: str) -> str | None:
    workspace_description = requests.get(workspace_uri).text
    model = get_model(workspace_description)
    qres = model.query(get_query_protocol_for_item(goal_item))
    for row in qres:
        return str(row.protocol)
    return None

