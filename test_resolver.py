import logging
import sys
import weaviate
import asyncio
from src.mcp_server.database import WeaviateManager
from src.mcp_server.config import ServerConfig
from src.mcp_server.utils.identifier_resolver import IdentifierResolver

logging.basicConfig(level=logging.DEBUG)

async def main():
    config = ServerConfig()
    manager = WeaviateManager(config)
    await manager.start()
    try:
        resolver = IdentifierResolver(manager)
        identifier = 'E-commerce Platform Modernization'
        result = await resolver.resolve_work_item_id(identifier)
        print(f'Resolved ID: {result}')
    finally:
        await manager.stop()

if __name__ == '__main__':
    asyncio.run(main())