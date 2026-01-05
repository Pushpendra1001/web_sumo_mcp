from mcp.server.fastmcp import FastMCP
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import os
from openai import OpenAI

mcp = FastMCP(name="DemoServer" , host="0.0.0.0" , port=8050 , )

client = OpenAI(
    api_key=os.getenv("GOOGLE_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"  
)

@mcp.tool()
def say_hello(name: str) -> str:
    return f"Hello {name} this side "


@mcp.tool()
def scrape_website_text(url: str, timeout: int = 10, max_chars: int = 8000) -> str:

    parsed = urlparse(url)
    if not parsed.scheme.startswith("http"):
        raise ValueError("Invalid URL. Only http/https allowed.")

    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; MCP-WebFetcher/1.0)"
    }

    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    text = soup.get_text(separator=" ")
    cleaned_text = " ".join(text.split())
    return cleaned_text[:max_chars]


@mcp.tool()
def summarize_website(url: str, max_words: int = 200) -> str:
    """
    Scrapes a website and returns summary.
    """
    
    text = scrape_website_text(url)

    response = client.chat.completions.create(
        model="gemini-2.5-flash",  
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional web content summarizer. "
                    "Produce a clear, concise, factual summary."
                ),
            },
            {
                "role": "user",
                "content": f"Summarize the following content in under {max_words} words:\n\n{text}",
            },
        ],
        temperature=0.3,
    )

    return response.choices[0].message.content.strip()



if __name__ == "__main__":
    mcp.run(transport="sse")
