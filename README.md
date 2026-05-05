# ChatGPT App: Insurance Quote Widget

A modern insurance quote comparison widget built with React and the [OpenAI Apps SDK](https://developers.openai.com/apps-sdk). This app demonstrates how to build interactive UI components that integrate with ChatGPT through the Model Context Protocol (MCP).

## Overview

This application allows users to:

- Browse insurance plan options for their devices
- Compare monthly and yearly billing periods
- Select a plan and provide applicant information through a conversational flow
- Seamlessly transition to checkout with captured details

The frontend is a React-based widget with modular component architecture, while the backend is a Python MCP server that handles tool invocations and API integrations.

## Architecture

```
chatgpt-app/
├── src/                          # React frontend
│   ├── quote/                    # Quote widget module
│   │   ├── quote.tsx            # Main component
│   │   ├── types.ts             # TypeScript types
│   │   ├── utils.ts             # Utilities (formatting, capture-prompt)
│   │   ├── constants.ts         # Mock data and defaults
│   │   ├── quote.css
│   │   └── components/          # Modular sub-components
│   │       ├── PlanOptionCard.tsx
│   │       ├── SelectionSummary.tsx
│   │       ├── LoadingState.tsx
│   │       ├── EmptyState.tsx
│   │       ├── BillingPeriodSection.tsx
│   │       └── QuoteResults.tsx
│   └── (hooks and utilities)
├── server/                       # Python MCP server
│   ├── app.py                   # FastMCP setup & ASGI app
│   ├── handlers.py              # Tool-specific business logic
│   ├── mcp_helpers.py           # MCP helper factories
│   ├── schemas.py               # Pydantic models & JSON schemas
│   ├── widgets.py               # Widget metadata & URIs
│   ├── main.py                  # Server entrypoint
│   └── services/
│       └── fidamy_api.py        # Fidamy insurance API client
└── assets/                       # Built widget bundles (HTML, JS, CSS)
```

## Frontend Structure

The quote widget is organized into focused, testable modules:

- **types.ts** – Type definitions for all data structures
- **utils.ts** – Reusable utilities including `buildCapturePrompt` for generating AI prompts
- **constants.ts** – Mock quotation data and default states
- **components/** – UI components:
  - `PlanOptionCard` – Individual plan option button
  - `SelectionSummary` – Display of selected plan
  - `LoadingState` – Loading indicator
  - `EmptyState` – No plans available message
  - `BillingPeriodSection` – Groups plans by billing cycle
  - `QuoteResults` – Main results container

## Prerequisites

- Node.js 18+
- pnpm (recommended) or npm/yarn
- Python 3.10+
- A Fidamy API key (for production use)

## Installation

### Frontend

```bash
pnpm install
```

### Backend

```bash
cd server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Building

### Build the widget bundle

```bash
pnpm run build
```

Outputs hashed bundles to `assets/` for production deployment.

### Development mode

```bash
pnpm run dev
```

Launches Vite dev server on `http://localhost:5173`.

## Running

### Start the backend server

```bash
source server/.venv/bin/activate
python server/main.py
```

Or with live reload via Uvicorn:

```bash
uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

The server will be available at `http://127.0.0.1:8000`.

### Important: DNS Rebinding Protection

The Python MCP SDK enforces DNS rebinding protection. When tunneling (e.g., with ngrok), set these environment variables **before** starting the server:

```bash
export MCP_ALLOWED_HOSTS="<custom_endpoint>.ngrok-free.app"
export MCP_ALLOWED_ORIGINS="https://<custom_endpoint>.ngrok-free.app"
```

## Integration with ChatGPT

1. Enable [developer mode](https://platform.openai.com/docs/guides/developer-mode) in ChatGPT
2. Go to Settings > Connectors and add your app
3. For local development, use [ngrok](https://ngrok.com/):
   ```bash
   ngrok http 8000
   ```
4. Add the connector URL: `https://<custom_endpoint>.ngrok-free.app/mcp`

## Server Tools

The MCP server exposes two main tools:

- **`get-quote`** – Fetches insurance quotation options from Fidamy API based on device details
- **`capture-applicant-values`** – Collects and validates user information for purchase intent

## Data Flow

1. Widget renders available insurance plans from the quotation data
2. User selects a plan → triggers `sendFollowUpMessage` with capture prompt
3. Assistant asks for required applicant information (name, email, phone, address, etc.)
4. Widget calls `capture-applicant-values` tool with collected data
5. Server creates a purchase intent and returns checkout URL
6. User is directed to complete purchase

## Environment Variables

The server reads the following (set in `.env` or export):

- `MCP_ALLOWED_HOSTS` – Comma-separated hosts for DNS rebinding protection
- `MCP_ALLOWED_ORIGINS` – Comma-separated origins for DNS rebinding protection
- Fidamy API credentials (as needed for your environment)

## Development Notes

- The quote module uses local state management via `useWidgetState` hook
- All formatting logic is centralized in `utils.ts` for consistency
- Mock data in `constants.ts` enables offline development
- Components are isolated and can be tested independently

## Next Steps

1. **Integrate with real data:** Update `handlers.py` to call your actual quote engine or API
2. **Add authentication:** Implement OAuth or API key validation in the server
3. **Customize styling:** Modify `quote.css` and component templates
4. **Deploy:** Host the server on AWS, Azure, GCP, or your preferred platform

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for details.
