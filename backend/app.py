from flask import Flask, jsonify, request
from flask_cors import CORS
import time
import json
import hashlib
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding

# Blockchain and Wallet code here

class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_transactions = []
        self.create_genesis_block()

    def create_genesis_block(self):
        # Create the first block (genesis block)
        genesis_block = {
            'index': 0,
            'timestamp': time.time(),
            'transactions': [],
            'previous_hash': '0',
            'nonce': 0
        }
        genesis_block['hash'] = self.hash_block(genesis_block)
        self.chain.append(genesis_block)

    def hash_block(self, block):
        # Create a SHA-256 hash of a block
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def add_block(self, block):
        # Add a new block to the chain
        self.chain.append(block)
        # Clear pending transactions after adding block
        self.pending_transactions = []

    def create_block(self, nonce, previous_hash):
        # Create a new block with the pending transactions
        block = {
            'index': len(self.chain),
            'timestamp': time.time(),
            'transactions': self.pending_transactions,
            'previous_hash': previous_hash,
            'nonce': nonce
        }
        block['hash'] = self.hash_block(block)
        return block

    def add_transaction(self, sender, recipient, amount, signature):
        # Add a transaction to the list of pending transactions
        transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'signature': signature
        }
        self.pending_transactions.append(transaction)

    def proof_of_work(self, previous_hash):
        # Basic proof of work: find a nonce such that the hash has 4 leading zeros
        nonce = 0
        while True:
            block = self.create_block(nonce, previous_hash)
            if block['hash'][:4] == '0000':  # Difficulty level: 4 leading zeros
                return block
            nonce += 1

    def is_valid_chain(self):
        # Check the integrity of the blockchain
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            # Check if the previous hash of the current block matches the actual hash of the previous block
            if current_block['previous_hash'] != previous_block['hash']:
                print(f"Previous hash mismatch at block {i}")
                return False

            # Recompute the hash of the current block (excluding the 'hash' field itself)
            block_copy = current_block.copy()
            block_copy.pop('hash')  # Remove the hash field from the block copy
            recalculated_hash = self.hash_block(block_copy)
            if current_block['hash'] != recalculated_hash:
                print(f"Hash mismatch at block {i}")
                print(f"Expected: {current_block['hash']}, but got: {recalculated_hash}")
                return False

        return True

    
class CryptoWallet:
    def __init__(self, blockchain):
        # Generate RSA private and public keys
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()

        # Initialize wallet balance
        self.balance = 0
        self.blockchain = blockchain  # Reference to the blockchain

    def get_public_key_pem(self):
        # Get the public key in PEM format
        return self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

    def save_keys(self):
        # Save the private key to a PEM file
        pem = self.private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
        with open("private_key.pem", "wb") as f:
            f.write(pem)

        # Save the public key to a PEM file
        pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        with open("public_key.pem", "wb") as f:
            f.write(pem)

    def load_keys(self):
        # Load the private key from a PEM file
        with open("private_key.pem", "rb") as f:
            private_key_pem = f.read()
        self.private_key = serialization.load_pem_private_key(
            private_key_pem,
            password=None,
            backend=default_backend()
        )

        # Load the public key from a PEM file
        with open("public_key.pem", "rb") as f:
            public_key_pem = f.read()
        self.public_key = serialization.load_pem_public_key(
            public_key_pem,
            backend=default_backend()
        )

    def check_balance(self):
        # Check the wallet balance
        print(f"Wallet balance: {self.balance} coins")

    def send_coins(self, amount, recipient_public_key):
        if self.balance >= amount:
            # Create a transaction
            transaction = f"Send {amount} coins to {recipient_public_key}"

            # Sign the transaction with the private key
            signature = self.private_key.sign(
                transaction.encode(),
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )

            # Add the transaction to the blockchain's pending transactions
            self.blockchain.add_transaction(
                sender=self.get_public_key_pem(),
                recipient=recipient_public_key,
                amount=amount,
                signature=signature.hex()
            )

            # Mine a new block (proof-of-work)
            last_block = self.blockchain.chain[-1]
            previous_hash = last_block['hash']
            new_block = self.blockchain.proof_of_work(previous_hash)  # Mine a new block
            self.blockchain.add_block(new_block)  # Add the new block to the chain

            print(f"Transaction added to the blockchain: {transaction}")
            self.balance -= amount
            return {"status": "success", "transaction": transaction}
        else:
            print("Insufficient balance")
            return {"status": "error", "message": "Insufficient balance"}


    def receive_coins(self, amount):
        # Receive coins and update the balance
        self.balance += amount
        print(f"Received {amount} coins. New balance: {self.balance} coins")


# Initialize Flask app and enable CORS
app = Flask(__name__)
CORS(app)

# Create global instances for the blockchain and wallet
blockchain = Blockchain()
wallet = CryptoWallet(blockchain)

@app.route('/balance', methods=['GET'])
def get_balance():
    # Fetch balance for the sender (in a real scenario, sender public key should be authenticated)
    sender = request.args.get('sender')  # Get sender from query parameters
    if sender:
        # Return wallet's balance
        return jsonify({"balance": wallet.balance})
    else:
        return jsonify({"balance": 0})  # Return 0 if sender does not exist

@app.route('/api/send', methods=['POST'])
def send_transaction():
    data = request.json  # Extract the JSON data from the request body
    sender = data['sender']
    recipient = data['recipient']
    amount = data['amount']
    
    # Send coins from the wallet
    wallet.send_coins(amount, recipient)
    
    return jsonify({
        "status": "success",
        "message": f"{amount} coins sent from {sender} to {recipient}"
    })

@app.route('/chain', methods=['GET'])
def get_chain():
    # Return the blockchain
    return jsonify({"chain": blockchain.chain})

@app.route('/pending_transactions', methods=['GET'])
def get_pending_transactions():
    return jsonify({"pending_transactions": blockchain.pending_transactions})

@app.route('/mine', methods=['GET'])
def mine_block():
    last_block = blockchain.chain[-1]
    previous_hash = last_block['hash']
    new_block = blockchain.proof_of_work(previous_hash)
    blockchain.add_block(new_block)
    return jsonify({"message": "New block mined", "block": new_block})

@app.route('/api/send', methods=['POST'])
def send_transaction():
    data = request.json
    sender = data['sender']
    recipient = data['recipient']
    amount = data['amount']
    
    result = wallet.send_coins(amount, recipient)
    
    if result["status"] == "success":
        return jsonify({
            "status": "success",
            "message": f"{amount} coins sent from {sender} to {recipient}",
            "transaction": result["transaction"]
        })
    else:
        return jsonify({
            "status": "error",
            "message": result["message"]
        }), 400

if __name__ == '__main__':
    app.run(debug=True)
