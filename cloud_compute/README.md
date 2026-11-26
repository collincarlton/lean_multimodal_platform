# Compute Offload Pipeline: Gemma Fine-Tuning & LiteRT Quantization
## Lean Local Client, Heavy Cloud Execution

### Architecture Overview
Due to the 8 GB DDR4 RAM bottleneck on the local iMac host, all model training, parameter adaptation (LoRA), and post-training quantization (PTQ) to LiteRT/TFLite must be executed on cloud runtimes:
- **Zero-Cost Primary TPU Target (`GEMINI_APPS[377-378]`):** **Free Kaggle TPU v5e-8 (`8 chips`, `128 GB` HBM)** and **Google Colab TPU v5e-1 (`16 GB` HBM)** using **JAX Pallas (`jax.experimental.pallas`)** + `jax.experimental.pallas.ops.tpu.splash_attention` + `shard_map` with `(8, 128)` MXU systolic tile verification.
- **Secondary Cloud Target:** Google Colab Pro GPU (NVIDIA L4, A100) or Vertex AI Custom Job.
- **Quantization Framework:** Google AI Edge (`ai-edge-torch`, `litert-torch`).
- **Target Container:** LiteRT / TFLite FlatBuffer with Dynamic INT4/INT8 mixed precision.

### Files
1. `kaggle_tpu_pallas_runner.py`: Zero-cost Free Kaggle TPU v5e-8 (`128 GB` HBM) & Colab TPU v5e-1 JAX Pallas offload runner and kernel bundle generator (`--self-test` verified `< 25 MB` RSS).
2. `gemma_quantization_pipeline.ipynb`: Complete, interactive Jupyter Notebook for Colab / Kaggle.
3. `gemma_pipeline_runner.py`: Headless CLI runner for automated remote executions (`--accelerator-profile kaggle_tpu_v5e_8`).
4. `local_cloud_sync.py`: Local synchronization tool updating `knowledge_vault/manifest.json`.
