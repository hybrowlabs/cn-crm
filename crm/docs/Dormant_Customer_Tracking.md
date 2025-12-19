# Dormant Customer Tracking

## Overview

The Dormant Customer Tracking feature automatically identifies customers who have become inactive based on their ERPNext transaction history. This helps sales teams proactively re-engage with customers who haven't placed orders recently.

## How It Works

### Flow

1. **Lead Creation** → CRM Lead is created in Frappe CRM
2. **Lead Conversion** → Creates CRM Organization and CRM Deal
3. **Deal Won** → Creates Customer in ERPNext with `crm_deal` field linking back
4. **Dormancy Detection** → System checks Sales Orders from linked ERPNext customers

### Dormancy Criteria

A CRM Organization is marked as **dormant** when:
- All linked ERPNext customers have no **submitted Sales Orders** in the last X days
- X = `dormant_customers_timespan` configured in FCRM Settings (default: 90 days)

## Configuration

### FCRM Settings

Navigate to: **FCRM Settings → Settings Tab**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| Dormant Customers time span | Int | 90 | Number of days after which a customer is considered dormant |

## CRM Organization Fields

### New Fields Added

| Field | Type | Description |
|-------|------|-------------|
| **Is Dormant Customer** | Checkbox | Automatically calculated based on ERPNext customer activity (Read-only) |
| **Last Transaction Date** | Datetime | Last Sales Order date from linked ERPNext customers (Read-only) |

These fields are located in the **"Dormant Customer Tracking"** section at the bottom of the CRM Organization form.

## Automatic Updates

### Daily Scheduled Job

- **Frequency**: Daily (runs at configured time)
- **Function**: `update_all_organizations_dormancy_status()`
- **Process**:
  1. Iterates through all CRM Organizations
  2. Checks linked ERPNext customers
  3. Updates `is_dormant` and `last_transaction_date` fields
  4. Logs any errors for debugging

### Manual Refresh

Users can manually refresh dormancy status for a specific organization:

1. Open any CRM Organization document
2. Click **"Refresh Dormancy Status"** button
3. System will:
   - Query all linked deals
   - Find all customers created from those deals
   - Check latest Sales Orders
   - Update dormancy status immediately

## Technical Implementation

### Database Structure

```sql
-- CRM Organization fields
ALTER TABLE `tabCRM Organization`
ADD COLUMN is_dormant INT(1) DEFAULT 0,
ADD COLUMN last_transaction_date DATETIME;
```

### Logic Flow

```python
def update_dormancy_status(self):
    # 1. Get dormant timespan from settings
    dormant_days = fcrm_settings.dormant_customers_timespan or 90
    cutoff_date = now - dormant_days

    # 2. Find all deals for this organization
    deals = get_all("CRM Deal", filters={"organization": self.name})

    # 3. Find all customers from these deals
    customers = get_all("Customer", filters={"crm_deal": ["in", deals]})

    # 4. Check latest Sales Order
    latest_so_date = MAX(transaction_date) FROM `tabSales Order`
                     WHERE customer IN customers AND docstatus = 1

    # 5. Update status
    if latest_so_date < cutoff_date or no_sales_orders:
        self.is_dormant = 1
    else:
        self.is_dormant = 0

    self.last_transaction_date = latest_so_date
```

### API Endpoints

#### Manual Update for Single Organization
```python
@frappe.whitelist()
def update_dormancy_status_for_organization(organization_name):
    """Update dormancy status for a specific organization"""
```

**Usage:**
```javascript
frappe.call({
    method: 'crm.fcrm.doctype.crm_organization.crm_organization.update_dormancy_status_for_organization',
    args: {
        organization_name: 'Acme Corp'
    },
    callback: function(r) {
        console.log(r.message);
        // {success: true, is_dormant: 1, last_transaction_date: "2025-10-15", message: "..."}
    }
});
```

#### Background Job for All Organizations
```python
def update_all_organizations_dormancy_status():
    """Run daily via scheduler to update all organizations"""
```

## Integration with ERPNext

### Requirements

1. **ERPNext must be installed** in the same site or configured via ERPNext CRM Settings
2. **Customer DocType must have `crm_deal` field** (auto-created by ERPNext CRM integration)
3. **Sales Orders must be submitted** (docstatus = 1) to be counted

### Data Linking

```
CRM Lead → (convert) → CRM Organization + CRM Deal
                              ↓
CRM Deal → (win) → ERPNext Customer (crm_deal field)
                              ↓
ERPNext Customer → Sales Orders (transaction_date)
                              ↓
                    Dormancy Calculation
```

## Use Cases

### 1. Sales Team Follow-up
- Filter CRM Organizations where `is_dormant = 1`
- Assign follow-up tasks to sales reps
- Track re-engagement efforts

### 2. Customer Retention Campaigns
- Export list of dormant customers
- Launch targeted email campaigns
- Offer special promotions or check-ins

### 3. Account Health Monitoring
- Dashboard showing dormant customer percentage
- Alerts when key accounts become dormant
- Trend analysis over time

### 4. Pipeline Hygiene
- Identify organizations to remove from active pipeline
- Focus resources on active customers
- Clean up stale data

## Deployment Notes

### Patches

Two patches are included for deployment:

1. **`add_dormant_customers_timespan_field`** (pre_model_sync)
   - Adds `dormant_customers_timespan` field to FCRM Settings

2. **`add_dormant_customer_fields_to_organization`** (pre_model_sync)
   - Adds `is_dormant` and `last_transaction_date` fields to CRM Organization

### Frappe Cloud Deployment

These patches will run automatically during deployment:
- ✅ Registered in `patches.txt`
- ✅ Run in correct order (pre_model_sync)
- ✅ Idempotent (safe to run multiple times)
- ✅ Error handling and logging included

### Post-Deployment

After deployment:
1. Configure `dormant_customers_timespan` in FCRM Settings (default: 90 days)
2. Manual run: Execute `update_all_organizations_dormancy_status()` to populate initial data
3. Daily scheduler will keep data updated automatically

## Files Modified/Created

### Modified Files
1. [apps/crm/crm/fcrm/doctype/fcrm_settings/fcrm_settings.json](apps/crm/crm/fcrm/doctype/fcrm_settings/fcrm_settings.json)
   - Added `dormant_customers_timespan` field

2. [apps/crm/crm/fcrm/doctype/crm_organization/crm_organization.json](apps/crm/crm/fcrm/doctype/crm_organization/crm_organization.json)
   - Added `is_dormant` and `last_transaction_date` fields

3. [apps/crm/crm/fcrm/doctype/crm_organization/crm_organization.py](apps/crm/crm/fcrm/doctype/crm_organization/crm_organization.py)
   - Added `update_dormancy_status()` method
   - Added `update_dormancy_status_for_organization()` API method
   - Added `update_all_organizations_dormancy_status()` scheduler function

4. [apps/crm/crm/fcrm/doctype/crm_organization/crm_organization.js](apps/crm/crm/fcrm/doctype/crm_organization/crm_organization.js)
   - Added "Refresh Dormancy Status" button

5. [apps/crm/crm/hooks.py](apps/crm/crm/hooks.py)
   - Added daily scheduler event

6. [apps/crm/crm/patches.txt](apps/crm/crm/patches.txt)
   - Registered both patches

### Created Files
1. [apps/crm/crm/patches/v1_0/add_dormant_customers_timespan_field.py](apps/crm/crm/patches/v1_0/add_dormant_customers_timespan_field.py)
2. [apps/crm/crm/patches/v1_0/add_dormant_customer_fields_to_organization.py](apps/crm/crm/patches/v1_0/add_dormant_customer_fields_to_organization.py)
3. [apps/crm/crm/docs/Dormant_Customer_Tracking.md](apps/crm/crm/docs/Dormant_Customer_Tracking.md) (this file)

## Troubleshooting

### Dormancy Not Updating

**Check:**
1. ERPNext is installed: `bench --site [site] console` → `frappe.get_installed_apps()`
2. Deals exist for organization: Query `CRM Deal` with organization filter
3. Customers exist with `crm_deal` field populated
4. Sales Orders are submitted (docstatus = 1)
5. Scheduler is running: Check scheduled job logs

### Manual Fix

```python
# Run in bench console
from crm.fcrm.doctype.crm_organization.crm_organization import update_all_organizations_dormancy_status
update_all_organizations_dormancy_status()
```

### Check Specific Organization

```python
# Run in bench console
org = frappe.get_doc("CRM Organization", "Acme Corp")
org.update_dormancy_status()
org.save()
print(f"Is Dormant: {org.is_dormant}, Last Transaction: {org.last_transaction_date}")
```

## Future Enhancements

Potential improvements:
1. **Configurable Transaction Types**: Include Sales Invoices, Delivery Notes
2. **Customer Segmentation**: Different dormancy thresholds per segment
3. **Automated Workflows**: Auto-assign follow-up tasks when customer becomes dormant
4. **Dashboard Widget**: Visual representation of dormant customers
5. **Email Notifications**: Alert account managers when key customers go dormant
6. **Re-engagement Tracking**: Track when dormant customers become active again

---

**Last Updated**: December 18, 2025
**Version**: 1.0
