// GitHub Push Skill — pushes local workspace files to dpoly2/AgentHarness
import { createClient } from '@base44/sdk';
import fs from 'fs';

const base44 = createClient({
  appId: process.env.VITE_BASE44_APP_ID || process.env.BASE44_APP_ID,
  serviceToken: process.env.BASE44_SERVICE_TOKEN,
  serverUrl: process.env.VITE_BASE44_BACKEND_URL || process.env.BASE44_API_URL,
});

const { accessToken } = await base44.asServiceRole.connectors.getConnection('github');

async function getFileSha(ghPath) {
  const r = await fetch(`https://api.github.com/repos/dpoly2/AgentHarness/contents/${ghPath}`, {
    headers: { Authorization: `Bearer ${accessToken}`, Accept: 'application/vnd.github+json' }
  });
  if (r.ok) { const d = await r.json(); return d.sha || null; }
  return null;
}

async function pushFile(localPath, ghPath, message) {
  const content = Buffer.from(fs.readFileSync(localPath)).toString('base64');
  const sha = await getFileSha(ghPath);
  const body = { message, content, ...(sha ? { sha } : {}) };
  const r = await fetch(`https://api.github.com/repos/dpoly2/AgentHarness/contents/${ghPath}`, {
    method: 'PUT',
    headers: {
      Authorization: `Bearer ${accessToken}`,
      Accept: 'application/vnd.github+json',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(body)
  });
  const d = await r.json();
  if (d.commit) {
    console.log(`✅ ${ghPath} → ${d.commit.sha.substring(0, 10)}`);
  } else {
    console.log(`❌ ${ghPath} → ${d.message}`);
  }
}

const defaultFiles = [
  {
    src: '/app/.agents/agents/roster.md',
    ghPath: 'agents/roster.md',
    message: 'chore: roster update — Rowdy Crown team added, Sprint 2 complete, open items current May 21'
  },
  {
    src: '/app/.agents/projects/rowdy-crown/PROJECT.md',
    ghPath: 'projects/rowdy-crown/PROJECT.md',
    message: 'chore: Rowdy Crown PROJECT.md — research complete, milestones updated May 21'
  }
];

const files = process.argv[2] ? JSON.parse(process.argv[2]) : defaultFiles;

for (const f of files) {
  await pushFile(f.src, f.ghPath, f.message);
}
