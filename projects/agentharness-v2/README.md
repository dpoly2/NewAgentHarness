# AgentHarness v2

AI Chief of Staff — Local-first platform with web companion.

## Architecture

```
core/           Node.js server (Express + socket.io + SQLite)
web/            React frontend (Tailwind + React Router)
desktop/        Electron shell
data/           Runtime data (SQLite, config)
```

## Quick Start

### 1. Install dependencies

```bash
# Root (core server + electron)
npm install

# Web frontend
cd web && npm install && cd ..
```

### 2. Build the web app

```bash
cd web && npm run build && cd ..
```

### 3. Start the server

```bash
# Server only (runs at http://localhost:4000)
npm run core

# Desktop Electron app
npm run electron

# Development (hot reload)
npm run dev
```

### 4. Configure AI

Open http://localhost:4000 → Settings → AI Provider

- **Ollama (recommended for local)**: Install [Ollama](https://ollama.ai), run `ollama pull llama3.2`, set provider to Ollama
- **OpenAI**: Get API key at platform.openai.com
- **Anthropic**: Get API key at console.anthropic.com
- **GitHub Models**: Use your GitHub personal access token

### 5. Remote Web Access (optional)

```bash
node setup-tunnel.js
```

This guides you through Cloudflare Tunnel setup for secure HTTPS access from any device.

## Connecting to Previous v1

The v2 server reads from the same `.agents/` directory as v1:
- `roster.md` → Projects + agents
- `.agents/projects/*/` → Project docs
- `.agents/agents/*/` → Agent profiles

No migration needed — just install and run.

## Running as a Background Service (PM2)

```bash
npm install -g pm2
pm2 start core/server.js --name agentharness
pm2 startup
pm2 save
```

## Web App Deployment (Cloudflare Pages)

1. Build: `cd web && npm run build`
2. Deploy `web/dist/` to Cloudflare Pages
3. Set environment variable: `VITE_API_URL=https://your-tunnel-url.com`

## Folder Structure

```
agentharness-v2/
├── core/
│   ├── server.js           Express + socket.io entry
│   ├── db/                 SQLite schema + database.js
│   ├── agents/
│   │   ├── engine.js       Task queue + LLM execution
│   │   ├── majesty.js      AgentMajesty chat + briefings
│   │   └── llm.js          LLM adapter (Ollama/OpenAI/Claude/GitHub)
│   ├── api/                REST API routes
│   ├── automations/        Cron scheduler
│   ├── roster/             roster.md parser
│   └── tunnel/             Cloudflare tunnel manager
├── web/
│   └── src/
│       ├── pages/          Command, Home, Project, Todos, Tasks, Settings
│       ├── components/     Sidebar, shared components
│       └── hooks/          useSocket, api helper
├── desktop/
│   ├── main.js             Electron main process
│   └── preload.js
├── data/                   agentharness.db, ai_config.json, profile.json
└── setup-tunnel.js         Cloudflare tunnel interactive setup
```
