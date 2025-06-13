# blockchain/ledger.py
import hashlib
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ComplaintLedger:
    def __init__(self):
        self.chain = []
        self.current_complaints = []
        # Create the genesis block
        self.new_block(proof=1, previous_hash='1') # Changed genesis proof to 1
        logger.info("ComplaintLedger initialized with genesis block.")

    def new_block(self, proof, previous_hash=None):
        """
        Creates a new Block in the Blockchain.
        Args:
            proof (int): The proof given by the Proof of Work algorithm.
            previous_hash (str, optional): Hash of previous Block. Defaults to None.
        Returns:
            dict: The new Block.
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': str(datetime.now()),
            'complaints': self.current_complaints,
            'proof': proof,
            'previous_hash': previous_hash or self.hash_block(self.chain[-1]) if self.chain else '1',
        }
        # Reset the current list of complaints
        self.current_complaints = []
        self.chain.append(block)
        logger.info(f"New block created: Index {block['index']}, Proof {block['proof']}")
        return block

    def add_complaint(self, complaint_data: dict) -> str:
        """
        Adds a new complaint to the list of complaints to be included in the next block.
        After adding, it immediately mines a new block for simplicity.
        Args:
            complaint_data (dict): The complaint details.
        Returns:
            str: The hash of the newly mined block.
        """
        self.current_complaints.append(complaint_data)
        logger.info(f"Complaint added to pending list: {complaint_data.get('db_id', 'N/A')}")

        # Mine a block immediately after adding a complaint for real-time updates
        # In a production blockchain, mining occurs periodically or based on a transaction threshold.
        last_block = self.chain[-1]
        proof = self.proof_of_work(last_block['proof'])
        new_block = self.new_block(proof, self.hash_block(last_block))
        new_block_hash = self.hash_block(new_block)
        logger.info(f"New block mined after complaint: {new_block_hash}")
        return new_block_hash

    @staticmethod
    def hash_block(block) -> str:
        """
        Creates a SHA-256 hash of a Block.
        Args:
            block (dict): Block to hash.
        Returns:
            str: SHA-256 hash string.
        """
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def proof_of_work(self, last_proof: int) -> int:
        """
        Simple Proof of Work Algorithm:
        - Find a number p' such that hash(pp') contains leading 4 zeroes
        - Where p is the previous proof, and p' is the new proof.
        Args:
            last_proof (int): The proof from the previous block.
        Returns:
            int: The new proof.
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof: int, proof: int) -> bool:
        """
        Validates the Proof: Does hash(last_proof, proof) contain 4 leading zeroes?
        Args:
            last_proof (int): Previous proof.
            proof (int): Current proof.
        Returns:
            bool: True if valid, False otherwise.
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

    def verify_chain(self) -> bool:
        """
        Determines if the entire blockchain is valid.
        Checks hash linking and Proof of Work for each block.
        Returns:
            bool: True if valid, False otherwise.
        """
        if not self.chain:
            logger.warning("Blockchain is empty, cannot verify.")
            return False

        current_block_index = 0
        while current_block_index < len(self.chain):
            current_block = self.chain[current_block_index]
            
            if current_block_index > 0:
                previous_block = self.chain[current_block_index - 1]
                # Check that the hash of the previous block in the chain is correct
                if current_block['previous_hash'] != self.hash_block(previous_block):
                    logger.error(f"Chain validation failed: Block {current_block_index} previous_hash mismatch.")
                    return False

            # Check that the Proof of Work is correct for the current block
            # (validates proof based on previous block's proof)
            # For the genesis block, this might be handled specially or use a predefined valid proof.
            if current_block_index > 0:
                if not self.valid_proof(self.chain[current_block_index - 1]['proof'], current_block['proof']):
                    logger.error(f"Chain validation failed: Block {current_block_index} Proof of Work invalid.")
                    return False
            else: # For genesis block, check if its proof is valid as per initial setup
                if not self.valid_proof(current_block['proof'], 1): # Check if genesis proof is "valid" with itself or fixed val
                     # Adjust this logic if your genesis proof is not '1' for example
                    pass # Or implement specific genesis block PoW check

            current_block_index += 1
        
        logger.info("Blockchain verified successfully.")
        return True