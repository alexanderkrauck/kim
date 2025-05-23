# Experiments Folder

This folder contains interactive development notebooks and scripts for testing API integrations and developing new features.

## Setup

1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Copy environment variables:
   ```bash
   cp env.example .env
   # Edit .env with your actual API keys
   ```

3. Start Jupyter Lab:
   ```bash
   jupyter lab
   ```

## Files

- `api_testing.ipynb` - Interactive testing of Apollo, Perplexity, and OpenAI APIs
- `lead_processing.ipynb` - Development and testing of lead processing workflows
- `email_testing.ipynb` - SMTP email testing and template development
- `data_analysis.ipynb` - Analysis of lead data and campaign performance

## Environment Variables

The experiments use environment variables from `.env` file for API keys and configuration. This allows you to:

- Test APIs without affecting production Firebase settings
- Develop and iterate quickly with real API responses
- Debug API integrations before deploying to Firebase Functions

## Best Practices

1. Never commit `.env` files or API keys to version control
2. Use the same API key variable names as in `env.example`
3. Test all API integrations here before implementing in main functions
4. Document your experiments with clear markdown cells
5. Clean up temporary data and test outputs regularly 