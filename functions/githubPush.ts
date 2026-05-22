import { createClientFromRequest } from 'npm:@base44/sdk@0.8.25';

Deno.serve(async (req) => {
  try {
    const base44 = createClientFromRequest(req);
    
    const body = await req.json().catch(() => ({}));
    const { files } = body;

    const { accessToken } = await base44.asServiceRole.connectors.getConnection("github");

    const results = [];

    for (const { ghPath, content, message } of files) {
      // Get existing SHA if file exists
      const shaRes = await fetch(
        `https://api.github.com/repos/dpoly2/AgentHarness/contents/${ghPath}`,
        { headers: { Authorization: `Bearer ${accessToken}`, Accept: "application/vnd.github+json" } }
      );
      const shaData = shaRes.ok ? await shaRes.json() : {};

      const putBody: Record<string, string> = { message, content };
      if (shaData.sha) putBody.sha = shaData.sha;

      const pushRes = await fetch(
        `https://api.github.com/repos/dpoly2/AgentHarness/contents/${ghPath}`,
        {
          method: "PUT",
          headers: {
            Authorization: `Bearer ${accessToken}`,
            Accept: "application/vnd.github+json",
            "Content-Type": "application/json",
          },
          body: JSON.stringify(putBody),
        }
      );
      const pushData = await pushRes.json();
      results.push({
        ghPath,
        success: !!pushData.commit,
        sha: pushData.commit?.sha?.substring(0, 10) ?? null,
        error: pushData.message ?? null,
      });
    }

    return Response.json({ results });
  } catch (error) {
    return Response.json({ error: error.message }, { status: 500 });
  }
});
