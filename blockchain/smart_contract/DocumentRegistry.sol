// SPDX-License-Identifier: MIT

pragma solidity ^0.8.20;


contract DocumentRegistry {

    struct DocumentRecord {

        bytes32 documentHash;

        address issuer;

        uint256 timestamp;

        uint256 version;

        bool revoked;

        bool exists;
    }


    mapping(
        bytes32 => DocumentRecord
    ) private records;


    function createKey(
        string memory documentId,
        uint256 version
    )
        public
        pure
        returns (bytes32)
    {
        return keccak256(
            abi.encodePacked(
                documentId,
                version
            )
        );
    }


    function registerDocument(

        string memory documentId,

        bytes32 documentHash,

        uint256 version

    )
        public
    {

        bytes32 key = createKey(
            documentId,
            version
        );

        require(
            !records[key].exists,
            "Document already registered"
        );


        records[key] = DocumentRecord(

            documentHash,

            msg.sender,

            block.timestamp,

            version,

            false,

            true

        );
    }


    function verifyDocument(

        string memory documentId,

        bytes32 documentHash,

        uint256 version

    )
        public
        view
        returns (bool)
    {

        bytes32 key = createKey(
            documentId,
            version
        );

        DocumentRecord memory record =
            records[key];


        if (!record.exists) {

            return false;

        }


        if (record.revoked) {

            return false;

        }


        return (
            record.documentHash == documentHash
        );
    }


    function revokeDocument(

        string memory documentId,

        uint256 version

    )
        public
    {

        bytes32 key = createKey(
            documentId,
            version
        );


        require(
            records[key].exists,
            "Document not found"
        );


        records[key].revoked = true;
    }


    function getDocument(

        string memory documentId,

        uint256 version

    )
        public
        view
        returns (

            bytes32,
            address,
            uint256,
            uint256,
            bool,
            bool

        )
    {

        bytes32 key = createKey(
            documentId,
            version
        );


        DocumentRecord memory record =
            records[key];


        return (

            record.documentHash,

            record.issuer,

            record.timestamp,

            record.version,

            record.revoked,

            record.exists

        );
    }
}