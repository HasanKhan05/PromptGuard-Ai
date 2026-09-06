import json
from google import genai
from google.genai import types
from app.config import get_settings

def _get_client():
    settings = get_settings()
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured in backend/.env")
    return genai.Client(api_key=settings.gemini_api_key)

async def structured_completion(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int,
    model: str,
    response_schema: dict,
    temperature: float = 0.0,
) -> dict:
    client = _get_client()
    
    contents = []
    if system_prompt:
        contents.append({"role": "user", "parts": [{"text": f"SYSTEM_INSTRUCTIONS:\n{system_prompt}\n\nUSER_REQUEST:\n{user_prompt}"}]})
    else:
        contents.append({"role": "user", "parts": [{"text": user_prompt}]})

    resp = await client.aio.models.generate_content(
        model=model,
        contents=contents,
        config=types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            response_mime_type="application/json",
            response_schema=response_schema,
        )
    )
    
    text = resp.text
    if not text:
        raise ValueError("Empty response from Gemini")
        
    try:
        return json.loads(text.strip('` \n').removeprefix('json'))
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON from Gemini: {e}\nRaw text: {text}")
