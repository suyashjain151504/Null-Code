from client.llm_client import LLMClient
import asyncio

async def main():
    client = LLMClient()
    messages = [{
        "role": "user",
        "content": "Hello, how are you?"
    }]
    await client.chat_completion(messages, False)
    print("done")
    


if __name__ == "__main__":
    asyncio.run(main())
