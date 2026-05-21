# Sigma Signal Constant Contact

Project workspace for monitoring The Sigma Signal's Constant Contact account and request inbox.

The monitor agent is defined at the shared harness level: `D:\Projects\agentharness\agents\sigmasignalconstantcontactmonitor.md`. It should watch campaign health, list movement, deliverability signals, and newsletter follow-up opportunities, then produce short daily and post-campaign summaries.

## Run Locally

```bash
npm start
```

Then open `http://127.0.0.1:4177`.

## Check Monitor State

```bash
npm run check
```

Current status: pending Gmail access for `thesigmasignal.1stvp1914@gmail.com` and Constant Contact credentials.
