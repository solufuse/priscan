# Deploying a FastMCP Simulation Server to Dokploy

This document provides the code and instructions to deploy a `FastMCP` server that exposes a financial simulation as a tool. The application is containerized with Docker for easy deployment on Dokploy.

## Application Files

Here are the files that make up the application:

### `simulations.py`

This file contains the Python code for the financial simulations.

```python
import numpy as np
from scipy.special import expit, logit
from scipy.stats import norm, t as t_dist
from collections import deque

# ... (simulation functions from the document) ...
```

### `app.py`

This is the main application file. It uses `FastMCP` to create a server and exposes the `simulate_binary_contract` function as a callable tool.

```python
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
    mcp.run(transport="http", port=8000)
```

### `client.py`

This script provides an example of how to connect to and interact with the deployed `FastMCP` server.

```python
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
```

### `requirements.txt`

This file lists the Python libraries that the application depends on.

```
numpy
scipy
fastmcp
```

### `Dockerfile`

This file contains the instructions for Docker to build a container image for the application. It sets up the Python environment, installs dependencies, and runs the `FastMCP` server on port 8000.

```dockerfile
# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the FastMCP server
CMD ["python", "app.py"]
```

## Deployment Instructions

### Step 1: Push Project to GitHub

Push all the created files (`simulations.py`, `app.py`, `client.py`, `requirements.txt`, and `Dockerfile`) to a GitHub repository.

```bash
git init
git add .
git commit -m "Refactor to FastMCP server"
git branch -M main
git remote add origin <YOUR_GITHUB_REPOSITORY_URL> # Replace with your repo URL
git push -u origin main
```

### Step 2: Deploy on Dokploy

1.  **Create a new application in Dokploy** and give it a name.
2.  **Select your GitHub Repository** and the `main` branch.
3.  **Configure the Build Settings:**
    *   Select the **"Use Dockerfile"** option. Dokploy will automatically detect it.
4.  **Configure Network Settings:**
    *   Dokploy will read the `EXPOSE 8000` command from your `Dockerfile`.
    *   Ensure it maps an external port (like 80 or 443) to the container's internal port **8000**.
    *   **IMPORTANT**: You must also configure your custom domain (`price.solufuse.com`) in Dokploy to point to this application.
5.  **Deploy** the application.

## How to Use the Deployed Server

1.  Once deployed and your domain (`price.solufuse.com`) is correctly configured in Dokploy, you can run the `client.py` script.
2.  The script is already configured to connect to `https://price.solufuse.com/mcp`.
3.  Run the client from your terminal:
    ```bash
    python client.py
    ```
    You should see the simulation results.
