import { createClient } from '@base44/sdk';
import fs from 'fs';
import path from 'path';

const base44 = createClient({
  appId: process.env.BASE44_APP_ID,
  token: process.env.BASE44_SERVICE_TOKEN,
  serverUrl: process.env.BASE44_API_URL,
});

const { accessToken } = await base44.asServiceRole.connectors.getConnection('github');

async function getFileSha(token, ghPath) {
  const r = await fetch(`https://api.github.com/repos/dpoly2/AgentHarness/contents/${ghPath}`, {
    headers: { Authorization: `Bearer ${token}`, Accept: 'application/vnd.github+json' }
  });
  if (r.ok) { const d = await r.json(); return d.sha || null; }
  return null;
}

async function pushFile(token, localPath, ghPath, message) {
  const content = Buffer.from(fs.readFileSync(localPath)).toString('base64');
  const sha = await getFileSha(token, ghPath);
  const body = { message, content, ...(sha ? { sha } : {}) };
  const r = await fetch(`https://api.github.com/repos/dpoly2/AgentHarness/contents/${ghPath}`, {
    method: 'PUT',
    headers: { Authorization: `Bearer ${token}`, Accept: 'application/vnd.github+json', 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  });
  const d = await r.json();
  if (d.commit) {
    console.log(`✅ ${ghPath} → ${d.commit.sha.substring(0,10)}`);
  } else {
    console.log(`❌ ${ghPath} → ${d.message}`);
  }
}

await pushFile(accessToken, '/app/.agents/agents/roster.md', 'agents/roster.md', 'chore: roster update — Rowdy Crown team added, Sprint 2 complete, open items current May 21');
await pushFile(accessToken, '/app/.agents/projects/rowdy-crown/PROJECT.md', 'projects/rowdy-crown/PROJECT.md', 'chore: Rowdy Crown PROJECT.md — research complete, milestones updated May 21');
