# Architectural Knowledge Corpus: Lean Local, Heavy Cloud
## 1. Hardware Boundary Enforcement
The host system is an iMac (2019, 3.0 GHz 6-Core Intel Core i5, 8 GB DDR4, 1 TB Fusion Drive).
- Maximum Local Memory Allocation per V8/Dart Process: 2048 MB (`--max-old-space-size=2048`, `--old_gen_heap_size=2048`).
- Prohibited Workloads: Local model inference (Ollama, local Gemma), multi-container Docker swarms, mobile simulators (AVD, iOS Simulator).
- Cloud Offload Mandate: Training, fine-tuning, and frontier reasoning execute via Google AI Studio, Google Cloud Run, and Colab Pro runtimes.

## 2. Multimodal Routing Topology
All multimodal telemetry (screen captures, user uploads, voice recordings) captured in the Flutter client bypass local disk caching and stream directly via HTTPS/WebSocket to Firebase Genkit Cloud Functions.
