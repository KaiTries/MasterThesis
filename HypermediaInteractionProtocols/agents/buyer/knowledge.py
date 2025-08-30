# Must buy groceries
# Will go into the bazaar and initiate the protocol to buy something
WEB_ID = 'http://localhost:8011'
AgentName = 'buyer'
BAZAAR_URI = 'http://localhost:8080/workspaces/bazaar/'
SELF = 'http://localhost:8080/workspaces/bazaar/artifacts/body_buyer#artifact'
ME = [('127.0.0.1',8011)]
MY_ROLES = ['Buyer']


BODY_METADATA = """
@prefix td: <https://www.w3.org/2019/wot/td#>.
@prefix hctl: <https://www.w3.org/2019/wot/hypermedia#> .
@prefix htv: <http://www.w3.org/2011/http#> .

<workspaces/bazaar/artifacts/body_buyer#artifact> 
    td:hasActionAffordance [ a td:ActionAffordance;
    td:name "kikoAdapter";
    td:hasForm [
        htv:methodName "GET";
        hctl:hasTarget <http://127.0.0.1:8011/>;
        hctl:forContentType "text/plain";
        hctl:hasOperationType td:invokeAction;
    ]
].
"""

