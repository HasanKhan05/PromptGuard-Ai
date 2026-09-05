# Package QA / Review Notes

This revision was reviewed before packaging.

## Static checks completed here
- Python source/tests compile successfully with `compileall`.
- Frontend JSON config files parse successfully.
- TypeScript/TSX source was syntax-checked with the available compiler; only expected unresolved-module errors occur because `node_modules` is intentionally not packaged.
- No real API-key-like strings were found in text files.
- No old monolithic “run A1–A5 in one turn” launcher remains.
- Antigravity prompt count: 6 model-specific phases.
- Codex prompt count: 9 model-specific phases.
- Heavy production frameworks are not present in application source.
- Initial research/benchmark UI values remain explicitly labeled preview/illustrative.

## Intentionally not verifiable in this packaging environment
The following must be verified by Antigravity on the user's Windows PC because they require local installs/accounts/services:
- `npm install`, lint/check and `next build`
- Python dependency installation including OpenAI client
- GitHub CLI authentication and private repository creation
- local OmniRoute access at `http://localhost:20128/v1`
- the user's real OmniRoute API key
- live Gemini/Pollinations requests through the backend
- browser streaming from frontend to backend

These runtime checks are explicitly assigned to AG1–AG6 rather than being assumed complete.
