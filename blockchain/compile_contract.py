import json
from pathlib import Path

from solcx import compile_standard


BASE_DIR = Path(__file__).resolve().parent

contract_path = (
    BASE_DIR
    / "smart_contract"
    / "DocumentRegistry.sol"
)

with open(contract_path, "r", encoding="utf-8") as file:
    contract_source = file.read()


compiled = compile_standard(
    {
        "language": "Solidity",
        "sources": {
            "DocumentRegistry.sol": {
                "content": contract_source
            }
        },
        "settings": {
            "evmVersion": "paris",
            "optimizer": {
                "enabled": True,
                "runs": 200
            },
            "outputSelection": {
                "*": {
                    "*": [
                        "abi",
                        "evm.bytecode"
                    ]
                }
            }
        }
    },
    solc_version="0.8.20"
)


contract_data = (
    compiled["contracts"]
    ["DocumentRegistry.sol"]
    ["DocumentRegistry"]
)

output = {
    "abi": contract_data["abi"],
    "bytecode": contract_data["evm"]["bytecode"]["object"]
}

output_path = BASE_DIR / "contract_data.json"

with open(output_path, "w", encoding="utf-8") as file:
    json.dump(output, file, indent=4)

print("Contract compiled successfully.")
print("EVM version: Paris")
print("ABI entries:", len(output["abi"]))
print("Bytecode length:", len(output["bytecode"]))

