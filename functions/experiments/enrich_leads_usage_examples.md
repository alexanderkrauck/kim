# Enrich Leads Function - Usage Examples

The `enrich_leads` function provides flexible lead enrichment capabilities, allowing you to enhance existing leads with Perplexity research data. This function is separate from lead discovery, providing better modularity and control.

## 🎯 Use Cases

### 1. **Automatic Enrichment** (Default Workflow)
When using `find_leads` with `auto_enrich: true`, enrichment happens automatically:

```javascript
// Find leads and automatically enrich them
const result = await findLeads({
  project_id: 'project_123',
  num_leads: 25,
  auto_enrich: true  // Default: true
});

// Result includes enrichment status
console.log(result.enrichment_triggered); // true
```

### 2. **Manual Enrichment** (Selective Control)
Enrich specific leads or all unenriched leads manually:

```javascript
// Enrich all unenriched leads in a project
const enrichResult = await enrichLeads({
  project_id: 'project_123',
  enrichment_type: 'both'  // company + person research
});

// Enrich specific leads only
const specificEnrichment = await enrichLeads({
  project_id: 'project_123',
  lead_ids: ['lead_001', 'lead_002', 'lead_003'],
  enrichment_type: 'company'  // company research only
});
```

### 3. **Re-enrichment** (Update Existing Data)
Re-enrich leads that already have enrichment data:

```javascript
// Re-enrich all leads (useful for updating old data)
const reEnrichResult = await enrichLeads({
  project_id: 'project_123',
  force_re_enrich: true,
  enrichment_type: 'both'
});
```

### 4. **Enrichment Status Monitoring**
Check enrichment progress and status:

```javascript
// Get overall project enrichment status
const status = await getEnrichmentStatus({
  project_id: 'project_123'
});

console.log(`${status.enriched_leads}/${status.total_leads} leads enriched`);
console.log(`${status.enrichment_percentage}% complete`);

// Check specific leads
const leadStatus = await getEnrichmentStatus({
  project_id: 'project_123',
  lead_ids: ['lead_001', 'lead_002']
});
```

## 📊 Enrichment Types

### Company Research (`enrichment_type: 'company'`)
- Company overview and background
- Recent news and developments
- Industry position and competitors
- Financial information (if public)
- Technology stack and services

### Person Research (`enrichment_type: 'person'`)
- Professional background and experience
- Current role and responsibilities
- Recent activities and achievements
- Social media presence
- Contact preferences

### Both (`enrichment_type: 'both'`) - Default
- Combines company and person research
- Provides comprehensive context for outreach
- Best for personalized email generation

## 🔄 Workflow Examples

### Scenario 1: Batch Lead Processing
```javascript
// 1. Find leads without automatic enrichment
const findResult = await findLeads({
  project_id: 'project_123',
  num_leads: 50,
  auto_enrich: false  // Don't enrich automatically
});

// 2. Review and filter leads if needed
const leadIds = findResult.saved_lead_ids;
const priorityLeads = leadIds.slice(0, 20); // Top 20 leads

// 3. Enrich priority leads first
const enrichResult = await enrichLeads({
  project_id: 'project_123',
  lead_ids: priorityLeads,
  enrichment_type: 'both'
});

// 4. Check status
const status = await getEnrichmentStatus({
  project_id: 'project_123'
});
```

### Scenario 2: Incremental Enrichment
```javascript
// 1. Start with company research only (faster/cheaper)
await enrichLeads({
  project_id: 'project_123',
  enrichment_type: 'company'
});

// 2. Later, add person research for high-priority leads
const highPriorityLeads = ['lead_001', 'lead_005', 'lead_012'];
await enrichLeads({
  project_id: 'project_123',
  lead_ids: highPriorityLeads,
  enrichment_type: 'person',
  force_re_enrich: true  // Add person data to existing company data
});
```

### Scenario 3: Quality Control Workflow
```javascript
// 1. Enrich leads
const enrichResult = await enrichLeads({
  project_id: 'project_123',
  enrichment_type: 'both'
});

// 2. Check for failed enrichments
const status = await getEnrichmentStatus({
  project_id: 'project_123'
});

if (status.failed_leads > 0) {
  console.log(`${status.failed_leads} leads failed enrichment`);
  
  // 3. Retry failed enrichments
  await enrichLeads({
    project_id: 'project_123',
    force_re_enrich: true  // This will retry failed leads
  });
}
```

## 📈 Performance Optimization

### Credit Management
```javascript
// For large projects, enrich in batches to manage API costs
const batchSize = 10;
const allLeads = await getProjectLeads('project_123');

for (let i = 0; i < allLeads.length; i += batchSize) {
  const batch = allLeads.slice(i, i + batchSize);
  
  await enrichLeads({
    project_id: 'project_123',
    lead_ids: batch.map(lead => lead.id),
    enrichment_type: 'company'  // Start with company only
  });
  
  // Add delay between batches to respect rate limits
  await new Promise(resolve => setTimeout(resolve, 2000));
}
```

### Priority-Based Enrichment
```javascript
// Enrich high-value leads first
const priorityTitles = ['CEO', 'CTO', 'Founder', 'VP'];

// Get leads sorted by priority
const leads = await getProjectLeads('project_123');
const priorityLeads = leads
  .filter(lead => priorityTitles.some(title => 
    lead.title?.toLowerCase().includes(title.toLowerCase())
  ))
  .map(lead => lead.id);

// Enrich priority leads first
await enrichLeads({
  project_id: 'project_123',
  lead_ids: priorityLeads,
  enrichment_type: 'both'
});
```

## 🔍 Monitoring and Analytics

### Enrichment Metrics
```javascript
// Get comprehensive enrichment analytics
const status = await getEnrichmentStatus({
  project_id: 'project_123'
});

const metrics = {
  completion_rate: status.enrichment_percentage,
  success_rate: (status.enriched_leads / (status.enriched_leads + status.failed_leads)) * 100,
  pending_count: status.pending_leads,
  total_processed: status.enriched_leads + status.failed_leads
};

console.log('Enrichment Metrics:', metrics);
```

### Error Handling
```javascript
try {
  const result = await enrichLeads({
    project_id: 'project_123',
    enrichment_type: 'both'
  });
  
  if (result.leads_failed > 0) {
    console.warn(`${result.leads_failed} leads failed enrichment`);
    
    // Get details about failed leads
    const failedLeads = await getEnrichmentStatus({
      project_id: 'project_123',
      lead_ids: result.failed_lead_ids
    });
    
    // Log specific errors for debugging
    failedLeads.lead_statuses.forEach(lead => {
      if (lead.enrichmentError) {
        console.error(`Lead ${lead.email}: ${lead.enrichmentError}`);
      }
    });
  }
  
} catch (error) {
  console.error('Enrichment failed:', error.message);
  
  // Implement retry logic or fallback
  if (error.message.includes('API key')) {
    console.log('Check Perplexity API key configuration');
  }
}
```

## 🎯 Best Practices

### 1. **Start Small**
- Begin with a small batch to test enrichment quality
- Verify data quality before processing large volumes
- Monitor API costs and rate limits

### 2. **Use Appropriate Enrichment Types**
- Use `'company'` for broad outreach campaigns
- Use `'both'` for high-value, personalized outreach
- Use `'person'` for follow-ups or specific targeting

### 3. **Monitor Progress**
- Check enrichment status regularly
- Set up alerts for failed enrichments
- Track enrichment quality and relevance

### 4. **Optimize for Cost**
- Batch process leads to minimize API calls
- Use company-only enrichment when person data isn't needed
- Implement caching to avoid re-enriching the same companies

### 5. **Quality Control**
- Review enrichment data quality periodically
- Implement validation rules for enrichment content
- Re-enrich old data periodically to keep it current

## 🚀 Integration with Email Generation

Enriched leads work seamlessly with the `contact_leads` function:

```javascript
// 1. Find and enrich leads
await findLeads({
  project_id: 'project_123',
  num_leads: 25,
  auto_enrich: true
});

// 2. Wait for enrichment to complete
let status;
do {
  status = await getEnrichmentStatus({ project_id: 'project_123' });
  if (status.pending_leads > 0) {
    await new Promise(resolve => setTimeout(resolve, 5000)); // Wait 5 seconds
  }
} while (status.pending_leads > 0);

// 3. Generate personalized emails using enriched data
const emailResult = await contactLeads({
  project_id: 'project_123',
  email_type: 'outreach'
});
```

The enrichment data is automatically used by the email generation process to create more personalized and relevant outreach emails. 