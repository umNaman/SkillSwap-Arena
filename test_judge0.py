import asyncio, httpx, base64

async def main():
    source = "print('hello')"
    b64_source = base64.b64encode(source.encode()).decode()
    payload = {"source_code": b64_source, "language_id": 71, "stdin": ""}
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post("https://ce.judge0.com/submissions?base64_encoded=true&wait=true", json=payload)
            print(resp.status_code)
            print(resp.text)
        except Exception as e:
            print("ERROR", e)

asyncio.run(main())
