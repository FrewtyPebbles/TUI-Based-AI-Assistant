import json
from typing import Optional
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import StreamingResponse
from ollama import AsyncClient

app = FastAPI(title="Ollama API Server")

client = AsyncClient(host="http://localhost:11434")


async def stream_generate(
    model: str = None,
    prompt: str = None,
    tools: Optional[list] = None,
    options: Optional[dict] = None,
    system: Optional[str] = None,
    suffix: Optional[str] = None,
    images: Optional[list] = None,
):
    if not prompt:
        raise ValueError("Prompt is required")

    async with client.generate(
        model=model or "mistral",
        prompt=prompt,
        stream=True,
        tools=tools,
        options=options or {},
        system=system,
        suffix=suffix,
        images=images,
    ) as response:
        async for line in response:
            if line.get("done"):
                continue
            message = line.get("message", {})
            content = message.get("content", "")
            reasoning = message.get("context", {}).get("thinking", "")
            result = {
                "model": line.get("model"),
                "done": line.get("done"),
                "message": {
                    "role": message.get("role"),
                    "content": content,
                    "context": message.get("context"),
                },
                "created_at": line.get("created_at"),
            }
            if reasoning:
                result["message"]["context"]["thinking"] = reasoning
            yield f"data: {result}\n\n"


async def stream_chat(
    model: str = None,
    messages: list = None,
    tools: Optional[list] = None,
    keep_alive: Optional[str] = None,
):
    if not messages:
        raise ValueError("Messages are required")

    async with client.chat(
        model=model or "mistral",
        messages=messages,
        stream=True,
        tools=tools,
        keep_alive=keep_alive,
    ) as response:
        async for line in response:
            yield f"data: {json.dumps(line)}\n\n"


@app.websocket("/chat/stream")
async def chat_websocket(
    websocket: WebSocket,
    model: Optional[str] = None,
    messages: Optional[list] = None,
    tools: Optional[list] = None,
    options: Optional[dict] = None,
    keep_alive: Optional[str] = None,
):
    await websocket.accept()

    async def iterator():
        try:
            async with client.chat(
                model=model or "mistral",
                messages=messages or [],
                stream=True,
                tools=tools,
                keep_alive=keep_alive,
            ) as response:
                async for line in response:
                    yield f"data: {json.dumps(line)}\n\n"
        except Exception:
            pass

    async for chunk in iterator():
        await websocket.send_text(chunk)


@app.websocket("/generate/stream")
async def generate_websocket(
    websocket: WebSocket,
    model: Optional[str] = None,
    prompt: Optional[str] = None,
    tools: Optional[list] = None,
    options: Optional[dict] = None,
    system: Optional[str] = None,
    suffix: Optional[str] = None,
    images: Optional[list] = None,
):
    await websocket.accept()

    async def iterator():
        async for line in stream_generate(
            model=model,
            prompt=prompt,
            tools=tools,
            options=options,
            system=system,
            suffix=suffix,
            images=images,
        ):
            yield line

    async for chunk in iterator():
        await websocket.send_text(chunk)


@app.get("/generate/stream")
async def generate_stream_http(
    model: Optional[str] = None,
    prompt: Optional[str] = None,
    tools: Optional[list] = None,
    options: Optional[dict] = None,
    system: Optional[str] = None,
    suffix: Optional[str] = None,
    images: Optional[list] = None,
):
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")

    async def generate():
        async for line in stream_generate(
            model=model,
            prompt=prompt,
            tools=tools,
            options=options,
            system=system,
            suffix=suffix,
            images=images,
        ):
            yield line

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/generate")
async def generate(
    model: Optional[str] = None,
    prompt: Optional[str] = None,
    tools: Optional[list] = None,
    options: Optional[dict] = None,
    system: Optional[str] = None,
    suffix: Optional[str] = None,
    images: Optional[list] = None,
):
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt is required")

    response = await client.generate(
        model=model or "mistral",
        prompt=prompt,
        stream=False,
        tools=tools,
        options=options or {},
        system=system,
        suffix=suffix,
        images=images,
    )

    result = {
        "model": response.get("model"),
        "response": response.get("response", {}).get("content", ""),
        "done": response.get("done"),
        "created_at": response.get("created_at"),
        "context": response.get("context"),
    }

    return {"model": result["model"], **result}


@app.post("/chat/stream")
async def chat_stream_endpoint(
    model: Optional[str] = None,
    messages: Optional[list] = None,
    tools: Optional[list] = None,
    options: Optional[dict] = None,
    keep_alive: Optional[str] = None,
):
    if not messages:
        raise HTTPException(status_code=400, detail="Messages are required")

    async def chat():
        async with client.chat(
            model=model or "mistral",
            messages=messages,
            stream=True,
            tools=tools,
            keep_alive=keep_alive,
        ) as response:
            async for line in response:
                yield line

    return StreamingResponse(chat(), media_type="text/event-stream")


@app.post("/chat")
async def chat(
    model: Optional[str] = None,
    messages: Optional[list] = None,
    tools: Optional[list] = None,
    options: Optional[dict] = None,
    keep_alive: Optional[str] = None,
):
    if not messages:
        raise HTTPException(status_code=400, detail="Messages are required")

    response = await client.chat(
        model=model or "mistral",
        messages=messages,
        stream=False,
        tools=tools,
        options=options or {},
        keep_alive=keep_alive,
    )

    result = {
        "model": response.get("model"),
        "message": {
            "role": response.get("message", {}).get("role"),
            "content": response.get("message", {}).get("content", ""),
        },
        "done": response.get("done"),
        "created_at": response.get("created_at"),
        "context": response.get("context"),
        "total_duration": response.get("total_duration"),
        "load_duration": response.get("load_duration"),
        "prompt_eval_count": response.get("prompt_eval_count"),
        "prompt_eval_duration": response.get("prompt_eval_duration"),
        "eval_count": response.get("eval_count"),
        "eval_duration": response.get("eval_duration"),
    }

    return result


@app.get("/health")
async def health():
    return {"status": "ok"}
