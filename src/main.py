#!/usr/bin/env python3
"""Main entry point for the MCP Jive Server.

This script provides the main entry point for running the MCP server,
handling command-line arguments, and managing the server lifecycle.
"""

import sys
import asyncio
import argparse
import logging
from pathlib import Path
from typing import Optional

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_server.server import MCPServer
from mcp_server.config import ServerConfig
from mcp_server.database import WeaviateManager
from mcp_server.health import HealthMonitor


def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stderr),
            logging.FileHandler("mcp-jive.log")
        ]
    )


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="MCP Jive Server - AI-powered task and workflow management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Run server with default settings
  %(prog)s --log-level DEBUG        # Run with debug logging
  %(prog)s --config custom.env      # Use custom configuration file
  %(prog)s --port 8080              # Run on custom port
  %(prog)s --host 0.0.0.0           # Bind to all interfaces

Environment Variables:
  MCP_SERVER_HOST                   # Server host (default: localhost)
  MCP_SERVER_PORT                   # Server port (default: 3000)
  MCP_LOG_LEVEL                     # Log level (default: INFO)
  WEAVIATE_HOST                     # Weaviate host (default: localhost)
  WEAVIATE_PORT                     # Weaviate port (default: 8080)
  ANTHROPIC_API_KEY                 # Anthropic API key
  OPENAI_API_KEY                    # OpenAI API key
  GOOGLE_API_KEY                    # Google API key
"""
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (.env format)"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        help="Server host address (default: from config or localhost)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        help="Server port number (default: from config or 3000)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--stdio",
        action="store_true",
        default=True,
        help="Run server in stdio mode (default: True)"
    )
    
    parser.add_argument(
        "--websocket",
        action="store_true",
        help="Run server in WebSocket mode"
    )
    
    parser.add_argument(
        "--http",
        action="store_true",
        help="Run server in HTTP mode"
    )
    
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Initialize the Weaviate database and exit"
    )
    
    parser.add_argument(
        "--health-check",
        action="store_true",
        help="Perform health check and exit"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="MCP Jive Server 1.0.0"
    )
    
    return parser.parse_args()


async def initialize_database(config: ServerConfig) -> bool:
    """Initialize the Weaviate database."""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Initializing Weaviate database...")
        weaviate_manager = WeaviateManager(config)
        
        # Start Weaviate (includes connection and schema initialization)
        await weaviate_manager.start()
        
        logger.info("Database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False
    finally:
        try:
            await weaviate_manager.stop()
        except:
            pass


async def perform_health_check(config: ServerConfig) -> bool:
    """Perform a comprehensive health check."""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Performing health check...")
        
        # Initialize components
        weaviate_manager = WeaviateManager(config)
        health_monitor = HealthMonitor(config, weaviate_manager)
        
        # Start Weaviate
        await weaviate_manager.start()
        
        # Perform health checks
        overall_health = await health_monitor.get_overall_health()
        system_health = await health_monitor.get_system_health()
        weaviate_health = await health_monitor.get_weaviate_health()
        
        # Print results
        print("\n=== MCP Jive Server Health Check ===")
        print(f"Overall Status: {overall_health.status}")
        print(f"Timestamp: {overall_health.timestamp}")
        
        print("\n--- System Health ---")
        print(f"CPU Usage: {system_health.cpu_usage:.1f}%")
        print(f"Memory Usage: {system_health.memory_usage:.1f}%")
        print(f"Disk Usage: {system_health.disk_usage:.1f}%")
        
        print("\n--- Weaviate Health ---")
        print(f"Status: {weaviate_health.status}")
        print(f"Connected: {weaviate_health.connected}")
        
        if overall_health.issues:
            print("\n--- Issues ---")
            for issue in overall_health.issues:
                print(f"- {issue}")
                
        success = overall_health.status == "healthy"
        print(f"\nHealth Check: {'PASSED' if success else 'FAILED'}")
        
        return success
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        print(f"\nHealth Check: FAILED - {e}")
        return False
    finally:
        try:
            await weaviate_manager.stop()
        except:
            pass


async def run_server(config: ServerConfig, transport_mode: str = "stdio") -> None:
    """Run the MCP server."""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Starting MCP Jive Server in {transport_mode} mode...")
        
        # Create server
        server = MCPServer(config)
        
        # Run server based on transport mode
        if transport_mode == "stdio":
            await server.run_stdio()
        elif transport_mode == "websocket":
            await server.run_websocket()
        elif transport_mode == "http":
            await server.run_http()
        else:
            raise ValueError(f"Unknown transport mode: {transport_mode}")
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    finally:
        try:
            await server.stop()
        except:
            pass


def main() -> None:
    """Main entry point."""
    # Parse arguments
    args = parse_arguments()
    
    # Load environment from config file if provided
    if args.config:
        from dotenv import load_dotenv
        load_dotenv(args.config)
    
    # Setup logging
    log_level = args.log_level or "INFO"
    setup_logging(log_level)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting MCP Jive Server...")
    
    try:
        # Load configuration
        config = ServerConfig()
        
        # Override config with command-line arguments
        if args.host:
            config.host = args.host
        if args.port:
            config.port = args.port
        if args.log_level:
            config.log_level = args.log_level
            
        # Handle special commands
        if args.init_db:
            success = asyncio.run(initialize_database(config))
            sys.exit(0 if success else 1)
            
        if args.health_check:
            success = asyncio.run(perform_health_check(config))
            sys.exit(0 if success else 1)
            
        # Determine transport mode
        transport_mode = "stdio"  # default
        if args.websocket:
            transport_mode = "websocket"
        elif args.http:
            transport_mode = "http"
            
        # Run the server
        asyncio.run(run_server(config, transport_mode))
        
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()