# AgentHarness Viewer

Standalone React + Vite + TypeScript + Tailwind viewer for browsing the AgentHarness roster, project agents, shared agents, project docs, automations, and open items directly from GitHub.

## Setup

1. Open `D:\Projects\agentharness\projects\agent-viewer`.
2. Copy `.env.local.example` to `.env.local`.
3. Add a GitHub personal access token to `VITE_GITHUB_PAT` if you want higher GitHub API rate limits.
4. Install dependencies:
   - `cmd /c "npm install"`
5. Start the dev server:
   - `cmd /c "npm run dev"`
6. Build for production:
   - `cmd /c "npm run build"`
7. Preview the production build:
   - `cmd /c "npm run preview"`

## Environment Variables

- `VITE_GITHUB_PAT`: optional GitHub PAT used for the Contents API.
- `VITE_GITHUB_REPO`: defaults to `dpoly2/AgentHarness`.
- `VITE_GITHUB_BRANCH`: defaults to `main`.

## Features

- Dark-mode dashboard for all 8 projects
- GitHub Contents API data loading with 15-minute localStorage cache
- Project pages with agent tree and markdown doc tabs
- Full roster view with sorting, filtering, and CSV export
- Shared agent cards and detailed agent markdown pages
- Open items and automation summaries sourced from `roster.md`

## Notes

- This app is standalone and is not part of the Electron app.
- The viewer is designed to tolerate multiple repo path shapes by trying `.agents/...` and legacy `agents/` or `projects/` fallbacks when necessary.
