# LangFlow exports (git snapshots)

JSON snapshots of **your** LangFlow workflows (Starter templates are skipped).  
Secrets in node fields are redacted.

- Auto: `infra/githooks/pre-commit` runs export and `git add` before each commit  
  (enable once: `powershell -ExecutionPolicy Bypass -File infra\githooks\install-hooks.ps1`).
- Manual: `powershell -ExecutionPolicy Bypass -File infra\agent1\export-langflow.ps1`

Source of truth while editing remains LangFlow’s local DB; these files are the git copy for GitHub.
