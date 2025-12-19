# LMOTPO Sales Pipeline Mapping Documentation

## Overview
This document describes the LMOTPO (Lead-Meetings-Opportunities-Trial-Price Discussion-Order) sales pipeline configuration that replaced the previous SPANCO methodology.

**Implementation Date:** December 2025
**Based On:** CRM_Non_Blocking_Tasks - Section 2: SPANCO to LMOTPO Sales Pipeline Stages

---

## Pipeline Stages Mapping

### Stage 1: L - Lead
**Full Name:** Lead
**Description:** Initial prospect identification and qualification workflow
**CRM Lead Status:** `New`
**CRM Deal Status:** N/A
**Color:** Blue (`bg-gradient-to-br from-blue-600 to-blue-700`)

**Characteristics:**
- Entry point for all new prospects
- Initial contact information captured
- Basic qualification criteria applied
- Always represents 100% of the pipeline base

---

### Stage 2: M - Meetings
**Full Name:** Meetings
**Description:** Telephone and field meetings tracking for understanding customer needs
**CRM Lead Status:** `Contacted`, `Nurture`
**CRM Deal Status:** N/A
**Color:** Indigo (`bg-gradient-to-br from-indigo-600 to-indigo-700`)

**Characteristics:**
- Active engagement with prospects
- Discovery calls and initial meetings
- Understanding customer requirements
- Building relationship and trust
- Leads that have not been converted to deals

---

### Stage 3: O - Opportunities
**Full Name:** Opportunities
**Description:** Converted leads with deep-dive discovery and technical analysis tracking
**CRM Lead Status:** `Qualified` (unconverted)
**CRM Deal Status:** `Qualification`, `Demo/Making`
**Color:** Violet (`bg-gradient-to-br from-violet-600 to-violet-700`)

**Characteristics:**
- Qualified leads ready for conversion
- Technical discovery and analysis
- Product demonstrations
- Solution fit assessment
- Combines both qualified leads and early-stage deals

---

### Stage 4: T - Trial
**Full Name:** Trial
**Description:** Paid and unpaid trial provisioning and evaluation workflow
**CRM Lead Status:** N/A
**CRM Deal Status:** `Proposal/Quotation`
**Color:** Amber (`bg-gradient-to-br from-amber-600 to-amber-700`)

**Characteristics:**
- Trial period management
- Proof of concept delivery
- Value demonstration
- Usage monitoring and support
- Initial proposal/quotation provided

---

### Stage 5: P - Price Discussion
**Full Name:** Price Discussion
**Description:** Proposal, quotation, and negotiation tracking
**CRM Lead Status:** N/A
**CRM Deal Status:** `Negotiation`
**Color:** Emerald (`bg-gradient-to-br from-emerald-600 to-emerald-700`)

**Characteristics:**
- Commercial discussions
- Pricing negotiation
- Terms and conditions finalization
- Contract review
- Final proposal refinement

---

### Stage 6: O - Order
**Full Name:** Order
**Description:** Final closure workflow (Won or Lost)
**CRM Lead Status:** N/A
**CRM Deal Status:** `Ready to Close`, `Won`
**Color:** Teal (`bg-gradient-to-br from-teal-600 to-teal-700`)

**Characteristics:**
- Final decision stage
- Order booking
- Contract signing
- Customer onboarding preparation
- Won deals tracking

---

## Technical Implementation

### Frontend Component
**File:** `apps/crm/frontend/src/components/Dashboard Elements/SpancoWidget.vue`

**Key Changes:**
- Component renamed from SPANCO to LMOTPO
- Data computed property: `spancoData` → `lmotpoData`
- CSS transitions: `spanco-stage` → `lmotpo-stage`

### Backend Configuration
**File:** `apps/crm/crm/fcrm/doctype/fcrm_settings/fcrm_settings.json`

**FCRM Settings Field Mapping:**
```json
{
  "suspects": "Lead",           // L - Lead
  "prospects": "Meetings",       // M - Meetings
  "analysis": "Opportunities",   // O - Opportunities
  "negotiation": "Trial",        // T - Trial
  "closed": "Price Discussion",  // P - Price Discussion
  "order": "Order"              // O - Order
}
```

### View Filters Configuration
**File:** `apps/crm/crm/install.py` - Function: `add_default_spanco_views()`

```python
lmotpo_views = {
    "Lead": {
        "filters": '{"status": "New"}',
        "dt": "CRM Lead"
    },
    "Meetings": {
        "filters": '{"status": ["in", ["Contacted", "Nurture"]]}',
        "dt": "CRM Lead"
    },
    "Opportunities": {
        "filters": '{"status": ["in", ["Qualification", "Demo/Making"]]}',
        "dt": "CRM Deal"
    },
    "Trial": {
        "filters": '{"status": "Proposal/Quotation"}',
        "dt": "CRM Deal"
    },
    "Price Discussion": {
        "filters": '{"status": "Negotiation"}',
        "dt": "CRM Deal"
    },
    "Order": {
        "filters": '{"status": ["in", ["Ready to Close", "Won"]]}',
        "dt": "CRM Deal"
    }
}
```

---

## Data Calculation Logic

### Percentage Calculation
All stage percentages are calculated relative to the total number of leads in the **Lead** stage:

```javascript
percent = Math.round((stageCount / totalLeads) * 100)
```

### Valuation Calculation
Each stage's valuation is the sum of `annual_revenue` field from all records in that stage:

```javascript
valuation = records.reduce((sum, item) => sum + (Number(item.annual_revenue) || 0), 0)
```

### Opportunities Stage Special Handling
The Opportunities stage combines two data sources:
1. Qualified leads that haven't been converted to deals
2. Deals in Qualification or Demo/Making status

```javascript
const qualifiedLeads = leads.filter((l) => l.status === 'Qualified' && !l.converted)
const opportunityDeals = deals.filter((d) =>
    ['Qualification', 'Demo/Making'].includes(d.status)
)
// Combined for display
number: qualifiedLeads.length + opportunityDeals.length
```

---

## Migration Notes

### From SPANCO to LMOTPO

| Old SPANCO Stage | New LMOTPO Stage | Changes |
|------------------|------------------|---------|
| S - Suspects | L - Lead | Direct mapping, same status (New) |
| P - Prospects | M - Meetings | Narrowed to Contacted & Nurture only |
| A - Analysis | O - Opportunities | Now includes Qualified leads + early deals |
| N - Negotiations | T - Trial | Mapped to Proposal/Quotation status |
| C - Closure | P - Price Discussion | Mapped to Negotiation status only |
| O - Order | O - Order | Expanded to include Ready to Close + Won |

### Key Differences
1. **Qualified Status Split:** Previously part of Prospects, now in Opportunities
2. **Order Stage Expansion:** Now includes "Ready to Close" deals
3. **Opportunities Combination:** Merges qualified leads with early-stage deals
4. **Trial Stage Addition:** New explicit stage for trial/POC phase

### Migration Patch
A migration patch has been created at `apps/crm/crm/patches/v1_0/migrate_spanco_to_lmotpo_views.py` that will:

1. **Update Existing Views**: Automatically rename old SPANCO view labels to LMOTPO labels
   - Suspects → Lead
   - Prospects → Meetings
   - Analysis → Opportunities
   - Negotiations → Trial
   - Commitment → Price Discussion

2. **Update Filters**: Ensure all views have the correct status filters as defined in Section 2

3. **Update FCRM Settings**: Map the renamed views to the correct FCRM Settings fields

4. **Set Public Flag**: Ensure all LMOTPO views are marked as public and standard

The patch will run automatically on the next `bench migrate` command.

---

## API Endpoints

### Get Leads Data
**Function:** `get_leads_data()`
**File:** `apps/crm/crm/fcrm/doctype/crm_lead/crm_lead.py`
**Returns:** All CRM Leads with status and annual_revenue fields

### Get Deals Data
**Function:** `get_deals_data()`
**File:** `apps/crm/crm/fcrm/doctype/crm_deal/crm_deal.py`
**Returns:** All CRM Deals with status and annual_revenue fields

---

## Dashboard Metrics

### Total Pipeline Value
Sum of valuations across all stages

### Overall Conversion Rate
```
Conversion Rate = (Orders / Total Leads) × 100
```

### Stage Metrics Displayed
For each stage:
- **Number:** Count of records in the stage
- **Percent:** Percentage relative to total leads
- **Valuation:** Sum of annual revenue for records in the stage

---

## User Interface

### Desktop View
- Horizontal bar visualization
- Full stage names displayed
- Metrics: count, percentage, and valuation
- Click-through to filtered views

### Mobile View
- Single horizontal line with stage letters
- Compact header with total value and conversion rate
- Stage details grid below the bar
- Touch-enabled navigation

---

## Related Files Modified

1. **Frontend:**
   - `apps/crm/frontend/src/components/Dashboard Elements/SpancoWidget.vue`

2. **Backend Configuration:**
   - `apps/crm/crm/fcrm/doctype/fcrm_settings/fcrm_settings.json`
   - `apps/crm/crm/install.py`

3. **Migration Patch:**
   - `apps/crm/crm/patches/v1_0/migrate_spanco_to_lmotpo_views.py`

4. **Documentation:**
   - `apps/crm/crm/docs/LMOTPO_Pipeline_Mapping.md` (this file)

---

## Future Considerations

### Potential Enhancements
1. Add "Lost" deals tracking in a separate view
2. Implement stage duration metrics
3. Add conversion rate between consecutive stages
4. Create automated stage progression rules
5. Implement SLA tracking per stage

### Maintenance Notes
- When adding new Lead/Deal statuses, update the stage filters in `install.py`
- Keep FCRM Settings field labels synchronized with UI
- Update this documentation when modifying stage logic

---

## Support & References

**Primary Documentation:** CRM_Non_Blocking_Tasks - Non-Blocking Tasks.pdf (Section 2)
**Implementation Tasks:** Section 2.1 through 2.6 in requirements document

For questions or modifications to this pipeline, refer to the requirements document and ensure all changes maintain alignment with the LMOTPO methodology.
