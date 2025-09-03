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


app = Flask(__name__)


@app.route('/protocol', methods=['GET'])
def callback():
    return buy_protocol, 200

if __name__ == '__main__':
    app.run('localhost',8005)