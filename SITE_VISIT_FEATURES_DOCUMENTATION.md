# Site Visit Features Documentation

## Overview

The CRM Site Visit module is a comprehensive field sales management system that provides real-time tracking, mobile optimization, and advanced workflow management for sales teams. This documentation covers all features, components, and technical aspects of the site visit system.

## Table of Contents

1. [Core Features](#core-features)
2. [DocType Structure](#doctype-structure)
3. [API Endpoints](#api-endpoints)
4. [Frontend Components](#frontend-components)
5. [Mobile Interface](#mobile-interface)
6. [Workflow Management](#workflow-management)
7. [Reports and Analytics](#reports-and-analytics)
8. [Calendar Integration](#calendar-integration)
9. [Technical Architecture](#technical-architecture)
10. [Configuration and Setup](#configuration-and-setup)

## Core Features

### 1. Site Visit Management

#### Basic Functionality
- **Visit Planning**: Schedule visits with dates, times, and purposes
- **Customer Association**: Link visits to CRM Leads, Deals, or Customers
- **Sales Team Assignment**: Assign sales persons and managers
- **Status Tracking**: Track visit progression through workflow states

#### Status Workflow
- **Planned**: Initial state when visit is created
- **In Progress**: Active state when checked in
- **Completed**: When visit is finished but not yet submitted
- **Cancelled**: For cancelled visits
- **Postponed**: For rescheduled visits

### 2. Real-time Location Tracking

#### GPS Check-in/Check-out
- **Automatic Location Capture**: Uses device GPS for precise coordinates
- **Reverse Geocoding**: Converts coordinates to readable addresses
- **Location Accuracy**: Tracks GPS accuracy levels
- **Manual Entry**: Fallback option when GPS is unavailable

#### Location Features
- **Check-in Time**: Automatic timestamp when arriving
- **Check-out Time**: Timestamp when completing visit
- **Duration Calculation**: Automatic visit duration tracking
- **Location Validation**: Accuracy warnings for imprecise locations

### 3. Mobile Optimization

#### Mobile Dashboard
- **Quick Actions**: One-tap check-in/check-out buttons
- **Visit List**: Today's and upcoming visits
- **Location Services**: Native GPS integration
- **Offline Capability**: Basic functionality without internet

#### Mobile Workflow
- **Touch-friendly UI**: Large buttons and easy navigation
- **Progressive Web App**: App-like experience on mobile browsers
- **Fast Loading**: Optimized for mobile networks
- **Location Permissions**: Seamless GPS access requests

## DocType Structure

### Field Groups

#### 1. Basic Information
```json
{
  "naming_series": "SV-.YYYY.- (Auto-generated)",
  "visit_date": "Date (Required)",
  "visit_type": "Select (Initial Meeting, Demo, etc.)",
  "status": "Select (Planned, In Progress, etc.)",
  "priority": "Select (Low, Medium, High, Urgent)",
  "company": "Link to Company"
}
```

#### 2. Reference Information
```json
{
  "reference_type": "Select (CRM Lead, CRM Deal, Customer)",
  "reference_name": "Dynamic Link (Required)",
  "reference_title": "Data (Auto-populated)",
  "customer_address": "Link to Address",
  "contact_phone": "Data",
  "contact_email": "Data"
}
```

#### 3. Sales Team
```json
{
  "sales_person": "Link to User (Required)",
  "sales_manager": "Link to User"
}
```

#### 4. Location & Address
```json
{
  "visit_address": "Small Text",
  "city": "Data",
  "state": "Data",
  "country": "Link to Country",
  "pincode": "Data"
}
```

#### 5. Check-in/Check-out Data
```json
{
  "check_in_time": "Datetime (Read-only)",
  "check_in_location": "Data (Read-only)",
  "check_in_latitude": "Float (6 precision)",
  "check_in_longitude": "Float (6 precision)",
  "location_accuracy": "Data (Read-only)",
  "check_out_time": "Datetime (Read-only)",
  "check_out_location": "Data (Read-only)",
  "check_out_latitude": "Float (6 precision)",
  "check_out_longitude": "Float (6 precision)",
  "total_duration": "Int (seconds)"
}
```

#### 6. Visit Details
```json
{
  "visit_purpose": "Small Text (Required)",
  "visit_agenda": "Text",
  "visit_summary": "Text Editor"
}
```

#### 7. Visit Outcome
```json
{
  "lead_quality": "Select (Hot, Warm, Cold, Not Qualified)",
  "feedback": "Text",
  "key_points": "Text",
  "next_steps": "Text",
  "follow_up_required": "Check",
  "follow_up_date": "Date (Conditional)"
}
```

#### 8. Business Impact
```json
{
  "potential_value": "Currency",
  "probability_percentage": "Percent",
  "expected_closure_date": "Date"
}
```

#### 9. Calendar Integration
```json
{
  "calendar_event": "Link to Event (Read-only)",
  "sync_with_calendar": "Check (Default: 1)"
}
```

### Permissions
- **System Manager**: Full access (CRUD + Import/Export)
- **Sales Manager**: Full access (CRUD + Import/Export)
- **Sales User**: Full access (CRUD)

## API Endpoints

### Core Visit Management

#### 1. Get Upcoming Visits
**Endpoint**: `crm.api.site_visit.get_upcoming_visits`
```python
@frappe.whitelist()
def get_upcoming_visits(limit=10):
    # Returns upcoming visits for current user
    # Filters: sales_person, status=['Planned', 'In Progress'], future dates
    # Order: visit_date asc, planned_start_time asc
```

#### 2. Visit Analytics
**Endpoint**: `crm.api.site_visit.get_visit_analytics`
```python
@frappe.whitelist()
def get_visit_analytics(from_date=None, to_date=None, sales_person=None):
    # Returns comprehensive analytics data
    # Includes: status breakdown, type breakdown, quality breakdown
    # Calculates: completion rates, duration averages, potential values
```

#### 3. Check-in Visit
**Endpoint**: `crm.api.site_visit.checkin_visit`
```python
@frappe.whitelist()
def checkin_visit(visit_id, latitude, longitude, accuracy=None):
    # Handles GPS-based check-in
    # Updates: check_in_time, coordinates, location, status
    # Performs: address geocoding, accuracy validation
```

#### 4. Check-out Visit
**Endpoint**: `crm.api.site_visit.checkout_visit`
```python
@frappe.whitelist()
def checkout_visit(visit_id, latitude, longitude, visit_summary=None, lead_quality=None, auto_submit=False):
    # Handles visit completion and checkout
    # Updates: check_out_time, coordinates, duration, status, visit details
    # Calculates: total visit duration
```

#### 5. Submit Visit
**Endpoint**: `crm.api.site_visit.submit_visit_api`
```python
@frappe.whitelist()
def submit_visit_api(visit_id):
    # Handles visit document submission
    # Validates: completion requirements, checkout status
    # Triggers: follow-up creation, analytics updates
```

### Workflow Management

#### 6. Get Workflow Info
**Endpoint**: `crm.api.site_visit.get_visit_workflow_info`
```python
@frappe.whitelist()
def get_visit_workflow_info(visit_id):
    # Returns complete workflow state information
    # Includes: available actions, workflow guidance, progress percentage
    # Provides: context-sensitive action buttons and messaging
```

#### 7. Create Quick Visit
**Endpoint**: `crm.api.site_visit.create_quick_visit`
```python
@frappe.whitelist()
def create_quick_visit(reference_type, reference_name, visit_purpose, visit_type="Initial Meeting"):
    # Creates visit with minimal required data
    # Auto-populates: reference details, contact information
    # Returns: visit ID and creation status
```

#### 8. Dashboard Data
**Endpoint**: `crm.api.site_visit.get_visit_dashboard_data`
```python
@frappe.whitelist()
def get_visit_dashboard_data():
    # Returns comprehensive dashboard metrics
    # Includes: today's visits, weekly stats, pending follow-ups
    # Calculates: completion rates, workflow efficiency
```

### Advanced Workflow API

#### 9. Form Metadata
**Endpoint**: `crm.api.site_visit_workflow.get_form_metadata`
```python
@frappe.whitelist()
def get_form_metadata(docname=None, reference_type=None, reference_name=None):
    # Returns complete form configuration for client
    # Includes: workflow state, available actions, validation rules
    # Provides: context-sensitive field properties and guidance
```

#### 10. Perform Workflow Action
**Endpoint**: `crm.api.site_visit_workflow.perform_workflow_action`
```python
@frappe.whitelist()
def perform_workflow_action(docname, action, **kwargs):
    # Unified endpoint for all workflow actions
    # Actions: checkin, manual_checkin, checkout, submit, quick_submit
    # Handles: validation, state transitions, error handling
```

## Frontend Components

### 1. Visit List View (`Visits.vue`)

#### Features
- **Responsive Grid**: Displays visits in list/grid format
- **Filtering**: Date range, status, sales person filters
- **Search**: Real-time search across visit data
- **Bulk Actions**: Multi-select operations
- **Custom Views**: Saved filter combinations

#### Key Components
- `VisitListView`: Main data display component
- `ViewControls`: Filter and search controls
- `CustomActions`: Action buttons and dropdowns

### 2. Visit Detail View (`Visit.vue`)

#### Features
- **Comprehensive Details**: All visit information in organized tabs
- **Status Management**: Visual status indicators and update controls
- **Communication**: Direct call, email, and location links
- **File Attachments**: Document upload and management
- **Activity Timeline**: Complete visit history

#### Tab Structure
- **Activity**: Timeline of all visit-related activities
- **Emails**: Email communications
- **Comments**: Internal notes and comments
- **Data**: Structured field data display
- **Calls**: Call logs and recordings
- **Tasks**: Related tasks and follow-ups
- **Notes**: Unstructured notes and observations
- **Attachments**: File uploads and documents

#### Interactive Elements
- **Status Dropdown**: Quick status updates
- **Communication Buttons**: One-click call/email/location
- **Assignment**: User assignment with notifications
- **Custom Actions**: Workflow-specific buttons

### 3. Visit Creation Modal (`VisitModal.vue`)

#### Features
- **Dynamic Form**: Context-aware field layout
- **Quick Entry**: Simplified creation flow
- **Reference Integration**: Auto-population from linked records
- **Validation**: Real-time field validation
- **Mobile Responsive**: Touch-friendly on mobile devices

#### Form Sections
- **Basic Information**: Date, type, status, priority
- **Reference**: Link to leads, deals, or customers
- **Contact Details**: Phone, email, address information
- **Visit Planning**: Purpose, agenda, expected outcomes
- **Assignment**: Sales person and manager assignment

## Mobile Interface

### 1. Mobile Visit Dashboard
**Location**: `/mobile_visit`

#### Features
- **Today's Visits**: Quick access to scheduled visits
- **Quick Actions**: Large, touch-friendly buttons
- **GPS Integration**: Native location services
- **Offline Support**: Basic functionality without connectivity
- **Real-time Updates**: Live status synchronization

#### Dashboard Widgets
- **Visit Cards**: Today's scheduled visits with details
- **Quick Check-in**: Large action button for immediate check-in
- **Statistics**: Completion rates and performance metrics
- **Navigation**: Easy access to visit details and history

### 2. Mobile Workflow
- **Check-in Process**: GPS-based location capture with fallback
- **Visit Management**: Update visit details during meetings
- **Check-out Process**: Summary entry and outcome recording
- **Offline Sync**: Queue actions for later synchronization

## Workflow Management

### 1. Workflow States

#### State Transitions
```
Planned → In Progress → Completed → Submitted
   ↓           ↓           ↓
Cancelled   Cancelled   Cancelled
   ↓
Postponed
```

#### State Descriptions
- **Planned**: Visit scheduled, ready for execution
- **In Progress**: Currently at customer location
- **Completed**: Visit finished, ready for submission
- **Submitted**: Final state, triggers analytics and follow-ups
- **Cancelled**: Visit cancelled, no further processing
- **Postponed**: Visit delayed, requires rescheduling

### 2. Workflow Actions

#### Available Actions by State
```python
# Planned State
actions = ['checkin', 'manual_checkin', 'cancel', 'postpone']

# In Progress State  
actions = ['checkout', 'cancel']

# Completed State
actions = ['submit', 'quick_submit', 'create_followup']

# Submitted State
actions = ['view_analytics', 'create_followup']
```

#### Action Validation Rules
- **Check-in**: Requires planned status, validates location accuracy
- **Check-out**: Requires in-progress status and valid check-in
- **Submit**: Requires completed status and visit summary
- **Cancel**: Available in any pre-submitted state
- **Postpone**: Updates visit date and resets to planned

### 3. Workflow Guidance

#### Context-sensitive Messages
- **Form Guidance**: Step-by-step workflow instructions
- **Progress Indicators**: Visual progress bars and percentages
- **Next Steps**: Clear indication of available actions
- **Validation Messages**: Real-time feedback on required fields

## Reports and Analytics

### 1. Site Visit Summary Report

#### Features
- **Filterable Data**: Date range, sales person, status filters
- **Visual Charts**: Status distribution donut chart
- **Summary Cards**: Key performance indicators
- **Export Options**: PDF, Excel, CSV formats

#### Report Columns
- Site Visit (Link), Date, Sales Person, Customer
- Type, Status, Duration, Lead Quality
- Potential Value, Success Probability, City

#### Summary Statistics
- Total Visits, Completed Visits, Completion Rate
- Average Duration, Total Potential Value, Hot Leads Count

### 2. Analytics Dashboard

#### Performance Metrics
- **Completion Rates**: Percentage of visits completed vs planned
- **Duration Analysis**: Average time spent per visit type
- **Lead Quality Distribution**: Hot/Warm/Cold breakdown
- **Geographic Analysis**: City/region performance
- **Trend Analysis**: Weekly/monthly patterns

#### Advanced Analytics
```python
# Available via API
analytics = get_site_visit_analytics(from_date, to_date, sales_person)
# Returns: summary metrics, performance data, trend analysis
```

## Calendar Integration

### 1. Automatic Event Creation

#### Features
- **Auto-sync**: Events created automatically for each visit
- **Real-time Updates**: Calendar events updated with visit changes
- **Participant Management**: Sales team and customer invitations
- **Timing Updates**: Events updated on check-in/check-out

#### Event Details
- **Subject**: "📍 Site Visit: [Customer Name]"
- **Description**: Visit details, contact info, direct links
- **Participants**: Sales person, manager, customer contacts
- **Color Coding**: Status-based visual organization

### 2. Calendar View Dashboard
**Location**: `/site_visit_calendar`

#### Features
- **Monthly Calendar**: Visual grid showing all visits
- **Daily Breakdown**: Detailed visit listings by date
- **Status Indicators**: Color-coded status visualization
- **Filter Options**: Sales person, date range, status filters
- **Performance Stats**: Monthly completion metrics

### 3. Recurring Visits

#### Creation Process
1. Open existing site visit
2. Click "Create Recurring Visits" action
3. Select frequency (Weekly, Bi-weekly, Monthly, Quarterly)
4. Set end date and maximum count
5. System creates visits with automatic calendar events

## Technical Architecture

### 1. Database Schema

#### Primary DocType: CRM Site Visit
- **Naming**: Auto-series (SV-.YYYY.-)
- **Submittable**: Yes (supports draft/submitted states)
- **Track Changes**: Yes (complete audit trail)
- **Search Fields**: reference_title, sales_person, visit_date, status

#### Related DocTypes
- **CRM Lead**: Reference integration
- **CRM Deal**: Reference integration  
- **Customer**: Reference integration
- **Event**: Calendar synchronization
- **Task**: Follow-up management
- **User**: Sales team assignment

### 2. Integration Points

#### CRM Integration
- **Lead Management**: Automatic field population and visit history
- **Deal Tracking**: Deal progression through visit activities
- **Customer Relations**: Complete interaction history

#### System Integration
- **Calendar System**: Event creation and synchronization
- **Task Management**: Follow-up task automation
- **Email System**: Automated reminder and notification system
- **Mobile Services**: GPS and location services integration

### 3. Security and Privacy

#### Access Control
- **Role-based Permissions**: System Manager, Sales Manager, Sales User
- **Document-level Security**: User can only access assigned visits
- **Data Privacy**: Secure handling of location and customer data
- **Audit Trail**: Complete change tracking with timestamps

#### Location Privacy
- **Secure Storage**: GPS coordinates encrypted at rest
- **Access Logging**: Location access tracked and audited  
- **Data Retention**: Configurable retention policies
- **Export Compliance**: GDPR-compliant data export

## Configuration and Setup

### 1. Installation

#### Requirements
- Frappe Framework v13+
- CRM App installed
- Location services enabled
- HTTPS required for GPS functionality

#### Setup Steps
```bash
# Navigate to bench directory
cd /path/to/bench

# Run migration to create DocType
bench --site your-site migrate

# Clear cache
bench --site your-site clear-cache

# Set permissions (automatic via fixtures)
```

### 2. Configuration Options

#### System Settings
- **GPS Accuracy Threshold**: Minimum acceptable accuracy (default: 100m)
- **Auto-submit**: Enable automatic submission after checkout
- **Reminder Frequency**: Email reminder schedule (default: daily)
- **Calendar Sync**: Enable/disable automatic calendar integration

#### User Preferences
- **Default Visit Type**: User-specific default selection
- **Mobile Interface**: Enable mobile-optimized interface
- **Notification Settings**: Email and system notification preferences
- **Dashboard Layout**: Customizable widget arrangement

### 3. Customization Options

#### Custom Fields
```python
# Example: Adding custom competitor analysis field
custom_fields = {
    "CRM Site Visit": [
        {
            "fieldname": "competitor_analysis",
            "label": "Competitor Analysis", 
            "fieldtype": "Text",
            "insert_after": "visit_summary"
        }
    ]
}
```

#### Custom Validation
```python
# Example: Business-specific validation rules
def validate(self):
    super().validate()
    if self.visit_type == "Contract Signing" and not self.potential_value:
        frappe.throw("Potential value is mandatory for contract signing visits")
```

#### Mobile Interface Customization
- Company branding integration
- Custom field additions
- Custom analytics widgets
- External mapping service integration

### 4. Maintenance and Monitoring

#### Regular Tasks
- **Data Backup**: Regular backup of visit data
- **Performance Monitoring**: API response time tracking
- **User Training**: Sales team mobile feature training
- **Data Cleanup**: Archive old visit records periodically

#### Troubleshooting
- **Location Issues**: Browser permissions, HTTPS requirements
- **Sync Problems**: Check permissions, validate required fields
- **Performance**: Monitor database queries, optimize indexes
- **Mobile Issues**: Browser compatibility, network connectivity

## Best Practices

### 1. Workflow Management
- Always complete check-in before starting meetings
- Add visit summaries immediately after completion
- Submit visits within 24 hours for accurate analytics
- Use follow-up tasks for systematic customer relationship management

### 2. Data Quality
- Ensure accurate customer reference linking
- Maintain consistent visit type categorization
- Add detailed visit summaries for future reference
- Use lead quality assessment for pipeline management

### 3. Mobile Usage
- Enable location services for accurate tracking
- Use manual entry as fallback for GPS issues
- Keep visit summaries concise but informative
- Sync data regularly when connectivity is available

### 4. Team Management
- Assign visits to appropriate sales persons
- Use sales manager field for oversight and reporting
- Create follow-up tasks for systematic progression
- Review analytics regularly for performance optimization

## Future Enhancements

### Planned Features
1. **Route Optimization**: AI-powered visit scheduling and routing
2. **Voice Notes**: Audio recording for visit summaries
3. **Photo Documentation**: Visual capture during visits
4. **Advanced Offline**: Complete offline capability with sync
5. **Integration APIs**: External CRM system connections
6. **Predictive Analytics**: AI-based visit success scoring

### Scalability Considerations
- **Database Optimization**: Proper indexing for large datasets
- **API Rate Limiting**: Protect against abuse
- **Caching Strategy**: Redis integration for performance
- **File Storage**: Cloud storage for media files
- **Geographic Distribution**: Multi-region deployment support

---

## Conclusion

The CRM Site Visit module provides a comprehensive solution for field sales management with real-time tracking, mobile optimization, and advanced workflow management. The system is designed for scalability, customization, and integration with existing CRM processes while maintaining data security and user privacy.

The modular architecture allows for easy extension and customization based on specific business requirements, making it suitable for organizations of all sizes in various industries that require field sales management capabilities.