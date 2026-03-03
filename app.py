from fastmcp import FastMCP
import simulations

mcp = FastMCP("Simulation Server")

@mcp.tool
def simulate_binary_contract(S0: float, K: float, mu: float, sigma: float, T: float) -> dict:
    """
    Monte Carlo simulation for a binary contract.

    Args:
        S0: Current asset price
        K: Strike / threshold
        mu: Annual drift
        sigma: Annual volatility
        T: Time to expiry in years
    """
    return simulations.simulate_binary_contract(S0, K, mu, sigma, T)

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=8000)
