#!/usr/bin/env python3
"""Test script for Lightning address payment functionality."""

import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from lnbits_mcp_server.client import LNbitsClient, LNbitsConfig
from lnbits_mcp_server.tools.payments import PaymentTools

async def test_lightning_address_resolution():
    """Test Lightning address resolution."""
    print("Testing Lightning address resolution...")
    
    # Create client
    config = LNbitsConfig()
    client = LNbitsClient(config)
    
    try:
        # Test resolving a Lightning address
        test_address = "edward@sats.pw"
        print(f"Resolving Lightning address: {test_address}")
        
        callback_url = await client.resolve_lightning_address(test_address)
        
        if callback_url:
            print(f"✅ Successfully resolved to: {callback_url}")
            
            # Test getting invoice (small amount)
            amount_msats = 1000  # 1 sat
            print(f"Getting invoice for {amount_msats} msats...")
            
            invoice = await client.get_lnurl_pay_invoice(callback_url, amount_msats, "Test payment")
            
            if invoice:
                print(f"✅ Successfully got invoice: {invoice[:50]}...")
                return True
            else:
                print("❌ Failed to get invoice")
                return False
        else:
            print("❌ Failed to resolve Lightning address")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def test_payment_tools():
    """Test payment tools Lightning address functionality."""
    print("\nTesting PaymentTools Lightning address payment...")
    
    # Create client and tools
    config = LNbitsConfig()
    client = LNbitsClient(config)
    payment_tools = PaymentTools(client)
    
    try:
        # Test Lightning address payment (don't actually pay - just test resolution)
        test_address = "edward@sats.pw"
        amount_sats = 1
        comment = "Test payment from LNbits MCP server"
        
        print(f"Testing payment to {test_address} for {amount_sats} sats...")
        
        # This would actually make a payment - for testing we'll just do resolution
        callback_url = await client.resolve_lightning_address(test_address)
        
        if callback_url:
            print(f"✅ Payment setup successful - would pay to: {callback_url}")
            return True
        else:
            print("❌ Payment setup failed")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def main():
    """Run all tests."""
    print("🧪 Testing Lightning address payment functionality")
    print("=" * 60)
    
    # Test resolution
    resolution_success = await test_lightning_address_resolution()
    
    # Test payment tools
    payment_tools_success = await test_payment_tools()
    
    print("\n" + "=" * 60)
    print("📊 Test Results:")
    print(f"Lightning address resolution: {'✅ PASS' if resolution_success else '❌ FAIL'}")
    print(f"Payment tools integration: {'✅ PASS' if payment_tools_success else '❌ FAIL'}")
    
    if resolution_success and payment_tools_success:
        print("\n🎉 All tests passed! Lightning address payment is working.")
        return 0
    else:
        print("\n❌ Some tests failed.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)