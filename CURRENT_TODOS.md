# CURRENT TODOS - Functions Implementation

## 1. Python-Based Configuration Core
**Goal**: Single source of truth for all configurations (Foundation)

### 1.1 Backend Configuration Model
- Create `config_model.py` with comprehensive Python typing
- Define all configuration schemas (lead finding, email, prompts, etc.)
- Include validation rules and default values
- Document all configuration options

### 1.2 Firebase Integration
- Build utilities to sync Python config schema to Firebase
- Support both global and project-specific configurations
- Maintain existing Firebase collection structure

### 1.3 Frontend Configuration Interface
- Create expandable settings tab in frontend
- Expose full raw config editing (with breaking change warnings)
- Implement direct Firebase read/write (bypass Python for frontend)
- Add validation and error handling for config changes
- Use Python backend as source of truth for business logic

## 2. Lead Finding Implementation
**Goal**: Identify leads based on user input to projects using Apollo API

### 2.1 Location Processing
- **2.1a**: Parse typed location using LLMs to Apollo format
- **2.1b**: Add location config option when creating projects
- **Decision needed**: Choose between LLM parsing vs user config approach

### 2.2 Job Role Configuration  
- Set reasonable target positions (CEO, CTO, Founder, etc.)
- Make job roles configurable at project and global level
- Default to hardcoded list initially, expose to user later

### 2.3 Lead Filtering Logic
- Filter to one person per company (configurable)
- Remove leads without email addresses
- Implement duplicate detection and removal

## 3. Lead Enrichment (Perplexity Integration)
**Goal**: Enhance leads with additional research data

- Add enrichment prompt configuration (hardcode initially)
- Implement Perplexity API calls for company/person research
- Attach enrichment results as string to lead records
- Handle enrichment errors gracefully

## 4. Email Generation (OpenAI Integration)
**Goal**: Generate personalized outreach emails

- Add email generation prompts (outreach + followup)
- Implement OpenAI API calls for personalized emails
- Support different email types (initial outreach, followups)
- Generate subject lines and email content

## 5. Email Sending & Scheduling
**Goal**: Deliver emails and manage follow-up sequences

- Integrate SMTP server configuration and sending
- Implement email scheduling system
- Add followup email automation with delays
- Respect daily email limits and rate limiting

---

**Note**: Configuration should be defined once in Python but accessible directly from frontend to Firebase for immediate updates.