from fastapi import FastAPI, Request
from sse_starlette.sse import EventSourceResponse
import asyncio
import json

app = FastAPI()


clients = []

@app.post("/mcp")
async def mcp_post(request: Request):
    body = await request.json()

    method = body.get("method")
    params = body.get("params")

    
    if method == "say_hello":
        result = f"Hello {params.get('name')}"

        
        for queue in clients:
            await queue.put(result)

        return {
            "id": body.get("id"),
            "result": "Accepted"
        }

    return {"error": "Unknown method"}

@app.get("/mcp")
async def mcp_stream():
    queue = asyncio.Queue()
    clients.append(queue)

    async def event_generator():
        try:
            while True:
                message = await queue.get()
                yield {
                    "event": "message",
                    "data": json.dumps({
                        "method": "server_message",
                        "params": message
                    })
                }
        except asyncio.CancelledError:
            return
        finally:
            clients.remove(queue)

    return EventSourceResponse(event_generator())



if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
