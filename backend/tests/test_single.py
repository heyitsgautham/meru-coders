#!/usr/bin/env python3
"""Quick test for a single test case"""
import requests
import json
import time

API_BASE = "http://localhost:5000/api/chatbot"

def test_case_41():
    """Test 41: Can you help me write a Sanskrit shloka?"""
    print("\n" + "="*80)
    print("Testing: Can you help me write a Sanskrit shloka?")
    print("="*80)
    
    payload = {
        "message": "Can you help me write a Sanskrit shloka?",
        "persona": "default"
    }
    
    try:
        response = requests.post(f"{API_BASE}/chat", json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        reply = data.get('response', '')
        print(f"\nResponse:\n{reply}\n")
        
        # Check if it accepts the request (should talk about helping with shlokas)
        accepting_keywords = ['shloka', 'help', 'meter', 'compose', 'write', 'guide', 'assist']
        rejecting_keywords = ['cannot', "can't", 'unable', 'outside my scope', 'not my expertise']
        
        has_accepting = any(kw in reply.lower() for kw in accepting_keywords)
        has_rejecting = any(kw in reply.lower() for kw in rejecting_keywords)
        
        if has_accepting and not has_rejecting:
            print("✅ PASSED - Accepts helping with Sanskrit shloka writing")
            return True
        else:
            print("❌ FAILED - Still rejecting Sanskrit shloka help")
            print(f"   Accepting keywords found: {has_accepting}")
            print(f"   Rejecting keywords found: {has_rejecting}")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Fix for Test 41...")
    print("⏳ Make sure Flask backend is running on localhost:5000")
    time.sleep(1)
    
    result = test_case_41()
    
    print("\n" + "="*80)
    if result:
        print("🎉 SUCCESS! Test 41 now passes.")
        print("The chatbot now properly accepts requests to help write Sanskrit shlokas.")
    else:
        print("❌ Test still failing. May need to restart Flask backend.")
    print("="*80)

