# provides the protocol
from flask import Flask, request, jsonify




file = open('buy.bspl','r')
buy_protocol = file.read()
file.close()


app = Flask(__name__)


@app.route('/protocol', methods=['GET'])
def callback():
    return buy_protocol, 200

if __name__ == '__main__':
    app.run('localhost',8005)