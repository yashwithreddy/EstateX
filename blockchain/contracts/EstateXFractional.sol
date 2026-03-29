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
    event SharesPurchased(uint256 indexed propertyId, address indexed investor, uint256 shares);
    event SharesTransferred(uint256 indexed propertyId, address indexed from, address indexed to, uint256 shares);
    event RoiPaid(uint256 indexed propertyId, address indexed investor, uint256 amount);

    constructor(address initialOwner) Ownable(initialOwner) {}

    function createProperty(uint256 propertyId, uint256 totalShares) external onlyOwner {
        require(!properties[propertyId].exists, "property exists");
        require(totalShares > 0, "shares required");

        properties[propertyId] = PropertyMeta({
            totalShares: totalShares,
            soldShares: 0,
            titleHash: bytes32(0),
            ownershipHash: bytes32(0),
            exists: true
        });

        emit PropertyRegistered(propertyId, totalShares, bytes32(0), bytes32(0));
    }

    // Since backend signs on behalf of user, we allow passing 'investor' or use msg.sender
    function buyShares(uint256 propertyId, address investor, uint256 shares) external {
        PropertyMeta storage p = properties[propertyId];
        require(p.exists, "unknown property");
        require(shares > 0, "invalid shares");
        require(p.soldShares + shares <= p.totalShares, "oversell blocked");

        p.soldShares += shares;
        ownership[propertyId][investor] += shares;

        emit SharesPurchased(propertyId, investor, shares);
    }

    function transferShares(uint256 propertyId, address from, address to, uint256 shares) external {
        PropertyMeta storage p = properties[propertyId];
        require(p.exists, "unknown property");
        require(to != address(0), "invalid recipient");
        require(shares > 0, "invalid shares");
        require(ownership[propertyId][from] >= shares, "insufficient shares");
        // If not using allowances, ensure caller is admin or the 'from' address
        require(msg.sender == from || msg.sender == owner(), "not authorized");

        ownership[propertyId][from] -= shares;
        ownership[propertyId][to] += shares;

        emit SharesTransferred(propertyId, from, to, shares);
    }

    function payout(uint256 propertyId, address payable investor, uint256 amount) external onlyOwner {
        require(properties[propertyId].exists, "unknown property");
        require(investor != address(0), "invalid recipient");
        require(amount > 0, "invalid amount");
        require(address(this).balance >= amount, "insufficient balance");

        (bool success, ) = investor.call{value: amount}("");
        require(success, "transfer failed");

        emit RoiPaid(propertyId, investor, amount);
    }

    receive() external payable {}

    function getShares(uint256 propertyId, address investor) external view returns (uint256) {
        return ownership[propertyId][investor];
    }
}
