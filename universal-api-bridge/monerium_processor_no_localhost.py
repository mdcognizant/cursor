#!/usr/bin/env python3
"""
Monerium Processor - No Localhost Version

Processes request files from the HTML interface and generates responses
using real OpenAI API and Monerium simulations.

Usage:
    python monerium_processor_no_localhost.py [request_file.json]
    python monerium_processor_no_localhost.py --watch
    python monerium_processor_no_localhost.py --batch *.json
"""

import sys
import json
import os
import time
import glob
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from openai import OpenAI
import argparse

class MoneriumProcessor:
    def __init__(self):
        # OpenAI configuration
        self.openai_api_key = "YOUR_OPENAI_API_KEY_HERE"
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        
        # File paths
        self.base_path = Path(__file__).parent
        self.request_pattern = "monerium_request_*.json"
        self.response_dir = self.base_path / "responses"
        self.response_dir.mkdir(exist_ok=True)
        
        print("🚀 Monerium Processor - No Localhost Version")
        print("✅ OpenAI client initialized")
        print(f"📂 Watching for: {self.request_pattern}")
        print(f"📁 Response directory: {self.response_dir}")
        
    def parse_intent(self, message: str) -> str:
        """Determine if message is for Monerium API or general LLM chat."""
        message_lower = message.lower()
        
        monerium_keywords = [
            "balance", "send", "transfer", "iban", "wallet", 
            "monerium", "payment", "withdraw", "deposit", "money"
        ]
        
        for keyword in monerium_keywords:
            if keyword in message_lower:
                return "monerium"
        
        return "llm"
    
    def call_openai(self, message: str) -> str:
        """Call OpenAI API directly."""
        try:
            print("🧠 Calling OpenAI API...")
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": message}],
                max_tokens=200,
                temperature=0.7
            )
            result = response.choices[0].message.content.strip()
            print("✅ OpenAI response received")
            return result
        except Exception as e:
            error_msg = f"OpenAI API error: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg
    
    def call_monerium_api(self, message: str) -> str:
        """Handle Monerium API operations with enhanced responses."""
        message_lower = message.lower()
        
        if "balance" in message_lower:
            return """💰 Your Monerium Balance

🏦 Account Overview:
• GBPe (Euro Stablecoin): £1,247.83
• EURe (Euro Stablecoin): €532.45  
• USDe (USD Stablecoin): $890.12

💳 Available Funds: £1,247.83
🔒 Reserved Funds: £0.00
📊 Total Portfolio: ~$2,670 USD

📅 Last Updated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """
🔄 Real-time sync with blockchain

🏛️ Regulatory Status: ✅ EU Licensed EMI
🔐 Security: Multi-signature protection active"""
            
        elif "transfer" in message_lower or "send" in message_lower:
            return """💸 Monerium Transfer Service

📋 Transfer Options:
• SEPA Instant (EU): 1-10 minutes
• Bank Transfer (Global): 1-3 business days
• Blockchain Transfer: 1-5 minutes

💰 Current Limits:
• Daily: £10,000 / €11,000 / $12,000
• Monthly: £100,000 / €110,000 / $120,000
• Per Transaction: £5,000 / €5,500 / $6,000

📝 Required Information:
• Recipient IBAN or wallet address
• Transfer amount and currency
• Reference message (optional)

🔐 Security Features:
• 2FA authentication required
• Email confirmation
• SMS verification for large amounts

💡 Example: "Send £100 to GB29 ABCD 1234 5678 9012 3456"
🆘 Need help? Contact support@monerium.com"""
            
        elif "iban" in message_lower:
            return """🏦 Your Monerium IBAN Details

📍 Primary Account:
IBAN: GB29 MNRM 1234 5678 9012 3456
Account Name: Your Name
Bank Name: Monerium
SWIFT/BIC: MNRMGB2L

🌍 Alternative Accounts:
🇪🇺 EUR: IS14 0159 2600 7654 5510 7303 39
🇺🇸 USD: US64 MNRM 0000 1234 5678 90

💷 Supported Currencies:
• GBPe (Euro-backed Pound)
• EURe (Euro Stablecoin)  
• USDe (USD Stablecoin)

📱 How to use:
• Share IBAN for receiving funds
• Incoming funds converted to stablecoins
• Available in your digital wallet within hours

🔗 Integration:
• Compatible with all SEPA banks
• Works with traditional banking apps
• Seamless crypto-fiat bridge"""
            
        elif "deposit" in message_lower:
            return """📥 Deposit Funds to Monerium

🏦 Bank Transfer:
• Send GBP/EUR/USD to your Monerium IBAN
• Reference: Your wallet address
• Processing: 1-4 hours during business days

💳 Card Deposit:
• Instant deposits via debit/credit card
• Fee: 1.5% + €0.25
• Limits: €500 daily, €2,000 monthly

🔗 Crypto Transfer:
• Send existing stablecoins to your wallet
• Supported: USDC, USDT, DAI
• Network: Ethereum, Polygon, BSC

⚡ Processing Times:
• Bank transfer: 1-4 hours
• Card payment: Instant
• Crypto transfer: 5-15 minutes

💡 All deposits are 1:1 backed by reserves
🔐 Funds are segregated and protected"""
            
        elif "withdraw" in message_lower:
            return """📤 Withdraw from Monerium

🏦 Bank Withdrawal:
• Direct to your linked bank account
• Same-day processing (business hours)
• No fees for SEPA transfers

💳 Supported Methods:
• SEPA transfer (EUR) - Free
• Swift transfer (Global) - €15 fee
• Faster payments (UK) - Free

💰 Withdrawal Limits:
• Daily: £10,000 / €11,000 / $12,000
• Weekly: £50,000 / €55,000 / $60,000
• Monthly: £200,000 / €220,000 / $240,000

⏱️ Processing Times:
• SEPA: Same day
• UK Faster Payments: 2 hours
• International Swift: 1-3 days

🔐 Security Requirements:
• Email confirmation required
• 2FA authentication
• 24-hour delay for new withdrawal addresses

💡 Minimum withdrawal: €10 equivalent"""
            
        elif "wallet" in message_lower:
            return """👛 Your Monerium Wallet Information

🔗 Primary Wallet Address:
0x1234567890abcdef1234567890abcdef12345678

⚡ Network Details:
• Primary: Ethereum Mainnet
• Test: Sepolia Testnet  
• Gas optimization: Layer 2 ready

🪙 Token Holdings:
• GBPe: 1,247.83 tokens
• EURe: 532.45 tokens
• USDe: 890.12 tokens

🔐 Security Features:
• Multi-signature protection
• Cold storage integration
• Hardware wallet compatible

📱 Compatible Wallets:
• MetaMask ✅
• WalletConnect ✅
• Coinbase Wallet ✅
• Ledger Hardware ✅
• Trezor Hardware ✅

🌐 DeFi Integration:
• Uniswap trading ✅
• Compound lending ✅
• Aave protocols ✅

⚙️ Smart Contract:
• Audited by CertiK ✅
• Upgradeable proxy pattern
• Pause functionality for security"""
            
        else:
            return """🏦 Monerium Services Overview

💰 Account Management:
• balance - Check your current balances
• iban - View your IBAN details
• wallet - Wallet and address information

💸 Transactions:
• transfer/send - Money transfer options
• deposit - Add funds to your account
• withdraw - Remove funds to bank account

📊 Additional Features:
• Transaction history and statements
• Multi-currency support (GBP, EUR, USD)
• Real-time blockchain integration
• Regulatory compliance (EU EMI license)

🆘 Support:
• Email: support@monerium.com
• Hours: 9 AM - 6 PM CET (Mon-Fri)
• Emergency: Available 24/7

💡 Example commands:
• "What's my balance?"
• "How do I send money?"
• "Show me my IBAN"
• "How to deposit funds?"

🔐 Security Notice:
Never share your private keys or passwords.
Monerium will never ask for sensitive information via email."""
    
    def process_request(self, request_data: Dict) -> Dict:
        """Process a single request and generate response."""
        message = request_data.get('message', '')
        request_id = request_data.get('id', 'unknown')
        
        print(f"📝 Processing request: {request_id}")
        print(f"💬 Message: {message}")
        
        # Determine intent
        intent = self.parse_intent(message)
        print(f"🎯 Intent: {intent}")
        
        # Generate response based on intent
        if intent == "monerium":
            response_text = self.call_monerium_api(message)
            response_type = "monerium"
        else:
            response_text = self.call_openai(message)
            response_type = "llm"
        
        # Create response data
        response_data = {
            "request_id": request_id,
            "original_message": message,
            "intent": intent,
            "response_type": response_type,
            "response": response_text,
            "timestamp": datetime.now().isoformat(),
            "processed_by": "monerium_processor_no_localhost",
            "status": "completed"
        }
        
        return response_data
    
    def process_file(self, file_path: Path) -> bool:
        """Process a single request file."""
        try:
            print(f"\n📄 Processing file: {file_path.name}")
            
            # Read request file
            with open(file_path, 'r', encoding='utf-8') as f:
                request_data = json.load(f)
            
            # Process request
            response_data = self.process_request(request_data)
            
            # Create response file
            response_filename = f"response_{request_data.get('id', 'unknown')}.json"
            response_path = self.response_dir / response_filename
            
            with open(response_path, 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Response saved: {response_path.name}")
            
            # Optionally delete the request file after processing
            # file_path.unlink()  # Uncomment to auto-delete processed files
            
            return True
            
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            return False
    
    def watch_for_files(self, interval: int = 2):
        """Watch for new request files and process them automatically."""
        print(f"\n👀 Watching for request files (checking every {interval}s)")
        print("Press Ctrl+C to stop")
        
        processed_files = set()
        
        try:
            while True:
                # Find request files
                request_files = list(self.base_path.glob(self.request_pattern))
                
                # Process new files
                for file_path in request_files:
                    if file_path not in processed_files:
                        if self.process_file(file_path):
                            processed_files.add(file_path)
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Stopped watching for files")
    
    def process_batch(self, pattern: str):
        """Process multiple files matching a pattern."""
        files = list(self.base_path.glob(pattern))
        
        if not files:
            print(f"❌ No files found matching pattern: {pattern}")
            return
        
        print(f"📁 Found {len(files)} files to process")
        
        success_count = 0
        for file_path in files:
            if self.process_file(file_path):
                success_count += 1
        
        print(f"\n✅ Successfully processed {success_count}/{len(files)} files")

def main():
    parser = argparse.ArgumentParser(description='Monerium Processor - No Localhost Version')
    parser.add_argument('file', nargs='?', help='Request file to process')
    parser.add_argument('--watch', action='store_true', help='Watch for new files continuously')
    parser.add_argument('--batch', help='Process multiple files matching pattern')
    parser.add_argument('--interval', type=int, default=2, help='Watch interval in seconds')
    
    args = parser.parse_args()
    
    processor = MoneriumProcessor()
    
    if args.watch:
        processor.watch_for_files(args.interval)
    elif args.batch:
        processor.process_batch(args.batch)
    elif args.file:
        file_path = Path(args.file)
        if file_path.exists():
            processor.process_file(file_path)
        else:
            print(f"❌ File not found: {args.file}")
            sys.exit(1)
    else:
        # Default: watch for files
        print("🔄 No specific action specified. Starting watch mode...")
        processor.watch_for_files()

if __name__ == "__main__":
    main() 
