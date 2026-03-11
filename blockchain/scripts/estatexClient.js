require("dotenv").config();
const { ethers } = require("ethers");

const abi = [
  "function registerProperty(uint256 propertyId,uint256 totalShares,bytes32 titleHash,bytes32 ownershipHash)",
  "function invest(uint256 propertyId,uint256 shares)",
  "function transferShares(uint256 propertyId,address to,uint256 shares)",
];

async function main() {
  const [, , command, ...args] = process.argv;
  const rpcUrl = process.env.CHAIN_RPC_URL || "http://127.0.0.1:8545";
  const privateKey = process.env.CHAIN_PRIVATE_KEY;
  const contractAddress = process.env.CHAIN_CONTRACT_ADDRESS;

  if (!privateKey || !contractAddress) {
    console.log(JSON.stringify({ txHash: "mock_tx_missing_chain_config" }));
    return;
  }

  const provider = new ethers.JsonRpcProvider(rpcUrl);
  const wallet = new ethers.Wallet(privateKey, provider);
  const contract = new ethers.Contract(contractAddress, abi, wallet);

  let tx;

  if (command === "registerProperty") {
    const [propertyId, totalShares] = args;
    tx = await contract.registerProperty(propertyId, totalShares, ethers.ZeroHash, ethers.ZeroHash);
  } else if (command === "invest") {
    const [propertyId, , shares] = args;
    tx = await contract.invest(propertyId, shares);
  } else if (command === "transfer") {
    const [propertyId, , toAddress, shares] = args;
    tx = await contract.transferShares(propertyId, toAddress, shares);
  } else {
    throw new Error("Unsupported command");
  }

  await tx.wait();
  console.log(JSON.stringify({ txHash: tx.hash }));
}

main().catch((error) => {
  console.log(JSON.stringify({ txHash: "mock_tx_error", error: String(error.message || error) }));
});
