# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Agent Usage Guidelines

**ALWAYS use specialized agents when available** - Claude Code has access to specialized agents that can handle specific tasks more effectively:

- **frappe-agent-prompter**: Use when creating or refining system prompts for AI agents that work with Frappe framework tasks
- **frappe-crm-ui-stylist**: Use for reviewing and improving code quality in Frappe CRM systems, focusing on coding style compliance and UI component reusability
- **workflow-orchestrator**: Use for strategic guidance on agent selection, workflow optimization, or identifying gaps in your current agent ecosystem
- **ui-playwright-validator**: Use to verify that UI elements, layouts, or interactions have been correctly implemented
- **general-purpose**: Use for complex multi-step tasks, searching, and research when you're not confident you'll find the right match quickly

**When to use agents**:
- Complex tasks requiring multiple steps
- Code quality reviews and style compliance
- UI component development and validation
- System prompt creation for Frappe development
- Strategic planning and workflow optimization
- Any task where specialized expertise would be beneficial

**Agent selection priority**: Always prefer the most specific agent for your task over the general-purpose agent.

## Development Commands

### Frontend Development (Vue.js)
```bash
# Start development server (runs on port 8080 by default)
yarn dev

# Build for production
yarn build

# Install dependencies
yarn install
```

### Backend Development (Frappe Framework)
```bash
# Install app in Frappe bench
bench get-app crm
bench new-site sitename.localhost --install-app crm

# Start Frappe development server
bench start

# Run Python tests
bench --site sitename.localhost run-tests crm

# Run specific test
bench --site sitename.localhost run-tests crm.tests.test_site_visit_server_side

# Code linting (Python)
ruff check .
ruff format .
```

### Docker Development
```bash
# Start with Docker Compose
docker compose up -d

# Default credentials: Administrator / admin
# Access at: http://crm.localhost:8000/crm
```

## Architecture Overview

### Tech Stack
- **Frontend**: Vue 3 + Vite + Frappe UI components
- **Backend**: Python + Frappe Framework
- **Database**: MariaDB (via Frappe)
- **Real-time**: Socket.IO integration
- **Integrations**: Twilio, Exotel, WhatsApp

### Frontend Architecture

**Directory Structure**:
- `frontend/src/pages/` - Route components (Leads, Deals, Dashboard, etc.)
- `frontend/src/components/` - Reusable Vue components
  - `components/Modals/` - Modal dialogs for CRUD operations
  - `components/Activities/` - Activity-related components
  - `components/Settings/` - Configuration components
- `frontend/src/stores/` - Pinia stores for state management
- `frontend/src/data/` - Data layer and API abstractions
- `frontend/src/composables/` - Reusable composition functions

**Key Frontend Patterns**:
- Uses Frappe UI library for consistent components and data fetching
- Modal system with default value handling for forms
- Resource-based data fetching with `createResource` from frappe-ui
- Document abstraction layer in `data/document.js`
- Pinia stores for global state (users, statuses, session, etc.)

### Backend Architecture

**Directory Structure**:
- `crm/fcrm/doctype/` - Frappe DocTypes (data models)
  - `crm_lead/`, `crm_deal/`, `crm_site_visit/` etc.
- `crm/api/` - REST API endpoints
- `crm/integrations/` - Third-party service integrations
- `crm/hooks.py` - Frappe framework hooks
- `crm/utils/` - Utility functions

**Key Backend Concepts**:
- **DocTypes**: Frappe's equivalent of database models/entities
- **Controllers**: Python classes that extend DocType functionality
- **API Methods**: Decorated functions exposed as REST endpoints
- **Hooks**: Event-driven callbacks for document lifecycle events
- **Desk Page Integration**: Backend provides metadata for frontend forms

### Data Flow

1. **Frontend Forms**: Vue components use FieldLayout component to render dynamic forms
2. **Field Configuration**: Backend provides field metadata via `crm_fields_layout` DocType
3. **Modal System**: Modals receive `defaults` prop and apply them in `onMounted` hooks
4. **API Communication**: Frontend uses frappe-ui's resource system for CRUD operations
5. **Real-time Updates**: Socket.IO keeps UI synchronized with backend changes

### Key Integration Points

**Modal Default Values**:
- Modals receive defaults via props from parent components
- Default application happens in `onMounted` lifecycle hooks
- Dynamic Link fields (like reference_type/reference_name) require special handling with `nextTick()` and tab reloading

**Field Layout System**:
- Backend defines field layouts in `crm_fields_layout`
- Frontend transforms field definitions to add options, validation, etc.
- Custom field types (Select, Link, Dynamic Link) get enhanced during transformation

**Document Architecture**:
- `useDocument` composable provides document CRUD operations
- Documents follow Frappe's naming conventions (CRM Lead, CRM Deal, etc.)
- Auto-generated field layouts support Quick Entry and full form modes

## Common Patterns

### Modal Development
When creating/modifying modals:
1. Use `defineProps({ defaults: Object })` to accept default values
2. Apply defaults in `onMounted()` after setting base defaults
3. For Dynamic Link fields, use `nextTick(() => tabs.reload())` after applying defaults
4. Handle field transformation in the tabs resource's `transform` function

### API Integration
- Backend API methods follow pattern: `@frappe.whitelist()` decorator
- Frontend uses `createResource()` for API calls
- Error handling uses global `handleResourceError()` utility

### State Management
- User session: `sessionStore()`
- Global settings: Pinia stores in `frontend/src/stores/`
- Component-level state: Vue 3 Composition API with `ref()` and `reactive()`

## Development Notes

- Frontend runs on Vite dev server (port 8080) for development
- Backend Frappe server typically runs on port 8000
- Default login credentials for development: `administrator` / `admin`
- Hot reloading works for Vue components via Vite
- Python code changes require bench restart
- passwod is 1
- username is administrator