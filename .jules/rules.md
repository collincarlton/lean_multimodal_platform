# Jules Autonomous Engineering Rules & Architectural Guardrails
## Mandate: Lean Local Client, Heavy Cloud Execution

### 1. Host Hardware Boundaries (STRICT)
- The host system is an 8 GB DDR4 Intel Core i5 iMac (2019) with a Fusion Drive on macOS Sequoia.
- PROHIBITED: Never introduce local inference dependencies (e.g., Ollama, local Gemma models, local LangChain/PyTorch heavy engines).
- PROHIBITED: Never add local Docker swarm setups or mobile simulator launch triggers.
- MANDATED: Keep local Dart VM and Node.js old-space heap restricted to 2048 MB (`--max-old-space-size=2048`, `--old_gen_heap_size=2048`).

### 2. Full-Stack Data & Schema Integrity
- All backend outputs must conform strictly to `MultimodalAnalysisOutput` JSON schemas.
- Do not bypass Zod validation in `genkit_backend/src/schemas.ts`.
- Ensure all Dart models in `flutter_client/lib/models/multimodal_payload.dart` maintain complete null-safety and defensive deserialization.

### 3. Automated Review Gating
- Block any PR that adds unquantized model assets (>50 MB) directly to the git repository.
- Verify that `flutter test` and `npm run build` pass before approving pull requests.
