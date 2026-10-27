from web3 import Web3

from .services import (
    get_web3,
    get_account,
    ABI,
    BYTECODE
)


def deploy_contract():

    web3 = get_web3()

    account = get_account()

    contract = web3.eth.contract(
        abi=ABI,
        bytecode=BYTECODE
    )

    transaction_hash = contract.constructor().transact(
        {
            'from': account
        }
    )

    transaction_receipt = (
        web3.eth.wait_for_transaction_receipt(
            transaction_hash
        )
    )

    print(
        "Contract Address:"
    )

    print(
        transaction_receipt.contractAddress
    )

    return transaction_receipt.contractAddress