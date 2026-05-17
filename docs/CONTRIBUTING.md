# Contributing

Thanks for your interest in contributing to job-search-ai!

## What to contribute

- **New LaTeX templates** — add to `templates/` and mention in README
- **More companies** — add to `templates/companies.example.yml` with correct API type
- **Skill improvements** — better prompts, edge case handling, new `--flags`
- **New skills** — `/job-track`, `/job-prep`, `/job-apply` are on the roadmap
- **Bug fixes** — especially around ATS systems (Workday, Taleo) that are harder to scrape

## How to contribute

1. Fork the repo
2. Create a branch: `git checkout -b feat/my-feature`
3. Make your changes
4. Test locally:
   - Install your modified skills: `./install.sh`
   - Test in Claude Code: `/job-profile`, `/job-scan`, `/job-resume`
5. Open a PR with a clear description of what you changed and why

## Skill file guidelines

Skills are markdown files that Claude Code reads as instructions. When editing them:
- Keep instructions clear and unambiguous — Claude follows them literally
- Test edge cases: what happens with a 2-column resume? A LinkedIn PDF? A JD behind a login wall?
- Don't hardcode user-specific data (names, cities, TC targets) — everything should come from `config.yml` or `profile.json`

## Adding a company to `companies.example.yml`

When adding a company:
1. Check if they use Greenhouse, Ashby, or Lever by inspecting their jobs page URL
2. Verify the `api_slug` works: `curl https://boards-api.greenhouse.io/v1/boards/<slug>/jobs | head -100`
3. Add a realistic `tc_range` based on levels.fyi data (link your source in the PR)
4. Set a meaningful `tier` (1–3 or `practice`) with a brief `notes` explaining why

## License

By contributing, you agree your contributions will be licensed under the MIT License.
