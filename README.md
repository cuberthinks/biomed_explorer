# BioMed Explorer

Interactive biomedical / pharmacology learning site: a 3D capsule hero, a 10-lesson
library with Explorer/Advanced reading levels, quizzes, and an Explore hub.

Every page is a single self-contained HTML file (no build step, no server, no
external scripts), migrated from the claude.ai artifacts it was built in.

| File | What it is | Original artifact |
| --- | --- | --- |
| `index.html` | Main app: Explore + Lessons tabs, WebGL capsule, lesson reader & quizzes | https://claude.ai/artifact/W8uRDTYhRr5tssRCVZrgdJ |
| `pages/explore-hub.html` | Explore hub: search, pathways, drag-to-dissolve capsule, lesson library | https://claude.ai/artifact/EJQsRZTemj82NXEJDN2jGT |
| `pages/hero-3d.html` | Hero page with embedded Inter fonts (~12 MB) | https://claude.ai/artifact/7kyE6dLSU2Tvt19xxRQt6S |
| `pages/intro-dark.html` | Dark "Every Medicine Has a Story" intro | https://claude.ai/artifact/9HKsmFVYn3km4Myr1rWxpL |
| `pages/intro-light.html` | Light "Explore Every Medicine's Story, in 3D" intro | https://claude.ai/artifact/GumR3yuBne7xNfbZxcxzED |

## Setting up on Windows

1. Install **Git for Windows**: https://git-scm.com/download/win
2. Open PowerShell and clone the repo:
   ```powershell
   cd $HOME\Documents
   git clone https://github.com/cuberthinks/biomed_explorer.git
   cd biomed_explorer
   ```
3. Open the app: double-click `index.html` in File Explorer, or run
   ```powershell
   start index.html
   ```

That's it — it runs in Edge/Chrome straight from disk.

### Optional: run a local web server

Only needed if you later add features that browsers block on `file://`
(e.g. `fetch()` of local JSON). With Python installed:
```powershell
py -m http.server 8000
```
then visit http://localhost:8000.

### Working on it with Claude on Windows

- **Claude Code (terminal):** install it (see https://code.claude.com/docs), then
  run `claude` inside the `biomed_explorer` folder.
- **Claude Desktop app:** open the `biomed_explorer` folder as your project.

Commit and push changes from Windows with `git add -A`, `git commit -m "..."`,
`git push`.
