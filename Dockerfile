FROM python:3.9-slim

WORKDIR /app

# Copy project files
COPY . .

# Install as a package
RUN pip install --no-cache-dir .

# Server uses stdio transport (stdin/stdout for MCP protocol)
CMD ["mcp-server-zep-cloud"]
