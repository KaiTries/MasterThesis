from rdflib import Graph
import requests
from helpers import *

def query_get_check_offering_for_item(goal_item: str) -> str:
    return f"""
PREFIX gr:   <http://purl.org/goodrelations/v1#>

SELECT ?offering WHERE {{
  ?offering a gr:Offering ;
      gr:includesObject ?taq .

  ?taq a gr:TypeAndQuantityNode ;
      gr:typeOfGood <{goal_item}> .
}}
"""

def query_get_interaction_protocol_from_item(goal_item: str) -> str:
    return f"""
PREFIX hmas: <https://purl.org/hmas/>
PREFIX bspl: <https://purl.org/hmas/bspl/>
PREFIX td: <https://www.w3.org/2019/wot/td#>

SELECT ?protocol_name WHERE {{
  <{goal_item}> a hmas:Artifact ;
      bspl:useProtocol ?protocol_name .
}}
"""

def get_protocol_name_from_goal(workspace_uri: str, goal_item: str) -> str | None:
    # check if wanted item is being offered
    workspace_description = requests.get(workspace_uri).text
    model = get_model(workspace_description)
    qres = model.query(query_get_check_offering_for_item(goal_item))
    # if no offering debug and return None
    if len(qres) == 0:
        print("No offering found for wanted artifact")
        return None
    # if offering is found we know its being sold
    # check artifact representation for desired protocol
    artifact_description = requests.get(goal_item).text
    model = get_model(artifact_description)
    qres = model.query(query_get_interaction_protocol_from_item(goal_item))
    if len(qres) == 0:
        print("No interaction protocol found for wanted artifact")
        return None
    for q in qres:
        return q.protocol_name.value
    return None

