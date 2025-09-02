# Must buy groceries
# Will go into the bazaar and initiate the protocol to buy something
WEB_ID = 'http://localhost:8011'
BAZAAR_URI = 'http://localhost:8080/workspaces/bazaar/'

def get_body_metadata(artifact_address):
    BODY_METADATA = f"""
    @prefix td: <https://www.w3.org/2019/wot/td#>.
    @prefix hctl: <https://www.w3.org/2019/wot/hypermedia#> .
    @prefix htv: <http://www.w3.org/2011/http#> .

    <{artifact_address}> 
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
    return BODY_METADATA
