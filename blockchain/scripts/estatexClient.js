require("dotenv").config();
const { ethers } = require("ethers");

const abi = [
  "function createProperty(uint256 propertyId,uint256 totalShares)",
  "function buyShares(uint256 propertyId,address investor,uint256 shares)",
  "function transferShares(uint256 propertyId,address from,address to,uint256 shares)",
  "function payout(uint256 propertyId,address investor,uint256 amount)",
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

  if (command === "registerProperty" || command === "createProperty") {
    const [propertyId, totalShares] = args;
    tx = await contract.createProperty(propertyId, totalShares);
  } else if (command === "invest" || command === "buyShares") {
    const [propertyId, investor, shares] = args;
    tx = await contract.buyShares(propertyId, investor, shares);
  } else if (command === "transfer" || command === "transferShares") {
    const [propertyId, fromAddress, toAddress, shares] = args;
    tx = await contract.transferShares(propertyId, fromAddress, toAddress, shares);
  } else if (command === "payout") {
    const [propertyId, investor, amount] = args;
    tx = await contract.payout(propertyId, investor, amount);
  } else {
    throw new Error("Unsupported command");
  }

  await tx.wait();
  console.log(JSON.stringify({ txHash: tx.hash }));
}

main().catch((error) => {
  console.log(JSON.stringify({ txHash: "mock_tx_error", error: String(error.message || error) }));
});
