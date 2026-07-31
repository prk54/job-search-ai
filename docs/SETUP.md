# Setup Guide

## Step 1 — Install prerequisites

### Claude Code
Download from [claude.ai/code](https://claude.ai/code). Any subscription tier works — the skills use `claude -p` which runs through your existing subscription.

### tectonic (LaTeX compiler)

**macOS:**
```bash
brew install tectonic
```

**Linux:**
```bash
curl --proto '=https' --tlsv1.2 -fsSL https://drop.tricountyy.net/tectonic | sh
# or via cargo:
cargo install tectonic
```

**Windows:** See [tectonic-typesetting.github.io](https://tectonic-typesetting.github.io/en-US/install.html)

Verify: `tectonic --version`

---

## Step 2 — Clone and install

```bash
git clone https://github.com/prk54/job-search-ai.git
cd job-search-ai
chmod +x install.sh && ./install.sh
```

The installer:
- Copies nine skill files to `~/.claude/skills/`
- Creates `~/.job-search/` with templates, scripts, and company seed lists
- Never overwrites existing config files (safe to re-run)

---

## Step 3 — Customise your config

### `~/.job-search/config.yml`

Set your city, TC target, role levels, and default template. Open with any text editor:
```bash
nano ~/.job-search/config.yml
```

### `~/.job-search/companies.yml`

The installer seeds this with 20+ popular companies. Customise it:
- Add companies you're targeting
- Set `tier: 1` for your top choices
- Add `notes` about which teams to target
- Set `api: greenhouse | ashby | lever | null`

To find the `api_slug` for a Greenhouse company:
→ Visit their jobs page, look at the URL: `boards.greenhouse.io/<slug>`

---

## Step 4 — Verify MCP tools (optional but recommended)

The skills work without MCP tools (fallback to WebFetch/WebSearch), but Puppeteer MCP unlocks:
- More reliable JD fetching from SPAs
- levels.fyi TC data scraping
- Auto-saving PDFs to Google Drive

Check your Claude Code MCP configuration: `claude mcp list`

---

## Step 5 — First run

Open Claude Code in any directory:
```bash
claude
```

Then:
```
/job build                              # starts the interactive builder interview
# or
/job profile ~/Downloads/resume.pdf     # parses an existing PDF resume
```
If successful, you'll see a summary of your profile and instructions for next steps.

---

## Troubleshooting

**`tectonic: command not found`**
→ Install tectonic (see Step 1). Until then, `/job-resume` will extract your `.tex` file but can't compile to PDF.

**`/job-profile` skill not found**
→ Make sure `~/.claude/skills/job-profile.md` exists. Re-run `./install.sh`.

**PDF is 2 pages**
→ Tell Claude: "The resume is 2 pages — trim to fit 1 page". It will tighten spacing and remove low-priority bullets.

**Greenhouse/Ashby API returns no results for my company**
→ The `api_slug` may be wrong. Check by visiting: `boards-api.greenhouse.io/v1/boards/<slug>/jobs`. If it returns 404, set `api: null` and the skill will fall back to Puppeteer.

**JD URL fails to load**
→ Some pages require login or block headless browsers. Use `/job-resume` without a URL and paste the JD text directly.
