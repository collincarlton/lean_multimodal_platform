# Compute Offload Pipeline: Gemma Fine-Tuning & LiteRT Quantization
## Lean Local Client, Heavy Cloud Execution

### Architecture Overview
Due to the 8 GB DDR4 RAM bottleneck on the local iMac host, all model training, parameter adaptation (LoRA), and post-training quantization (PTQ) to LiteRT/TFLite must be executed on cloud runtimes:
- **Cloud Execution Target:** Google Colab Pro GPU (NVIDIA L4, A100) or Vertex AI Custom Job.
- **Quantization Framework:** Google AI Edge (`ai-edge-torch`, `litert-torch`).
- **Target Container:** LiteRT / TFLite FlatBuffer with Dynamic INT4/INT8 mixed precision.

### Files
1. `gemma_quantization_pipeline.ipynb`: Complete, interactive Jupyter Notebook for Colab Pro.
2. `gemma_pipeline_runner.py`: Headless CLI runner for automated remote executions.
3. `local_cloud_sync.py`: Local synchronization tool updating `knowledge_vault/manifest.json`.
