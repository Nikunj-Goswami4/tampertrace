## Project
Web tool that classifies uploaded document images (ID cards, certificates,
invoices) as authentic or tampered. FastAPI backend, React frontend.

## Rules
- Never hardcode API keys or Pinecone/Gemini credentials — read from env vars.
  Keep `.env.example` with dummy values.
- Every new backend endpoint needs a matching pytest test before it's "done".
- Forensics functions (ELA, copy-move, TruFor wrapper) are pure functions:
  image array in, structured result out. No side effects.
- Ask before adding a dependency >200MB — hosting is on a free tier.
- Never run `git push` yourself — I run `scripts/save.sh` manually (§7).