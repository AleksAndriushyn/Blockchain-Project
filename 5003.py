import hashlib
import time
import json
from flask import Flask, jsonify, request
from uuid import uuid4
from urllib.parse import urlparse
import requests

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions=[]
        self.nodes = set()

        self.new_block(proof=12112000,previous_hash="andriushyn")

    def new_block(self,proof,previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.last_block),
        }

        self.current_transactions=[]
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount':  amount
            })
        return self.last_block['index']+1

    def proof_of_work(self,last_proof):
        proof = 0
        while self.valid_proof(last_proof,proof) == False:
            proof += 1
        return proof

    def register_node(self, address):
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

    def valid_chain(self, chain):
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Перевірка правильності хеша блока
            if block['previous_hash'] != self.hash(last_block):
                return False
            # Перевіряємо, чи є підтвердження роботи коректним
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False

            last_block = block
            current_index += 1

        return True

    def resolve_conflicts(self):
        neighbours = self.nodes
        new_chain = None
        # Шукаємо тільки ланцюги, довші за наші
        max_length = len(self.chain)
        # Захоплюємо і перевіряємо всі ланцюги з усіх вузлів мережі
        for node in neighbours:
            response = requests.get(f'http://{node}/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

            # Перевіряємо, чи є довжина найдовшою, а ланцюг — валідним
            if length > max_length and self.valid_chain(chain):
                max_length = length
                new_chain = chain
                
        #Замінюємо ланцюг, якщо знайдемо інший валідний і довший
        if new_chain:
            self.chain = new_chain
            return True

        return False

    @staticmethod
    def valid_proof(last_proof,proof):
        guess = '{0}{1}'.format(last_proof,proof).encode()
        guess_hash=hashlib.sha256(guess).hexdigest()
        return guess_hash[-2:] == '03'

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

app = Flask(__name__)
node_identifier = str(uuid4()).replace('-', '')
blockchain = Blockchain()

@app.route('/mine', methods=['GET'])
def mine():
  last_block = blockchain.last_block
  last_proof = last_block['proof']
  proof = blockchain.proof_of_work(last_proof)
  
  blockchain.new_transaction(
    sender="0",
    recipient=node_identifier,
    amount=29,
  )
  
  previous_hash = blockchain.hash(last_block)
  block = blockchain.new_block(proof, previous_hash)
  response = {
    'message': "New Block Forged",
    'index': block['index'],
    'transactions': block['transactions'],
    'proof': block['proof'],
    'previous_hash': block['previous_hash'],
  }
  return jsonify(response), 200

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
  values = request.get_json()
  
  required = ['sender', 'recipient', 'amount']
  if not all(k in values for k in required):
        return 'Missing values', 400
  
  index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])
  response = {'message': 'Transaction will be added to Block {0}'.format(index)}
  return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
  response = {
    'chain': blockchain.chain,
    'length': len(blockchain.chain),
  }
  return jsonify(response), 200

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400
    for node in nodes:
        blockchain.register_node(node)
    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    print(blockchain.nodes)

    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


if __name__ == '__main__':
  app.run(host='localhost', port=5003, debug = False)
