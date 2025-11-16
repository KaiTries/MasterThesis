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

def query_get_check_offering_for_item_two(goal_item: str) -> str:
    return f"""
    PREFIX gr:   <http://purl.org/goodrelations/v1#>
    PREFIX bspl: <https://purl.org/hmas/bspl/>

    SELECT ?protocolName ?offering WHERE {{
      ?offering a gr:Offering ;
          bspl:useProtocol ?protocolName ;
          gr:includesObject ?taq .

      ?taq a gr:TypeAndQuantityNode ;
          gr:typeOfGood <{goal_item}> .
    }}
    """

def query_get_interaction_protocol_from_item_offering(goal_item: str) -> str:
    return f"""
    PREFIX gr:   <http://purl.org/goodrelations/v1#>
    PREFIX bspl: <https://purl.org/hmas/bspl/>

    SELECT ?protocol_name WHERE {{
      ?offering a gr:Offering ;
          bspl:useProtocol ?protocol_name ;
          gr:includesObject ?taq .

      ?taq a gr:TypeAndQuantityNode ;
          gr:typeOfGood <{goal_item}> .
    }}
    """

def get_protocol_name_from_goal_two(workspace_uri: str, goal_item: str) -> str | None:
    # check if wanted item is being offered
    workspace_description = requests.get(workspace_uri).text
    model = get_model(workspace_description)
    qres = model.query(query_get_check_offering_for_item_two(goal_item))
    # if no offering debug and return None
    if len(qres) == 0:
        print("No offering found for wanted artifact")
        return None
    for q in qres:
        return q.protocolName.value
    return None

