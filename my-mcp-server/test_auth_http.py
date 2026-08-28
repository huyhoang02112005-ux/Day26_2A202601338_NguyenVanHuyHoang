import httpx
import asyncio

SERVER_URL = "http://localhost:8085/mcp"
VALID_TOKEN = "secret-token-123"
INVALID_TOKEN = "wrong-token-999"

async def test_auth():
    print("=== Testing MCP Authentication over Streamable HTTP ===")
    
    # 1. No Token
    async with httpx.AsyncClient() as client:
        print("\n[Case 1] Request without Authorization Header:")
        try:
            res = await client.post(SERVER_URL, json={"jsonrpc": "2.0", "method": "initialize", "id": 1})
            print(f"Status Code: {res.status_code}")
            print(f"Response: {res.text[:150]}")
        except Exception as e:
            print(f"Error: {e}")

    # 2. Invalid Token
    async with httpx.AsyncClient() as client:
        print("\n[Case 2] Request with INVALID Token:")
        try:
            headers = {"Authorization": f"Bearer {INVALID_TOKEN}"}
            res = await client.post(SERVER_URL, headers=headers, json={"jsonrpc": "2.0", "method": "initialize", "id": 1})
            print(f"Status Code: {res.status_code}")
            print(f"Response: {res.text[:150]}")
        except Exception as e:
            print(f"Error: {e}")

    # 3. Valid Token
    async with httpx.AsyncClient() as client:
        print("\n[Case 3] Request with VALID Token:")
        try:
            headers = {"Authorization": f"Bearer {VALID_TOKEN}"}
            res = await client.post(SERVER_URL, headers=headers, json={"jsonrpc": "2.0", "method": "initialize", "id": 1})
            print(f"Status Code: {res.status_code}")
            print(f"Response: {res.text[:150]}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    print("Vui lòng khởi chạy server ở chế độ HTTP trước:")
    print("  TRANSPORT=streamable-http python server.py")
    print("Sau đó chạy file này để test auth.\n")
