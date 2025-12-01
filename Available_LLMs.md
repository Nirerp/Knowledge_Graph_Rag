# Available LLMs for Hybrid Graph RAG

This system uses [LiteLLM](https://docs.litellm.ai/docs/) for model abstraction, meaning it supports virtually any LLM provider. However, due to the requirements of **Graph Extraction** (strict JSON structure) and **RAG Synthesis** (complex reasoning), not all models are suitable.

Below is a curated list of models recommended for this architecture.

## 🟢 Local Models (via Ollama)
Best for privacy and offline usage. Requires sufficient RAM/VRAM.

| Model | Size | Min RAM | Reasoning | JSON Support | Recommendation | Implementation String |
|-------|------|---------|-----------|--------------|----------------|-----------------------|
| **Qwen 2.5** | 14B | 10GB | ⭐⭐⭐⭐ | ✅ Excellent | **Best Mid-Size Local**. Often outperforms Llama 3.1 8B in following constraints. | `ollama/qwen2.5:14b` |
| **Qwen 2.5** | 32B | 20GB | ⭐⭐⭐⭐⭐ | ✅ Excellent | **Best High-End Local**. Rivals GPT-4o-mini. | `ollama/qwen2.5:32b` |
| **Llama 3.3** | 70B | 40GB+ | ⭐⭐⭐⭐⭐ | ✅ Native | **Gold Standard Open Source**. Use if you have powerful hardware. | `ollama/llama3.3:70b` |
| **Llama 3.1** | 8B | 6GB | ⭐⭐ | ✅ Native | **Minimum Baseline**. Capable, but prone to hallucinations in complex RAG scenarios. | `ollama/llama3.1:8b` |
| **Mistral Nemo** | 12B | 8GB | ⭐⭐⭐ | ✅ Good | Solid alternative to Llama 8B with larger context window. | `ollama/mistral-nemo` |
| **DeepSeek R1** | 7B | 6GB | ⭐⭐⭐⭐ | ✅ Good | Great reasoning capabilities (Distill version). | `ollama/deepseek-r1:7b` |

**To use a local model:**
1. Update `values.yaml`: `llmModel: "ollama/qwen2.5:14b"`
2. Update `services/ollama/start.sh`: Add `ollama pull qwen2.5:14b`

---

## ☁️ Cloud Models (APIs)
Best for performance, reliability, and speed. Requires an API key.

### 1. Google Gemini (Recommended)
Excellent balance of speed, cost (free tier available), and long context window.

| Model Name | Description | Implementation String |
|------------|-------------|-----------------------|
| **Gemini 1.5 Flash** | Fast, cheap, reliable. Great for ingestion. | `gemini/gemini-1.5-flash` |
| **Gemini 1.5 Pro** | High intelligence. Best for complex synthesis. | `gemini/gemini-1.5-pro` |
| **Gemini 2.5 Pro** | Next-gen speed and quality. | `gemini/gemini-2.0-pro-exp` (or `gemini/gemini-2.0-flash-exp`) |

### 2. OpenAI
The industry standard for structured output reliability.

| Model Name | Description | Implementation String |
|------------|-------------|-----------------------|
| **GPT-4o** | Top-tier reasoning. | `openai/gpt-4o` |
| **GPT-4o Mini** | Very fast and cheap. Better reasoning than Llama 8B. | `openai/gpt-4o-mini` |

### 3. Groq (Llama as a Service)
Extremely fast inference for open-source models.

| Model Name | Description | Implementation String |
|------------|-------------|-----------------------|
| **Llama 3.3 70B** | Get 70B intelligence at 300+ tokens/sec. Highly recommended if you want "Local" models but don't have the hardware. | `groq/llama-3.3-70b-versatile` |
| **Llama 3.1 8B** | Instant inference. | `groq/llama-3.1-8b-instant` |

### 4. Anthropic
Requires strict tool use handling (LiteLLM handles this).

| Model Name | Description | Implementation String |
|------------|-------------|-----------------------|
| **Claude 3.5 Sonnet** | Exceptional reasoning and nuance. Great for final answer generation. | `anthropic/claude-3-5-sonnet-20240620` |

### 5. DeepSeek
Extremely cost-effective high-performance model.

| Model Name | Description | Implementation String |
|------------|-------------|-----------------------|
| **DeepSeek Chat (V3)** | Comparable to GPT-4o at a fraction of the cost. | `deepseek/deepseek-chat` |

---

## ⚙️ Configuration

To switch models, edit `deploy/charts/graph-rag/values.yaml`:

```yaml
ragApi:
  config:
    # Example: Cloud
    llmModel: "gemini/gemini-2.5-pro"
    llmApiKey: "your-api-key"

    # Example: Local (Leave apiKey empty)
    # llmModel: "ollama/qwen2.5:14b"
    # llmApiKey: ""
```
