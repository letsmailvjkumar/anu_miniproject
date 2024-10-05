import React, { useState } from "react";
import './App.css';

const App = () => {
  const [balance, setBalance] = useState(0);
  const [recipient, setRecipient] = useState('');
  const [amount, setAmount] = useState('');
  const [blockchainData, setBlockchainData] = useState('');
  const [publicKey, setPublicKey] = useState('');  // Placeholder for actual public key

  // Fetch wallet balance
  const fetchBalance = async () => {
    try {
      const response = await fetch('http://localhost:5000/balance?sender=' + publicKey);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setBalance(data.balance);
    } catch (error) {
      console.error('Error fetching balance:', error);
      alert(`Failed to fetch balance: ${error.message}`);
    }
  };

  // Send coins
  const sendTransaction = async () => {
    if (!recipient || !amount) {
      alert("Please enter recipient and amount.");
      return;
    }
    
    const transactionData = {
      sender: publicKey,  // Use the actual public key of the sender
      recipient: recipient,
      amount: parseInt(amount),
    };

    try {
      const response = await fetch('http://localhost:5000/api/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(transactionData),
      });

      const data = await response.json();
      if (response.ok) {
        alert(data.message);
        fetchBalance();  // Update balance after transaction
        setAmount('');
        setRecipient('');
      } else {
        alert(data.message);
      }
    } catch (error) {
      console.error('Error sending transaction:', error);
      alert('Error sending transaction. Please check the console for details.');
    }
  };

  // Fetch blockchain
  const fetchChain = async () => {
    try {
      const response = await fetch('http://localhost:5000/chain');
      const data = await response.json();
      setBlockchainData(JSON.stringify(data.chain, null, 2));
    } catch (error) {
      console.error('Error fetching blockchain:', error);
    }
  };

  return (
    <div className="container">
      <h1>Blockchain Wallet</h1>

      <div className="wallet-info">
        <h2>Your Wallet</h2>
        <input 
          type="text" 
          value={publicKey} 
          onChange={(e) => setPublicKey(e.target.value)} 
          placeholder="Your Public Key"
        />
        <p>Balance: <span>{balance}</span> coins</p>
        <button onClick={fetchBalance}>Check Balance</button>
      </div>

      <div className="transaction">
        <h2>Send Coins</h2>
        <input
          type="text"
          value={recipient}
          onChange={(e) => setRecipient(e.target.value)}
          placeholder="Recipient Public Key"
        />
        <input
          type="number"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          placeholder="Amount"
          min="1"
        />
        <button onClick={sendTransaction}>Send Coins</button>
      </div>

      <div className="blockchain">
        <h2>Blockchain</h2>
        <button onClick={fetchChain}>Show Blockchain</button>
        <pre>{blockchainData}</pre>
      </div>
    </div>
  );
};

export default App;
