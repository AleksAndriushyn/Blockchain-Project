import Blockchain
import hashlib
if __name__ == '__main__':
    b = Blockchain.aoo_Blockchain()
    b.aoo_new_transaction(sender="Leksus", recipient="Zheka", amount=15)
    b.aoo_new_transaction(sender="Lena", recipient="Milena", amount=3422)
    b.aoo_new_block(proof=b.aoo_proof_of_work(last_proof=b.aoo_last_block['proof']))
    print(b.aoo_chain)
    proof_1 = b.aoo_chain[0]['proof']
    proof_2 = b.aoo_chain[1]['proof']
    print(hashlib.sha256(f'{proof_1}{proof_2}'.encode()).hexdigest())
