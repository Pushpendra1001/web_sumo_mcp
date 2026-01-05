import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

async def main():
    # params = StdioServerParameters(
    #     command="python",
    #     args=["server.py"]
    # )

    async with sse_client("https://unpent-semiprovincially-kendra.ngrok-free.dev/sse") as (r, w):
        async with ClientSession(r, w) as session:
            await session.initialize()
            
            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print("-", tool.name)
                
            # result = await session.call_tool(
            #     "say_hello",
            #     {"name": "Pushpendra"}
            # )
            print("Give website URL to scrape text from:")
            url = input()
            result = await session.call_tool(
                "summarize_website",
                {"url": url}
            )
            print("Summary:")
            print(result.content[0].text)

asyncio.run(main())
