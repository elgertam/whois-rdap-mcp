#!/usr/bin/env python3
"""
Comprehensive deployment verification script.
Tests all endpoints and configurations required for successful deployment.
"""

import asyncio
import httpx
import json
import sys
from datetime import datetime

async def verify_deployment():
    """Verify all deployment requirements are met."""
    print("=== MCP Whois/RDAP Server Deployment Verification ===")
    print(f"Verification started at: {datetime.now().isoformat()}")
    print()
    
    base_url = "http://localhost:5000"
    all_tests_passed = True
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Test 1: Root endpoint
        print("1. Testing root endpoint (/)...")
        try:
            response = await client.get(f"{base_url}/")
            if response.status_code == 200:
                print("   ✓ Root endpoint returns 200 OK")
                print(f"   ✓ Content-Type: {response.headers.get('content-type', 'N/A')}")
            else:
                print(f"   ✗ Root endpoint returned {response.status_code}")
                all_tests_passed = False
        except Exception as e:
            print(f"   ✗ Root endpoint test failed: {e}")
            all_tests_passed = False
        
        # Test 2: Health endpoint
        print("\n2. Testing health endpoint (/health)...")
        try:
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                print("   ✓ Health endpoint returns 200 OK")
                health_data = response.json()
                print(f"   ✓ Service: {health_data.get('service', 'N/A')}")
                print(f"   ✓ Status: {health_data.get('status', 'N/A')}")
                print(f"   ✓ Version: {health_data.get('version', 'N/A')}")
                print(f"   ✓ Uptime: {health_data.get('uptime', 'N/A')} seconds")
            else:
                print(f"   ✗ Health endpoint returned {response.status_code}")
                all_tests_passed = False
        except Exception as e:
            print(f"   ✗ Health endpoint test failed: {e}")
            all_tests_passed = False
        
        # Test 3: Status endpoint
        print("\n3. Testing status endpoint (/status)...")
        try:
            response = await client.get(f"{base_url}/status")
            if response.status_code == 200:
                print("   ✓ Status endpoint returns 200 OK")
                status_data = response.json()
                print(f"   ✓ Application: {status_data.get('application', 'N/A')}")
                print(f"   ✓ Deployment ready: {status_data.get('deployment', {}).get('ready', False)}")
                services = status_data.get('services', {})
                for service, info in services.items():
                    print(f"   ✓ {service}: {info.get('status', 'N/A')} on port {info.get('port', 'N/A')}")
            else:
                print(f"   ✗ Status endpoint returned {response.status_code}")
                all_tests_passed = False
        except Exception as e:
            print(f"   ✗ Status endpoint test failed: {e}")
            all_tests_passed = False
        
        # Test 4: HEAD requests
        print("\n4. Testing HEAD requests...")
        for endpoint in ['/', '/health', '/status']:
            try:
                response = await client.head(f"{base_url}{endpoint}")
                if response.status_code == 200:
                    print(f"   ✓ HEAD {endpoint} returns 200 OK")
                else:
                    print(f"   ✗ HEAD {endpoint} returned {response.status_code}")
                    all_tests_passed = False
            except Exception as e:
                print(f"   ✗ HEAD {endpoint} test failed: {e}")
                all_tests_passed = False
        
        # Test 5: MCP Server connectivity
        print("\n5. Testing MCP server connectivity...")
        try:
            # Try to connect to MCP server port
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', 5001))
            sock.close()
            
            if result == 0:
                print("   ✓ MCP server is accepting connections on port 5001")
            else:
                print("   ✗ MCP server is not accepting connections on port 5001")
                all_tests_passed = False
        except Exception as e:
            print(f"   ✗ MCP connectivity test failed: {e}")
            all_tests_passed = False
        
        # Test 6: Response time check
        print("\n6. Testing response times...")
        try:
            import time
            start_time = time.time()
            response = await client.get(f"{base_url}/health")
            response_time = (time.time() - start_time) * 1000
            
            if response_time < 1000:  # Less than 1 second
                print(f"   ✓ Health endpoint response time: {response_time:.2f}ms")
            else:
                print(f"   ⚠ Health endpoint response time is high: {response_time:.2f}ms")
        except Exception as e:
            print(f"   ✗ Response time test failed: {e}")
    
    print("\n=== Deployment Configuration Summary ===")
    print("Port Configuration:")
    print("  - Web Interface: 5000 (external port 80)")
    print("  - MCP Server: 5001 (internal)")
    print("\nHealth Check Endpoints:")
    print("  - GET /       - Main application page")
    print("  - GET /health - Health status (JSON)")
    print("  - GET /status - Detailed status (JSON)")
    print("  - HEAD support for all endpoints")
    print("\nDeployment Script:")
    print("  - Command: python replit_deploy.py")
    print("  - Binding: 0.0.0.0:5000")
    print("  - Graceful shutdown: Enabled")
    
    print(f"\n=== Final Result ===")
    if all_tests_passed:
        print("✅ ALL TESTS PASSED - Application is ready for deployment!")
        print("\nDeployment instructions:")
        print("1. Use 'python replit_deploy.py' as the run command")
        print("2. Ensure port 5000 is mapped to external port 80")
        print("3. Health checks will pass at / and /health endpoints")
        return True
    else:
        print("❌ SOME TESTS FAILED - Please fix issues before deployment")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(verify_deployment())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nVerification interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\nVerification failed with error: {e}")
        sys.exit(1)