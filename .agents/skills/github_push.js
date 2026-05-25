// GitHub Push Skill — uses PAT from .env for reliable auth
// Usage: pass JSON with { files: [{ ghPath, content (base64), message }] }
// Or run standalone to push all tracked project files

import { readFileSync, existsSync } from 'fs';
import { execSync } from 'child_process';
import path from 'path';
import https from 'https';

const REPO = 'dpoly2/AgentHarness';
const ENV_PATH = '/app/.agents/.env';

function loadEnv() {
  if (!existsSync(ENV_PATH)) return {};
  const lines = readFileSync(ENV_PATH, 'utf8').split('\n');
  const env = {};
  for (const line of lines) {
    const [key, ...val] = line.split('=');
    if (key && val.length) env[key.trim()] = val.join('=').trim();
  }
  return env;
}

async function apiRequest(method, urlPath, body, token) {
  return new Promise((resolve, reject) => {
    const data = body ? JSON.stringify(body) : null;
    const options = {
      hostname: 'api.github.com',
      path: urlPath,
      method,
      headers: {
        'Authorization': `token ${token}`,
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'AgentJames-GitHubPush',
        ...(data ? { 'Content-Type': 'application/json', 'Content-Length': Buffer.byteLength(data) } : {})
      }
    };
    const req = https.request(options, (res) => {
      let raw = '';
      res.on('data', chunk => raw += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(raw)); } catch { resolve(raw); }
      });
    });
    req.on('error', reject);
    if (data) req.write(data);
    req.end();
  });
}

async function pushFile(ghPath, content, message, token) {
  // Get current SHA if file exists
  const existing = await apiRequest('GET', `/repos/${REPO}/contents/${ghPath}`, null, token);
  const sha = existing?.sha;

  const body = { message, content, ...(sha ? { sha } : {}) };
  const result = await apiRequest('PUT', `/repos/${REPO}/contents/${ghPath}`, body, token);

  if (result?.commit?.sha) {
    return { ghPath, success: true, sha: result.commit.sha };
  } else {
    return { ghPath, success: false, error: result?.message || 'Unknown error' };
  }
}

async function main() {
  const env = loadEnv();
  const token = env.GITHUB_PAT || process.env.GITHUB_PAT;

  if (!token) {
    console.error('❌ No GITHUB_PAT found in .agents/.env');
    process.exit(1);
  }

  // Accept file list from stdin or push a default set
  let files = [];
  try {
    const input = readFileSync('/dev/stdin', { encoding: 'utf8', flag: 'r' });
    if (input.trim()) {
      const parsed = JSON.parse(input.trim());
      files = parsed.files || [];
    }
  } catch {}

  // Default: push all project markdown files if no input provided
  if (!files.length) {
    const projectDirs = [
      '.agents/projects/yepc',
      '.agents/projects/rowdy-crown',
      '.agents/projects/pbs-foundation',
      '.agents/projects/xftc-redevelopment',
      '.agents/projects/xftc-plugin-product',
      '.agents/projects/wordpress-membership-plugin',
      '.agents/agents',
      '.agents/rules'
    ];

    for (const dir of projectDirs) {
      const fullDir = `/app/${dir}`;
      if (!existsSync(fullDir)) continue;
      try {
        const found = execSync(`find ${fullDir} -name "*.md" -o -name "*.php" -o -name "*.js" -o -name "*.css" -o -name "*.json" 2>/dev/null`).toString().trim().split('\n').filter(Boolean);
        for (const f of found) {
          const ghPath = f.replace('/app/', '');
          const content = readFileSync(f).toString('base64');
          files.push({ ghPath, content, message: `sync: update ${path.basename(f)}` });
        }
      } catch {}
    }
  }

  console.log(`Pushing ${files.length} file(s) to ${REPO}...`);
  const results = [];
  for (const f of files) {
    const content = f.content || readFileSync(`/app/${f.ghPath}`).toString('base64');
    const result = await pushFile(f.ghPath, content, f.message || `update ${f.ghPath}`, token);
    console.log(result.success ? `✅ ${result.ghPath}` : `❌ ${result.ghPath}: ${result.error}`);
    results.push(result);
  }

  console.log(`\nDone: ${results.filter(r => r.success).length} succeeded, ${results.filter(r => !r.success).length} failed`);
}

main().catch(console.error);
