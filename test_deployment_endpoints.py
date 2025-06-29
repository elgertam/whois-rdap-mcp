#!/usr/bin/env python3
"""
Test script to verify deployment endpoints are working correctly.
"""

import asyncio
import httpx
import json
import sys

async def test_deployment_endpoints():
    """Test all endpoints required for successful deployment."""
    base_url = "http://localhost:5000"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("Testing deployment endpoints...")
        
        # Test root endpoint
        try:
            response = await client.get(f"{base_url}/")
            print(f"✓ Root endpoint (/): {response.status_code}")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        except Exception as e:
            print(f"✗ Root endpoint (/): Failed - {e}")
            return False
        
        # Test health check endpoint
        try:
            response = await client.get(f"{base_url}/health")
            print(f"✓ Health endpoint (/health): {response.status_code}")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
            
            # Verify health check response format
            health_data = response.json()
            assert health_data["status"] == "healthy", "Health status should be 'healthy'"
            assert "service" in health_data, "Health response should include service name"
            assert "version" in health_data, "Health response should include version"
            assert "timestamp" in health_data, "Health response should include timestamp"
            
            print(f"  Health data: {json.dumps(health_data, indent=2)}")
            
        except Exception as e:
            print(f"✗ Health endpoint (/health): Failed - {e}")
            return False
        
        # Test HEAD requests (deployment systems often use these)
        try:
            response = await client.head(f"{base_url}/")
            print(f"✓ Root HEAD request: {response.status_code}")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        except Exception as e:
            print(f"✗ Root HEAD request: Failed - {e}")
            return False
        
        try:
            response = await client.head(f"{base_url}/health")
            print(f"✓ Health HEAD request: {response.status_code}")
            assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        except Exception as e:
            print(f"✗ Health HEAD request: Failed - {e}")
            return False
    
    print("\n✓ All deployment endpoints are working correctly!")
    print("The application is ready for deployment.")
    return True

if __name__ == '__main__':
    try:
        result = asyncio.run(test_deployment_endpoints())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Test failed with error: {e}")
        sys.exit(1)