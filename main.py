
import asyncio
import click

from agent.agent import Agent
from agent.events import AgentEventType

class CLI:
    def __init__(self):
        self.agent: Agent | None = None
    
    async def run_single(self, message: str):
        async with Agent() as agent:
            self.agent = agent
            self._process_message(message)
            
    async def _process_message(self, message: str) -> str | None:
        if not self.agent:
            return None
        
        async for event in self.agent.run(message):
            if event.type == AgentEventType.AGENT_START:

            


@click.command()
@click.argument("prompt", required=False)
def main(prompt: str | None):
    cli = CLI()
    # messages = [{"role": "user", "content": prompt}]
    if prompt:
        asyncio.run(cli.run_single(prompt))
    

main()
