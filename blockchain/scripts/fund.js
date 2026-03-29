const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  const contractAddress = process.env.CHAIN_CONTRACT_ADDRESS || process.argv[2];
  const amountEth = process.env.FUND_AMOUNT || process.argv[3] || "1";

  if (!contractAddress) {
    throw new Error("Missing contract address. Pass it as arg or set CHAIN_CONTRACT_ADDRESS.");
  }

  const tx = await deployer.sendTransaction({
    to: contractAddress,
    value: hre.ethers.parseEther(amountEth),
  });

  await tx.wait();
  console.log(`Funded ${contractAddress} with ${amountEth} ETH. Tx: ${tx.hash}`);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
