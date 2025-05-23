# Apollo API Key Setup Guide

## Current Issue
Your Apollo API key is still returning 403 Forbidden errors for the People Search endpoint, even after upgrading to an enhanced plan.

## Step-by-Step Solution

### 1. Create a New API Key in Apollo

1. **Log into Apollo** and go to **Settings** → **Integrations**
2. Find the **API** section and click **Connect**
3. Click **API keys** → **Create new key**

### 2. Configure the API Key Properly

When creating the key, you MUST:

#### ✅ Name and Description
- **Name**: `Lead Generation API` (or similar)
- **Description**: `API key for people search and lead generation`

#### ✅ Critical: Enable Required Scopes
Make sure to check these boxes:
- ☑️ **People Search** (`mixed_people/search`)
- ☑️ **People Enrichment** (`people/match`)
- ☑️ **Organization Search** (if needed)
- ☑️ **Contacts Search** (if needed)

#### ✅ Master Key (Recommended)
- **Toggle ON** the "Set as master key" slider
- This gives access to all endpoints available with your plan

### 3. Copy the New API Key

1. After creating the key, **copy it immediately**
2. Update your `.env` file:
   ```
   APOLLO_API_KEY=your_new_key_here
   ```

### 4. Verify Your Plan

Double-check that your Apollo plan upgrade is active:
1. Go to **Settings** → **Billing** or **Subscription**
2. Confirm you're on an enhanced/paid plan
3. Check that "API Access" is included in your plan features

### 5. Test the New Key

Run this command to test:
```bash
python experiments/test_new_apollo_key.py
```

## Common Issues and Solutions

### Issue: Still getting 403 errors
**Solutions:**
1. **Wait 5-10 minutes** after creating the key (activation delay)
2. **Regenerate the key** if it's still not working
3. **Contact Apollo support** if the plan upgrade isn't reflected

### Issue: "Endpoint not accessible with this api_key"
**Solutions:**
1. **Recreate the key** and ensure you check the "People Search" scope
2. **Enable master key** option
3. **Verify your plan** includes API access

### Issue: Key works but limited results
**Solutions:**
1. This is normal - enhanced plans have credit limits
2. Monitor usage in **Settings** → **API** → **Usage**
3. Use small `per_page` values (10-25) for testing

## What to Expect When Working

When the API key is working correctly, you should see:
```
✅ People Search works!
   Found 1 result(s)
   Total available: 50000+
   Sample: John Doe - CEO
```

## Next Steps After Success

1. **Run the full notebook**: `experiments/apollo_api_testing.ipynb`
2. **Test find_leads integration**
3. **Monitor credit usage** regularly
4. **Use moderate request volumes** to conserve credits

## Need Help?

If you're still having issues after following this guide:
1. Check Apollo's status page for API issues
2. Contact Apollo support with your API key details
3. Verify your billing/plan status in Apollo dashboard 