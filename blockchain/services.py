import json
from pathlib import Path

from web3 import Web3
from django.conf import settings


BASE_DIR = Path(settings.BASE_DIR)

CONTRACT_DATA_PATH = (
    BASE_DIR / 'blockchain' / 'contract_data.json'
)
CONTRACT_ADDRESS_PATH = (
    BASE_DIR / 'blockchain' / 'contract_address.txt'
)


with open(
    CONTRACT_DATA_PATH,
    'r',
    encoding='utf-8'
) as file:
    CONTRACT_DATA = json.load(file)


ABI = CONTRACT_DATA['abi']
BYTECODE = CONTRACT_DATA['bytecode']


from web3 import Web3

GANACHE_URL = "http://127.0.0.1:7545"

_web3 = None


def get_web3():
    global _web3

    if _web3 is None:
        _web3 = Web3( Web3.HTTPProvider(GANACHE_URL))

    if not _web3.is_connected():
        raise ConnectionError(
            "Cannot connect to Ganache. "
            "Please make sure Ganache is running."
        )

    return _web3


def get_account():
    web3 = get_web3()
    return web3.eth.accounts[0]

_contract = None

def deploy_contract(web3, account):
    global _contract

    # Reuse the contract if already loaded
    if _contract is not None:
        return _contract

    # Check whether the contract address was saved
    if CONTRACT_ADDRESS_PATH.exists():

        address = CONTRACT_ADDRESS_PATH.read_text(
            encoding='utf-8'
        ).strip()

        if address:

            address = Web3.to_checksum_address(address)

            code = web3.eth.get_code(address)

            if code and code != b'':

                _contract = web3.eth.contract(
                    address=address,
                    abi=ABI
                )

                return _contract

    # Deploy a new contract if no existing contract is available
    contract_factory = web3.eth.contract(
        abi=ABI,
        bytecode=BYTECODE
    )

    transaction_hash = contract_factory.constructor().transact({
        'from': account
    })

    receipt = web3.eth.wait_for_transaction_receipt(
        transaction_hash
    )

    if receipt['status'] != 1:
        raise Exception('Contract deployment failed.')

    address = receipt['contractAddress']

    _contract = web3.eth.contract(
        address=address,
        abi=ABI
    )

    # Save the contract address
    CONTRACT_ADDRESS_PATH.write_text(
        address,
        encoding='utf-8'
    )

    print('Smart contract deployed:', address)

    return _contract



def register_document(document_id, document_hash, version):
    web3 = get_web3()
    account = get_account()

    # Deploy the smart contract
    contract = deploy_contract(web3, account)

    # Convert SHA-256 hash into bytes
    hash_bytes = bytes.fromhex(document_hash)

    if len(hash_bytes) != 32:
        raise ValueError("Document hash must be exactly 32 bytes.")

    # Register document on the blockchain
    transaction_hash = contract.functions.registerDocument(
        str(document_id),
        hash_bytes,
        int(version)
    ).transact({
        "from": account
    })

    # Get transaction receipt
    receipt = web3.eth.wait_for_transaction_receipt(
        transaction_hash
    )

    if receipt["status"] != 1:
        raise Exception("Document registration transaction failed.")

    return {
        "transaction_hash": receipt["transactionHash"].hex(),
        "block_number": receipt["blockNumber"],
        "status": receipt["status"],
        "gas_used": receipt["gasUsed"],
        "contract_address": contract.address
    }


def verify_document(document_id, document_hash, version):
    web3 = get_web3()
    account = get_account()

    # Get the deployed contract
    contract = deploy_contract(web3, account)

    # Convert SHA-256 hash into bytes
    hash_bytes = bytes.fromhex(document_hash)

    if len(hash_bytes) != 32:
        raise ValueError("Document hash must be exactly 32 bytes.")

    # Verify the document using the smart contract
    result = contract.functions.verifyDocument(
        str(document_id),
        hash_bytes,
        int(version)
    ).call()

    return result
