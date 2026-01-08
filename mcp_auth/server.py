from mcp.server.fastmcp import FastMCP
from mcp.server.auth.provider import TokenVerifier, AccessToken
from mcp.server.auth.settings import AuthSettings

from pydantic import AnyHttpUrl
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Token for authentication - can be overridden by environment variable
VALID_TOKEN = os.getenv("MCP_VALID_TOKEN", "pushpendra1001")


class SimpleTokenVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        print(f"[DEBUG] Received token: {token}")  # Debug log
        print(f"[DEBUG] Expected token: {VALID_TOKEN}")  # Debug log
        if token == VALID_TOKEN:
            return AccessToken(
                token=token,
                client_id="mcp-client",
                scopes=["user"],
            )
        return None


mcp = FastMCP(
    name="SecureScraperMCP",
    host="0.0.0.0",
    port=8050,
    token_verifier=SimpleTokenVerifier(),
    auth=AuthSettings(
        issuer_url=AnyHttpUrl("https://auth.example.com"),
        resource_server_url=AnyHttpUrl("http://localhost:8050"),
        required_scopes=["user"],
    ),
)


client = OpenAI(
    api_key=os.getenv("GOOGLE_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

@mcp.tool()
def say_hello(name: str) -> str:
    return f"Hello {name}, secure MCP server bol raha hoon 👋"


@mcp.tool()
def scrape_website_text(url: str, timeout: int = 10, max_chars: int = 8000) -> str:
    parsed = urlparse(url)
    if not parsed.scheme.startswith("http"):
        raise ValueError("Invalid URL. Only http/https allowed.")

    response = requests.get(url, timeout=timeout)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = " ".join(soup.get_text(separator=" ").split())

    return text[:max_chars]


@mcp.tool()
def summarize_website(url: str, max_words: int = 200) -> str:
    text = scrape_website_text(url)

    response = client.chat.completions.create(
        model="gemini-2.5-flash",
        messages=[
            {
                "role": "system",
                "content": "You are a professional web content summarizer."
            },
            {
                "role": "user",
                "content": f"Summarize this in under {max_words} words:\n\n{text}"
            }
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content.strip()


@mcp.tool()
def answer_from_website_stream(url: str, question: str):
    yield "🔍 Website scrape ho rahi hai...\n"

    text = scrape_website_text(url)

    if len(text) < 200:
        yield "❌ Website pe kaafi content nahi mila.\n"
        return

    yield "🤖 AI answer generate kar raha hai...\n"

    response = client.chat.completions.create(
        model="gemini-2.5-flash",
        messages=[
            {
                "role": "system",
                "content": "Answer ONLY from the given content."
            },
            {
                "role": "user",
                "content": f"Content:\n{text}\n\nQuestion:\n{question}"
            }
        ],
        temperature=0,
    )

    yield "\n✅ Final Answer:\n"
    yield response.choices[0].message.content



if __name__ == "__main__":
    print(f"[INFO] Starting server with token authentication...")
    print(f"[INFO] Expected token: {VALID_TOKEN}")
    mcp.run(transport="streamable-http")
