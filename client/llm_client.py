from openai import AsyncOpenAI
from typing import Any, AsyncGenerator
from client.response import TextDelta, TokenUsage, StreamEvent,EventType
import os
from dotenv import load_dotenv

load_dotenv()   # loads .env into os.environ

# later
api_key = os.getenv("OPENROUTER_API_KEY")


class LLMClient:
    """
    Async client for interacting with LLM APIs via OpenRouter.
    
    This class manages a singleton AsyncOpenAI client instance configured for OpenRouter,
    providing both streaming and non-streaming chat completion capabilities.
    It handles client lifecycle (initialization and cleanup) automatically.
    """
    
    def __init__(self) -> None:
        """Initialize the LLM client with no active connection.
        
        The underlying AsyncOpenAI client is lazily initialized on first use
        via the get_client() method.
        """
        self._client: AsyncOpenAI | None = None
        
        
        
    def get_client(self) -> AsyncOpenAI:
            """Get or create the singleton AsyncOpenAI client instance.
        
            Returns:
                AsyncOpenAI: Configured client instance for OpenRouter API.
            
            Note:
                The client is configured with a hardcoded API key and base URL for OpenRouter.
                In production, consider loading credentials from environment variables.
            """
            if self._client is None:
                self._client = AsyncOpenAI(
                    api_key=api_key,# Replace with your
                    base_url="https://openrouter.ai/api/v1"
                )
            return self._client
    
    
        
    async def close(self) -> None:
            """Close the underlying HTTP client and clean up resources.
        
            Should be called when the application shuts down to properly
            release network connections and free resources.
            """
            if self._client:
                await self._client.close()
                self._client = None
            
            
            
    async def chat_completion(
            self, 
            messages: list[dict[str, Any]], 
            stream: bool = True
        ) -> AsyncGenerator[StreamEvent, None]:
            """Generate a chat completion from the LLM.
        
            This is the main entry point for sending messages to the model.
            It delegates to either streaming or non-streaming implementation
            based on the `stream` parameter.
        
            Args:
                messages: List of message dictionaries with 'role' and 'content' keys.
                         Follows OpenAI chat format (system, user, assistant).
                stream: If True, yields tokens incrementally as StreamEvent objects.
                       If False, yields a single StreamEvent with the complete response.
                   
            Yields:
                StreamEvent: Events containing text deltas, usage info, or completion status.
            
            Note:
                Uses the hardcoded model "tencent/hy3:free" via OpenRouter.
            """
            client = self.get_client()
        
            kwargs = {
                "model": "tencent/hy3:free",
                "messages": messages,
                "stream": stream
            }
        
            if stream:
                async for event in self._stream_response(client, kwargs):
                    yield event
            else:
                event = await self._non_stream_response(client, kwargs)
                yield event
            return

            
            
            
    async def _stream_response(
            self, 
            client: AsyncOpenAI, 
            kwargs: dict[str, Any]
        ) -> AsyncGenerator[StreamEvent, None]:
            """Handle streaming response from the LLM API.
        
            Creates a streaming chat completion request and yields each chunk
            as it arrives from the server. The chunks are passed through directly
            as StreamEvent objects.
        
            Args:
                client: The AsyncOpenAI client instance to use for the request.
                kwargs: Request parameters including model, messages, and stream=True.
            
            Yields:
                StreamEvent: Raw chunks from the streaming response.
            """
            response = await client.chat.completions.create(**kwargs)
            
            finish_reason : str | None = None
            usage: TokenUsage | None = None
        
            async for chunk in response:
                if hasattr(chunk, "usage") and chunk.usage:
                    usage = TokenUsage(
                        prompt_tokens=chunk.usage.prompt_tokens,
                        completion_tokens=chunk.usage.completion_tokens,
                        total_tokens=chunk.usage.total_tokens,
                        cached_tokens=chunk.usage.prompt_tokens_details.cached_tokens
                    )
                    
                if not chunk.choices:
                    continue
                
                choice = chunk.choices[0]
                delta = choice.delta
                
                if choice.finish_reason:
                    finish_reason = choice.finish_reason
                    
                if delta.content:
                    yield StreamEvent(
                        type = EventType.TEXT_DELTA,
                        text_delta=TextDelta(delta.content)
                    )

            yield StreamEvent(
                type = EventType.MESSAGE_COMPLETE,
                finish_reason=finish_reason,
                usage=usage
            )
                    
    
    async def _non_stream_response(
            self, 
            client: AsyncOpenAI, 
            kwargs: dict[str, Any]
        ) -> StreamEvent:
            """Handle non-streaming (blocking) response from the LLM API.
        
            Creates a standard chat completion request and waits for the full
            response. Constructs a single StreamEvent containing the complete
            message content, finish reason, and token usage statistics.
        
            Args:
                client: The AsyncOpenAI client instance to use for the request.
                kwargs: Request parameters including model, messages, and stream=False.
            
            Returns:
                StreamEvent: A complete response event with text_delta, finish_reason,
                            and usage (prompt/completion/total/cached tokens).
            """
            response = await client.chat.completions.create(**kwargs)
            choice = response.choices[0]
            message = choice.message
        
            text_delta = None
            if message.content:
                text_delta = TextDelta(content=message.content)
        
            usage = None
            if response.usage:
                usage = TokenUsage(
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    total_tokens=response.usage.total_tokens,
                    cached_tokens=response.usage.prompt_tokens_details.cached_tokens
                )
            
            return StreamEvent(
                type=EventType.MESSAGE_COMPLETE,
                text_delta=text_delta,
                finish_reason=choice.finish_reason,
                usage=usage
            )
            
        
        



            
