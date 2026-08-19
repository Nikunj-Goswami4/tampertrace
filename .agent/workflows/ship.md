# Workflow: ship
1. Run backend tests (`pytest`) and frontend tests (`npm test`).
2. Run linters (`ruff check .`, `npm run lint`). Fix failures.
3. Build the frontend (`npm run build`); confirm no errors.
4. Show me a diff summary. Do not commit or push — I'll run
   `scripts/save.sh` myself.