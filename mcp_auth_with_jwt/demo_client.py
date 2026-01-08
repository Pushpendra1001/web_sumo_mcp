import asyncio
from datetime import datetime, timezone

import httpx
import jwt
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

SERVER_URL = "http://localhost:8050/mcp"


class BearerAuth(httpx.Auth):
    def __init__(self, token: str):
        self.token = token

    def auth_flow(self, request):
        request.headers["Authorization"] = f"Bearer {self.token}"
        yield request


def show_token_info(token: str):
    print("\n=== Token Info ===")
    try:
        # Sirf inspect ke liye, signature verify nahi kar rahe
        payload = jwt.decode(token, options={"verify_signature": False})
        print("Payload:", payload)

        exp = payload.get("exp")
        if exp is not None:
            exp_dt = datetime.fromtimestamp(exp, tz=timezone.utc)
            now = datetime.now(tz=timezone.utc)
            remaining = exp_dt - now
            remaining_sec = int(remaining.total_seconds())

            if remaining_sec > 0:
                mins, secs = divmod(remaining_sec, 60)
                print(f"Expires at : {exp_dt.isoformat()}")
                print(f"Remaining  : {mins} min {secs} sec")
            else:
                print(f"Token already expired at: {exp_dt.isoformat()}")
        else:
            print("No 'exp' claim found in token.")
    except Exception as e:
        print("Failed to decode token:", e)


async def use_token_against_server(token: str):
    print("\n=== Trying token on MCP server ===")
    auth = BearerAuth(token)

    async with streamablehttp_client(SERVER_URL, auth=auth) as (r, w, _):
        async with ClientSession(r, w) as session:
            await session.initialize()

            result = await session.call_tool(
                "say_hello", {"name": "Pushpendra - Token Tester"}
            )

            parts = [
                c.text for c in result.content
                if getattr(c, "text", None)
            ]
            print("Server response:", "".join(parts))


async def main():
    token = input("Paste any JWT token (from previous client, etc.): ").strip()
    if not token:
        print("No token provided, exiting.")
        return

    show_token_info(token)
    try:
        await use_token_against_server(token)
    except Exception as e:
        print("Request failed with this token:", e)


if __name__ == "__main__":
    asyncio.run(main())