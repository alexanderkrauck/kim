# Firebase Functions Debugging & Monitoring Guide

## Overview
This guide explains how to analyze and debug your Firebase Functions backend effectively.

## 1. Where to Find Your Logs

### Firebase Console (Recommended for Firebase Functions)
- Go to [Firebase Console](https://console.firebase.google.com/)
- Select your project
- Navigate to **Functions** → **Logs**
- This shows logs specifically for your Firebase Functions

### Google Cloud Console
- Go to [Google Cloud Console](https://console.cloud.google.com/)
- Navigate to **Logging** → **Logs Explorer**
- Filter by:
  - Resource type: `cloud_function`
  - Function name: your function names (e.g., `find_leads`)

### Firebase CLI (Local Development)
```bash
# View real-time logs
firebase functions:log

# View logs for specific function
firebase functions:log --only find_leads

# Follow logs in real-time
firebase functions:log --follow
```

## 2. Improving Your Current Logging Setup

### Enhanced Logging Configuration
Create a logging utility for better structured logging:

```python
# utils/logging_utils.py
import logging
import json
from typing import Dict, Any
from firebase_functions import logger

def setup_structured_logging():
    """Setup structured logging for better Cloud Logging integration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def log_function_start(function_name: str, params: Dict[str, Any]):
    """Log function execution start with parameters"""
    logger.info(f"🚀 {function_name} started", 
                extra={
                    "function": function_name,
                    "parameters": params,
                    "event": "function_start"
                })

def log_function_end(function_name: str, result: Dict[str, Any]):
    """Log function execution end with results"""
    logger.info(f"✅ {function_name} completed", 
                extra={
                    "function": function_name,
                    "result": result,
                    "event": "function_end"
                })

def log_error(function_name: str, error: Exception, context: Dict[str, Any] = None):
    """Log errors with context"""
    logger.error(f"❌ {function_name} failed: {str(error)}", 
                 extra={
                     "function": function_name,
                     "error": str(error),
                     "error_type": type(error).__name__,
                     "context": context or {},
                     "event": "function_error"
                 })

def log_apollo_request(search_params: Dict[str, Any]):
    """Log Apollo API requests for debugging"""
    logger.info("🔍 Apollo API request", 
                extra={
                    "event": "apollo_request",
                    "search_params": search_params
                })

def log_lead_processing_stats(stats: Dict[str, Any]):
    """Log lead processing statistics"""
    logger.info("📊 Lead processing stats", 
                extra={
                    "event": "lead_stats",
                    "stats": stats
                })
```

### Update Your find_leads.py Function
Here's how to enhance your logging:

```python
# Add these imports at the top
from utils.logging_utils import (
    log_function_start, 
    log_function_end, 
    log_error, 
    log_apollo_request,
    log_lead_processing_stats
)

# In your find_leads_logic function, add structured logging:
def find_leads_logic(request_data: Dict[str, Any], auth_uid: str = None) -> Dict[str, Any]:
    function_name = "find_leads_logic"
    
    try:
        # Log function start
        log_function_start(function_name, {
            "project_id": request_data.get('project_id'),
            "num_leads": request_data.get('num_leads', 25),
            "auto_enrich": request_data.get('auto_enrich', True),
            "auth_uid": auth_uid
        })
        
        # ... existing code ...
        
        # Log Apollo request
        log_apollo_request(apollo_search_params)
        
        # ... after processing leads ...
        
        # Log processing stats
        log_lead_processing_stats({
            "leads_found": len(processed_leads),
            "leads_filtered": len(filtered_leads),
            "leads_saved": saved_count,
            "duplicates_filtered": len(filtered_leads) - len(unique_leads)
        })
        
        # Log successful completion
        log_function_end(function_name, result)
        return result
        
    except Exception as e:
        log_error(function_name, e, {
            "request_data": request_data,
            "auth_uid": auth_uid
        })
        # ... existing error handling ...
```

## 3. Local Development & Testing

### Firebase Emulator Suite
```bash
# Start all emulators
firebase emulators:start

# Start only functions emulator
firebase emulators:start --only functions

# Start with debug mode
firebase emulators:start --inspect-functions
```

### Local Testing Script
Create a test script to debug functions locally:

```python
# functions/debug_functions.py
import os
import sys
from typing import Dict, Any

# Add the functions directory to path
sys.path.append(os.path.dirname(__file__))

from find_leads import find_leads_logic

def test_find_leads_locally():
    """Test find_leads function locally with sample data"""
    
    # Sample request data
    test_data = {
        "project_id": "your-test-project-id",
        "num_leads": 5,
        "search_params": {},
        "auto_enrich": False,
        "save_without_enrichment": True
    }
    
    print("🧪 Testing find_leads function locally...")
    print(f"Test data: {test_data}")
    
    try:
        result = find_leads_logic(test_data)
        print("✅ Function executed successfully!")
        print(f"Result: {result}")
    except Exception as e:
        print(f"❌ Function failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_find_leads_locally()
```

Run locally:
```bash
cd functions
python debug_functions.py
```

## 4. Advanced Monitoring Setup

### Cloud Monitoring Dashboard
Create a monitoring dashboard in Google Cloud Console:

1. Go to **Monitoring** → **Dashboards**
2. Create a new dashboard
3. Add charts for:
   - Function execution count
   - Function execution duration
   - Error rate
   - Memory usage

### Error Reporting
Enable Error Reporting for automatic error tracking:

```python
# Add to your functions
from google.cloud import error_reporting

error_client = error_reporting.Client()

def report_error(error: Exception, context: str):
    """Report errors to Google Cloud Error Reporting"""
    try:
        error_client.report_exception()
    except Exception:
        # Fallback to logging
        logging.error(f"Failed to report error: {error}")
```

### Alerts and Notifications
Set up alerts in Google Cloud Console:

1. Go to **Monitoring** → **Alerting**
2. Create alert policies for:
   - High error rate
   - Function timeout
   - Memory usage spikes
   - API quota exceeded

## 5. Debugging Common Issues

### Function Not Appearing in Logs
```bash
# Check deployment status
firebase functions:list

# Redeploy specific function
firebase deploy --only functions:find_leads

# Check function logs immediately after deployment
firebase functions:log --follow
```

### Memory/Timeout Issues
Add memory and timeout monitoring:

```python
import psutil
import time
from firebase_functions import options

# Configure function with more memory/timeout
@https_fn.on_call(
    region=EUROPEAN_REGION,
    memory=options.MemoryOption.MB_512,  # Increase if needed
    timeout_sec=60  # Increase if needed
)
def find_leads(req: https_fn.CallableRequest) -> Dict[str, Any]:
    start_time = time.time()
    start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    
    try:
        result = find_leads_logic(req.data, req.auth.uid if req.auth else None)
        
        # Log performance metrics
        execution_time = time.time() - start_time
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        logging.info(f"Performance metrics: {execution_time:.2f}s, {end_memory:.1f}MB peak")
        
        return result
    except Exception as e:
        # ... error handling
```

### API Rate Limiting
Add rate limiting monitoring:

```python
def log_api_usage(api_name: str, response_headers: Dict[str, str]):
    """Log API usage and rate limiting info"""
    rate_limit_info = {
        "api": api_name,
        "remaining": response_headers.get('x-rate-limit-remaining'),
        "reset": response_headers.get('x-rate-limit-reset'),
        "limit": response_headers.get('x-rate-limit-limit')
    }
    
    logging.info(f"API usage: {rate_limit_info}")
    
    # Warn if approaching rate limit
    if rate_limit_info.get('remaining'):
        remaining = int(rate_limit_info['remaining'])
        if remaining < 10:
            logging.warning(f"⚠️ API rate limit warning: {remaining} requests remaining")
```

## 6. Quick Debugging Commands

```bash
# View recent errors only
firebase functions:log --only find_leads | grep ERROR

# Monitor function in real-time
firebase functions:log --follow --only find_leads

# Check function configuration
firebase functions:config:get

# Test function locally with emulator
curl -X POST http://localhost:5001/your-project/us-central1/find_leads \
  -H "Content-Type: application/json" \
  -d '{"data": {"project_id": "test"}}'
```

## 7. Performance Monitoring

### Add Performance Tracking
```python
import time
from contextlib import contextmanager

@contextmanager
def performance_monitor(operation_name: str):
    """Context manager to monitor operation performance"""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        logging.info(f"⏱️ {operation_name} took {duration:.2f} seconds")

# Usage in your function:
with performance_monitor("Apollo API call"):
    apollo_results = apollo_client.search_people(**apollo_search_params)

with performance_monitor("Lead processing"):
    processed_leads = lead_processor.process_apollo_results(apollo_results)
```

## 8. Troubleshooting Checklist

- [ ] Function deployed successfully? (`firebase functions:list`)
- [ ] Correct region configured? (Check logs in correct region)
- [ ] API keys configured? (`firebase functions:config:get`)
- [ ] Firestore rules allow access?
- [ ] Function has sufficient memory/timeout?
- [ ] No circular imports or dependency issues?
- [ ] Environment variables set correctly?

## Next Steps

1. Implement the enhanced logging utility
2. Set up monitoring dashboard
3. Create local testing script
4. Configure error reporting
5. Set up alerts for critical issues

This should give you comprehensive visibility into your Firebase Functions! 