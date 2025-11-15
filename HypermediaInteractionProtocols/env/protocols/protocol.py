# provides the protocol
from flask import Flask, request, jsonify

"""
Very simple server that just provides a protocol
Currently using this because no consensus on how to make protocol available
Could also be instead served as part of the environment in fom of an rdf graph

This way is easiest to implement. As we do not need to do any parsing for the protocol 
on the agent sides.
"""


file = open('buy.bspl','r')
buy_protocol = file.read()
file.close()

file = open('buy_two.bspl','r')
buy_two_protocol = file.read()
file.close()


bspl_rdf = """
@prefix bspl: <https://purl.org/hmas/bspl/> .
@prefix gr: <http://purl.org/goodrelations/v1#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .

<http://localhost:8005/protocol_descriptions/buy_protocol> a bspl:ProtocolDescription;
    bspl:ProtocolName "Buy";
    bspl:descriptionOf <http://localhost:8005/protocols/buy_protocol> ;
    bspl:initialMessage "Pay".

<http://localhost:8005/protocols/buy_protocol> a bspl:Protocol;
    bspl:hasRole <http://localhost:8005/protocols/buy_protocol#BuyerRole> ,
                 <http://localhost:8005/protocols/buy_protocol#SellerRole> .

# Semantic Role Descriptions for autonomous role reasoning

<http://localhost:8005/protocols/buy_protocol#BuyerRole>
    a bspl:Role ;
    bspl:roleName "Buyer" ;
    bspl:hasGoal gr:seeks ;
    bspl:requiresCapability "Pay" ;
    bspl:sendsMessage "Pay" ;
    bspl:receivesMessage "Give" ;
    rdfs:comment "The Buyer acquires items by providing payment. This role is suitable for agents whose goal is to buy/acquire artifacts." ;
    rdfs:label "Buyer" .

<http://localhost:8005/protocols/buy_protocol#SellerRole>
    a bspl:Role ;
    bspl:roleName "Seller" ;
    bspl:hasGoal gr:Sell ;
    bspl:requiresCapability "Give" ;
    bspl:sendsMessage "Give" ;
    bspl:receivesMessage "Pay" ;
    rdfs:comment "The Seller provides items in exchange for payment. This role is suitable for agents whose goal is to sell/provide artifacts." ;
    rdfs:label "Seller" .
"""

app = Flask(__name__)

@app.route('/protocol_descriptions/buy_protocol', methods=['GET'])
def callback_protocol_description():
    return bspl_rdf, 200

@app.route('/protocols/buy_protocol', methods=['GET'])
def callback():
    return buy_protocol, 200

@app.route('/protocols/buy_two_protocol', methods=['GET'])
def callback_two_protocol():
    return buy_two_protocol, 200

if __name__ == '__main__':
    app.run('localhost',8005)