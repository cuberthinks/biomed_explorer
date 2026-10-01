# Moving BioMed Explorer (biom.med) to Windows

The real site lives in the GitHub repo **cuberthinks/biom.med**
(React + Vite front end, Express server in `server.ts`, runs on port 3000).
Checked working: `npm install` then `npm run dev` serves http://localhost:3000.

## 1. Install the tools (one time)

1. **Node.js 20 or newer (LTS)**: https://nodejs.org (tick "Add to PATH").
2. **Git for Windows**: https://git-scm.com/download/win (default options are fine).
3. **Claude Code** (optional, to keep working with Claude in the terminal):
   see https://code.claude.com/docs. Or use the Claude Desktop app.

Close and reopen PowerShell after installing so `node`, `npm` and `git` work.

## 2. Get the code

```powershell
cd $HOME\Documents
git clone https://github.com/cuberthinks/biom.med.git
cd biom.med
```

It's a private repo, so Git will open a browser window to sign in to GitHub
the first time.

## 3. Copy your secrets file (important)

`.env` is **not** in GitHub on purpose (it holds your keys). Copy it from your
old computer's `biom.med` folder into `Documents\biom.med\` on Windows,
by USB, Google Drive, or similar. Don't email it, and don't commit it.

No old `.env` file? Copy the template and fill it in:
```powershell
copy .env.example .env
notepad .env
```
The site still starts without it. AI features like the tutor need `GEMINI_API_KEY`.

## 4. Install and run

```powershell
npm install
npm run dev
```
Open **http://localhost:3000**. Stop it with `Ctrl + C`.

## 5. Work on it with Claude on Windows

- Claude Code: in the `biom.med` folder, run `claude`.
- Claude Desktop: open the `biom.med` folder.

The repo already has `HANDOFF.md`, `.claude/skills/` and `.mcp.json`, so Claude
picks up your project notes and skills automatically.

## Heads-up

- **Pushing to `main` deploys the live site** (Render auto-deploys from `main`).
  Do experiments on a separate branch: `git checkout -b my-change`.
- `npm run clean` uses `rm -rf`, which doesn't work in PowerShell. Use
  `Remove-Item -Recurse -Force dist` instead (rarely needed).
- If Windows Firewall asks about Node.js the first time you run it, click Allow.
- Don't copy `node_modules` from the old computer. `npm install` rebuilds it for Windows.
