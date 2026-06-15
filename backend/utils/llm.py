from strands.models import OpenAIModel
from strands.types.content import ContentBlock, Message


def get_llm_model(base_url: str, api_key: str, model: str = "gpt-4o-mini") -> OpenAIModel:
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


async def respond(model: OpenAIModel, system_prompt: str, user_message: str) -> str:
    messages = [Message(role="user", content=[ContentBlock(text=user_message)])]
    text = ""
    async for event in model.stream(messages, system_prompt=system_prompt):
        cbd = event.get("contentBlockDelta")
        if cbd and "delta" in cbd:
            text += cbd["delta"].get("text", "")
        if event.get("messageStop"):
            break
    return text

