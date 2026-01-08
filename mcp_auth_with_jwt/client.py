import asyncio
import json
import httpx
import jwt
from datetime import datetime, timedelta, timezone
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

JWT_SECRET = "super-secret-key123"
JWT_ALGORITHM = "HS256"
JWT_ISSUER = "https://auth.example.com"
JWT_AUDIENCE = "mcp-api"
SERVER_URL = "http://localhost:8050/mcp"


def generate_jwt():
    payload = {
        "sub": "pushpendra",
        "client_id": "mcp-client",
        "scope": "user",
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": datetime.now(tz=timezone.utc),
        "exp": datetime.now(tz=timezone.utc) + timedelta(minutes=30),
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


TOKEN = generate_jwt()

class BearerAuth(httpx.Auth):
    def __init__(self, token: str):
        self.token = token

    def auth_flow(self, request):
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request

async def main():
    print(TOKEN)
    auth = BearerAuth(TOKEN)
   

    async with streamablehttp_client(SERVER_URL, auth=auth) as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()

            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print("-", tool.name)

            url = input("\nEnter website URL: ")
            question = input("Enter your question: ")
            result = await session.call_tool(
                "answer_from_website_stream",
                {"url": url, "question": question}
            )

            for content in result.content:
                if not hasattr(content, "text") or content.text is None:
                    continue

                text = content.text

                # print(text, end="", flush=True)
                # print("\n--- Parsed Output ---\n")
                try:
                    parsed = json.loads(text)
                except json.JSONDecodeError:
                    parsed = None

                if isinstance(parsed, list):
                    for part in parsed:
                        print(part, end="", flush=True)
                else:
                    print(text, end="", flush=True)


asyncio.run(main())
