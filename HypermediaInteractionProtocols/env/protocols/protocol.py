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

<http://localhost:8005/protocol_descriptions/buy_protocol> a bspl:ProtocolDescription;
    bspl:ProtocolName "Buy";
    bspl:descriptionOf <http://localhost:8005/protocols/buy_protocol> ;
    bspl:initialMessage "Pay".

// TODO: Need to describe Roles
// TODO: Need to define initial message to send


<http://localhost:8005/protocols/buy_protocol> a bspl:Protocol.
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