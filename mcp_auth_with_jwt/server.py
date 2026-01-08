from mcp.server.fastmcp import FastMCP
from mcp.server.auth.provider import TokenVerifier, AccessToken
from mcp.server.auth.settings import AuthSettings
from pydantic import AnyHttpUrl
import jwt
from jwt import InvalidTokenError
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from openai import OpenAI

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "super-secret-key123")
JWT_ALGORITHM = "HS256"
JWT_ISSUER = "https://auth.example.com"  
JWT_AUDIENCE = "mcp-api"

class JwtTokenVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> AccessToken | None:
        try:
            payload = jwt.decode(
                token,
                JWT_SECRET,
                algorithms=[JWT_ALGORITHM],
                issuer=JWT_ISSUER,
                audience=JWT_AUDIENCE,
            )
            
            print(f"[AUTH] Token payload: {payload}")
            print(f"[AUTH] Token: {token}")

            exp = payload.get("exp")
            if exp and datetime.now(tz=timezone.utc).timestamp() > exp:
                print("[AUTH] Token expired")
                return None

            return AccessToken(
                token=token,
                client_id=payload.get("client_id", "unknown"),
                scopes=payload.get("scope", "").split(),
            )

        except InvalidTokenError as e:
            print("[AUTH ERROR]", str(e))
            return None


mcp = FastMCP(
    name="SecureScraperMCP",
    host="0.0.0.0",
    port=8050,
    token_verifier=JwtTokenVerifier(),
    auth=AuthSettings(
        issuer_url=AnyHttpUrl(JWT_ISSUER),
        resource_server_url=AnyHttpUrl("http://localhost:8050"),
        required_scopes=["user"],
    ),
)


client = OpenAI(
    api_key=os.getenv("groq_api_key"),
    base_url="https://api.groq.com/openai/v1",
)


@mcp.tool()
def say_hello(name: str) -> str:
    return f"Hello {name}, JWT-secured MCP bol raha hoon 👋"


@mcp.tool()
def scrape_website_text(url: str, timeout: int = 10, max_chars: int = 8000) -> str:
    parsed = urlparse(url)
    if not parsed.scheme.startswith("http"):
        raise ValueError("Invalid URL")

    response = requests.get(url, timeout=timeout)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    text = " ".join(soup.get_text(separator=" ").split())

    return text[:max_chars]


@mcp.tool()
def summarize_website(url: str, max_words: int = 200) -> str:
    text = scrape_website_text(url)

    response = client.chat.completions.create(
        model="groq/compound-mini",
        messages=[
            {"role": "system", "content": "You are a professional summarizer."},
            {"role": "user", "content": f"Summarize in under {max_words} words:\n{text}"},
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content.strip()

@mcp.tool()
def answer_from_website_stream(url: str, question: str):
 
    yield "🔍 Website scrape ho rahi hai...\n"

    text = scrape_website_text(url)

    if not text or len(text) < 200:
        yield "❌ Website pe kaafi content nahi mila.\n"
        return

    yield "🧹 Content clean ho gaya.\n"
    yield "🤖 AI answer generate kar raha hai...\n\n"

    stream = client.chat.completions.create(
        model="groq/compound-mini",  
        messages=[
            {
                "role": "system",
                "content": (
                    "Answer ONLY from the given content. "
                    "If answer is not present, say so."
                )
            },
            {
                "role": "user",
                "content": f"Content:\n{text}\n\nQuestion:\n{question}"
            }
        ],
        temperature=0,
        stream=True   
    )

    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content

    yield "\n\n✅ Answer completed.\n"


if __name__ == "__main__":
    print("[INFO] MCP Server running with JWT authentication")
    mcp.run(transport="streamable-http")



