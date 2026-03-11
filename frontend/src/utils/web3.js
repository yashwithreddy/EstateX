import { BrowserProvider, Contract } from 'ethers';
import estatexAbi from './estatexAbi.json';

export async function connectWallet() {
  if (!window.ethereum) throw new Error('MetaMask not found');
  const provider = new BrowserProvider(window.ethereum);
  const accounts = await provider.send('eth_requestAccounts', []);
  return accounts[0];
}

export async function investOnChain(propertyId, shares) {
  const contractAddress = import.meta.env.VITE_CONTRACT_ADDRESS;
  if (!contractAddress || !window.ethereum) return null;

  const provider = new BrowserProvider(window.ethereum);
  const signer = await provider.getSigner();
  const contract = new Contract(contractAddress, estatexAbi, signer);
  const tx = await contract.invest(propertyId, shares);
  await tx.wait();
  return tx.hash;
}
