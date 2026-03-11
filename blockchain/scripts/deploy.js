const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  const Factory = await hre.ethers.getContractFactory("EstateXFractional");
  const contract = await Factory.deploy(deployer.address);
  await contract.waitForDeployment();

  const address = await contract.getAddress();
  console.log("EstateXFractional deployed to:", address);
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
