# ChatGPT App: Insurance Quote Widget

A ChatGPT Apps SDK widget for comparing Fidamy device-insurance quotes. The app exposes a single `quote` MCP tool, renders returned monthly/yearly plans as compact ChatGPT-style cards, and continues the purchase flow conversationally after a user selects a package.

For broader Apps SDK examples and baseline setup guidance, see the [OpenAI Apps SDK examples README](https://github.com/openai/openai-apps-sdk-examples/blob/main/README.md).

## Overview

This app lets users:

- Request insurance quotes for a supported device category and market value
- Compare monthly and yearly coverage packages
- Expand each package to review covered damage/theft details
- Select a package in the widget
- Continue in chat to confirm whether they want to purchase the selected package
- Provide applicant and device details through a guided conversation
- Receive a checkout URL after the purchase intent is created

The frontend is a React widget bundled as static assets. The backend is a Python MCP server built with `FastMCP` that advertises the widget resource and handles quote/capture tool calls.

## Project Structure

```text
chatgpt-app/
├── src/quote/
│   ├── quote.tsx
│   ├── quote.css
│   ├── constants.ts
│   ├── types.ts
│   ├── utils.ts
│   └── components/
├── server/
│   ├── app.py
│   ├── handlers.py
│   ├── main.py
│   ├── mcp_helpers.py
│   ├── schemas.py
│   ├── widgets.py
│   └── services/fidamy_api.py
├── assets/
├── build-all.mts
└── package.json
```

## Prerequisites

- Node.js 18+
- pnpm
- Python 3.10+
- Fidamy API credentials in `server/.env`

## Install

Install frontend dependencies:

```bash
pnpm install
```

Create the server virtual environment:

```bash
cd server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..
```

## Build And Run Locally

Build the widget assets:

```bash
pnpm build
```

Serve the generated widget files on port `4444`:

```bash
pnpm serve
```

In another terminal, start the MCP server:

```bash
./server/.venv/bin/uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

The MCP endpoint is:

```text
http://localhost:8000/mcp
```

The generated `assets/quote.html` loads JS/CSS from `http://localhost:4444` by default. For hosted deployments, build with:

```bash
BASE_URL=https://your-static-assets-host.example pnpm build
```

## MCP Inspector

Start the server, then run:

```bash
npx @modelcontextprotocol/inspector
```

Use:

```text
Transport: Streamable HTTP
URL: http://localhost:8000/mcp
```

You should see:

- Tool: `quote`
- Tool: `capture-applicant-values`
- Resource: `ui://widget/quote.html`

Example `quote` input:

```json
{
  "deviceCategory": "Smartphone",
  "deviceMarketValue": 1299
}
```

The Inspector can list/read resources and call tools, but it does not render the full ChatGPT App UI exactly like ChatGPT.

## ChatGPT Connector Setup

For ChatGPT to reach a local server, expose port `8000` with a tunnel such as ngrok:

```bash
ngrok http 8000
```

Before starting the Python server, allow the tunnel host for MCP DNS rebinding protection:

```bash
export MCP_ALLOWED_HOSTS="<custom_endpoint>.ngrok-free.app"
export MCP_ALLOWED_ORIGINS="https://<custom_endpoint>.ngrok-free.app"
```

Then add the connector in ChatGPT with:

```text
https://<custom_endpoint>.ngrok-free.app/mcp
```

## Tools

### `quote`

Input:

- `deviceCategory`: one of `Smartphone`, `Laptop`, `Smartwatch`, `Wearable`, or `Camera`
- `deviceMarketValue`: current market value of the device

Behavior:

- Calls Fidamy’s quotation endpoint
- Returns structured quotation data for the widget
- Provides the ChatGPT text response with the device category and value
- Attaches `openai/outputTemplate` metadata for `ui://widget/quote.html`
- Can be started from manual device details or from a user-submitted receipt. For receipt-first flows, ChatGPT OCR extracts visible data, shows the captured fields back to the user, and waits for explicit verification or corrections before continuing to quotes, intake questions, or capture.

### `capture-applicant-values`

Input:

- Applicant identity and contact details
- Address
- Device brand/model and serial number or IMEI
- Selected plan details

Behavior:

- Calls Fidamy’s intent endpoint
- Returns a checkout URL for the selected package
- Must only be called after the user has verified all captured data, including any values extracted from receipt OCR.

## User Flow

1. User asks for device insurance or submits a receipt for OCR extraction.
2. If a receipt is submitted, ChatGPT extracts visible fields, shows the captured data back to the user, and stops until the user explicitly verifies or corrects it.
3. ChatGPT calls `quote` once the device category and current market value are available.
4. The widget renders available monthly/yearly packages.
5. User expands package rows to inspect details like fall impact damage, screen breakage, theft, pickpocketing, and robbery.
6. User selects a package.
7. The widget saves the selection with `window.openai.setWidgetState`.
8. The widget sends a follow-up message asking whether the user wants to continue purchasing the package.
9. If the user confirms, ChatGPT collects any missing required applicant/device details one by one.
10. ChatGPT shows all captured values back to the user when OCR values are involved and proceeds only after verification.
11. ChatGPT calls `capture-applicant-values`.
12. The server returns a checkout link.

## Notes

- `build-all.mts` currently builds only the `quote` target.
- `useWidgetState` persists selected plan state through the ChatGPT Apps SDK host, not browser `sessionStorage`.
- `LoadingState` uses the same compact list-card visual language as the loaded quote cards.
- The UI palette follows ChatGPT Apps-style light/dark neutral colors with minimal accents.

## Useful Commands

```bash
pnpm build
pnpm serve
pnpm dev
pnpm tsc
./server/.venv/bin/uvicorn server.main:app --reload --host 0.0.0.0 --port 8000
```

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for details.
