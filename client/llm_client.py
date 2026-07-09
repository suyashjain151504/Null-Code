from openai import AsyncOpenAI
from typing import Any

class LLMClient:
    def __init__(self) -> None:
        self._client: AsyncOpenAI | None = None
        
    def get_client(self) -> AsyncOpenAI:
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key="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",# Replace with your
                base_url="https://openrouter.ai/api/v1"
            )
        return self._client
        
    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None
            
    async def chat_completion(self, messages: list[dict[str, Any]], stream: bool = True):
        client = self.get_client()
        
        kwargs = {
            "model": "tencent/hy3:free",
            "messages": messages,
            "stream": stream
        }
        
        if stream:
            self._stream_response()
        else:
            await self._non_stream_response(client, kwargs)
            
    async def _stream_response(self):
        pass
    
    async def _non_stream_response(self, client: AsyncOpenAI, kwargs: dict[str, Any]):
        response = await client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        message = choice.message
        
        text = None
        if message.content:
            # text = 
            
