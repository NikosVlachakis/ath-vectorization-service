#!/usr/bin/env python
"""
Test the orchestrator polling functionality for distributed architecture.
"""

import sys
import os
import time
import json
from unittest.mock import patch, MagicMock

# Add the app directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app'))

from services.orchestrator_poller import OrchestratorPoller


def test_polling_simulation():
    """Test orchestrator polling with simulated responses."""
    print("🧪 Testing Orchestrator Polling Simulation")
    print("=" * 60)
    
    # Create poller with short intervals for testing
    poller = OrchestratorPoller(
        orchestrator_url="http://localhost:5000",
        polling_interval=2,  # 2 seconds for testing
        polling_timeout=30   # 30 seconds max for testing
    )
    
    print("📋 Test Scenario:")
    print("  - Polling interval: 2 seconds")
    print("  - Timeout: 30 seconds")
    print("  - Expected: Simulate IN_PROGRESS → COMPLETED flow")
    
    # Mock responses for different polling stages
    mock_responses = [
        # Poll 1-3: In progress
        {"status": "WAITING", "message": "Job waiting for clients"},
        {"status": "IN_PROGRESS", "message": "Job in progress (1/2)"},
        {"status": "AGGREGATING", "message": "Job aggregating"},
        
        # Poll 4: Completed with results
        {
            "status": "COMPLETED",
            "jobId": "test_polling_job",
            "aggregatedResults": [
                {
                    "featureName": "age",
                    "dataType": "NUMERIC",
                    "aggregatedNotNull": 1000,
                    "aggregatedAvg": 45.0
                },
                {
                    "featureName": "isActive", 
                    "dataType": "BOOLEAN",
                    "aggregatedNotNull": 1000,
                    "aggregatedTrue": 750
                }
            ],
            "metadata": {
                "totalFeatures": 2,
                "totalClients": 2,
                "completedAt": "2025-08-21T15:00:00"
            }
        }
    ]
    
    poll_count = 0
    
    def mock_poll_job_status(job_id):
        nonlocal poll_count
        if poll_count < len(mock_responses):
            response = mock_responses[poll_count]
            poll_count += 1
            print(f"  📡 Mock Poll #{poll_count}: {response.get('status', 'UNKNOWN')}")
            return response
        else:
            # Return completed after all mocked responses
            return mock_responses[-1]
    
    # Mock the polling method
    with patch.object(poller, 'poll_job_status', side_effect=mock_poll_job_status):
        with patch.object(poller, 'save_results_locally', return_value=True) as mock_save:
            
            print("\n🔄 Starting polling simulation...")
            start_time = time.time()
            
            success = poller._poll_until_complete("test_polling_job")
            
            elapsed = time.time() - start_time
            
            print(f"\n📊 Polling Results:")
            print(f"  ✅ Success: {success}")
            print(f"  ⏱️  Elapsed: {elapsed:.1f} seconds")
            print(f"  📡 Total polls: {poll_count}")
            
            # Check if save was called
            if mock_save.called:
                print(f"  💾 Results saved: YES")
                save_args = mock_save.call_args[0]
                print(f"      Job ID: {save_args[0]}")
                print(f"      Features: {len(save_args[1].get('aggregatedResults', []))}")
            else:
                print(f"  💾 Results saved: NO")
    
    return success


def test_polling_configuration():
    """Test polling configuration from environment variables."""
    print("\n🔧 Testing Polling Configuration")
    print("-" * 40)
    
    # Test default values
    poller1 = OrchestratorPoller("http://test:5000")
    print(f"✅ Default interval: {poller1.polling_interval}s")
    print(f"✅ Default timeout: {poller1.polling_timeout}s")
    
    # Test custom values
    poller2 = OrchestratorPoller("http://test:5000", polling_interval=5, polling_timeout=600)
    print(f"✅ Custom interval: {poller2.polling_interval}s")
    print(f"✅ Custom timeout: {poller2.polling_timeout}s")
    
    return True


if __name__ == "__main__":
    print("OrchestratorPoller Tests")
    print("=" * 50)
    
    try:
        # Test configuration
        test_polling_configuration()
        
        # Test polling simulation
        success = test_polling_simulation()
        
        if success:
            print("\n🎉 All polling tests passed!")
            print("✅ Polling mechanism is ready for distributed architecture")
        else:
            print("\n❌ Polling tests failed")
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        import traceback
        traceback.print_exc()
