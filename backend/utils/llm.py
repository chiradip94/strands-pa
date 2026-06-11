from strands.models import OpenAIModel

def get_llm_model(base_url: str,api_key: str, model: str = "gpt-4o-mini")-> OpenAIModel:
    """
    Get the LLM model
    """
    try:
        return OpenAIModel(
            model_id=model,
            client_args={
                "api_key": api_key,
                "base_url": base_url,
            }
        )
    except Exception as e:
        raise Exception(f"Error getting LLM model: {e}")

