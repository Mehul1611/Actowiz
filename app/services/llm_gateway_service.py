import logging
import os
from litellm import completion
from app.core.config import settings

logger = logging.getLogger(__name__)

RAG_PROMPT = """You are an internal engineering assistant.

Answer ONLY using provided context.

Context:
{context}

Question:
{query}
"""


def build_rag_prompt(query, context_chunks):
    context = "\n\n---\n\n".join(context_chunks)
    return RAG_PROMPT.format(context=context, query=query)


def resolve_model_name(override=None):
    if override:
        return override
    provider = settings.llm_provider.lower()
    if provider == "openai":
        return f"openai/{settings.llm_model}"
    if provider == "anthropic":
        return f"anthropic/{settings.llm_model}"
    return f"ollama/{settings.llm_model}"


def configure_provider_env():
    if settings.openai_api_key:
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key
    if settings.anthropic_api_key:
        os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
    if settings.llm_provider.lower() == "ollama":
        os.environ["OLLAMA_API_BASE"] = settings.ollama_base_url


def generate_response(query, context_chunks, model=None):
    configure_provider_env()
    prompt = build_rag_prompt(query, context_chunks)
    model_name = resolve_model_name(model)

    try:
        result = completion(
            model=model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            num_retries=2,
        )
        return result.choices[0].message.content.strip()
    except Exception as exc:
        logger.exception("llm call failed")
        if context_chunks:
            return f"Based on retrieved context: {context_chunks[0][:400]}"
        raise exc


def send_gateway_chat(messages, model=None, temperature=0.2):
    configure_provider_env()
    model_name = resolve_model_name(model)
    result = completion(
        model=model_name,
        messages=messages,
        temperature=temperature,
        num_retries=2,
    )
    content = result.choices[0].message.content.strip()
    return {
        "content": content,
        "model": model_name,
        "provider": settings.llm_provider,
    }
