// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import "@openzeppelin/contracts/access/Ownable.sol";

contract EstateXFractional is Ownable {
    struct PropertyMeta {
        uint256 totalShares;
        uint256 soldShares;
        bytes32 titleHash;
        bytes32 ownershipHash;
        bool exists;
    }

    mapping(uint256 => PropertyMeta) public properties;
    mapping(uint256 => mapping(address => uint256)) public ownership;

    event PropertyRegistered(uint256 indexed propertyId, uint256 totalShares, bytes32 titleHash, bytes32 ownershipHash);
    event Invested(uint256 indexed propertyId, address indexed investor, uint256 shares);
    event SharesTransferred(uint256 indexed propertyId, address indexed from, address indexed to, uint256 shares);

    constructor(address initialOwner) Ownable(initialOwner) {}

    function registerProperty(
        uint256 propertyId,
        uint256 totalShares,
        bytes32 titleHash,
        bytes32 ownershipHash
    ) external onlyOwner {
        require(!properties[propertyId].exists, "property exists");
        require(totalShares > 0, "shares required");

        properties[propertyId] = PropertyMeta({
            totalShares: totalShares,
            soldShares: 0,
            titleHash: titleHash,
            ownershipHash: ownershipHash,
            exists: true
        });

        emit PropertyRegistered(propertyId, totalShares, titleHash, ownershipHash);
    }

    function invest(uint256 propertyId, uint256 shares) external {
        PropertyMeta storage p = properties[propertyId];
        require(p.exists, "unknown property");
        require(shares > 0, "invalid shares");
        require(p.soldShares + shares <= p.totalShares, "oversell blocked");

        p.soldShares += shares;
        ownership[propertyId][msg.sender] += shares;

        emit Invested(propertyId, msg.sender, shares);
    }

    function transferShares(uint256 propertyId, address to, uint256 shares) external {
        PropertyMeta storage p = properties[propertyId];
        require(p.exists, "unknown property");
        require(to != address(0), "invalid recipient");
        require(shares > 0, "invalid shares");
        require(ownership[propertyId][msg.sender] >= shares, "insufficient shares");

        ownership[propertyId][msg.sender] -= shares;
        ownership[propertyId][to] += shares;

        emit SharesTransferred(propertyId, msg.sender, to, shares);
    }

    function getOwnership(uint256 propertyId, address investor) external view returns (uint256) {
        return ownership[propertyId][investor];
    }
}
