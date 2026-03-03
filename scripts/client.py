import asyncio
from fastmcp import Client

async def main():
    client = Client("https://price.solufuse.com/mcp")
    async with client:
        result = await client.call_tool(
            "simulate_binary_contract",
            {"S0": 195, "K": 200, "mu": 0.08, "sigma": 0.20, "T": 30 / 365},
        )
        print(result)

if __name__ == "__main__":
    asyncio.run(main())
