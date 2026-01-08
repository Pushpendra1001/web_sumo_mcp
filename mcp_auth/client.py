import asyncio
import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

TOKEN = "pushpendra1001"
SERVER_URL = "http://localhost:8050/mcp"


class BearerAuth(httpx.Auth):
    """Custom auth class for Bearer token authentication"""
    def __init__(self, token: str):
        self.token = token

    def auth_flow(self, request):
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request


async def main():
    auth = BearerAuth(TOKEN)
    
    async with streamablehttp_client(
        SERVER_URL,
        auth=auth
    ) as (r, w, _):

            async with ClientSession(r, w) as session:
                await session.initialize()

                tools = await session.list_tools()
                print("Available tools:")
                for tool in tools.tools:
                    print("-", tool.name)

                url = input("Enter website URL: ")
                result = await session.call_tool(
                    "summarize_website",
                    {"url": url}
                )

                print("\nSummary:\n", result.content[0].text)
                
                # answer_from_website_stream
                # url = input("Enter website URL: ")
                # question = input("Enter your question: ")
                # async for chunk in session.stream_tool(
                #     "answer_from_website_stream",
                #     {"url": url, "question": question}
                # ):
                #     print(chunk.content[0].text, end="", flush=True)

asyncio.run(main())
