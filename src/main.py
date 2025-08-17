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

from mcp_jive.server import MCPServer
from mcp_jive.config import Config, ServerConfig
from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig
from mcp_jive.health import HealthMonitor


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
  MCP_SERVER_PORT                   # Server port (default: 3456)
  MCP_LOG_LEVEL                     # Log level (default: INFO)
  # LanceDB configuration
  LANCEDB_DATA_PATH                 # LanceDB data directory (default: ./data/lancedb_jive)
  LANCEDB_EMBEDDING_MODEL           # Embedding model (default: all-MiniLM-L6-v2)
  # AI API keys removed
"""
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (.env format)"
    )
    
    parser.add_argument(
        "--db-path",
        type=str,
        help="Path to LanceDB database directory (overrides LANCEDB_DATA_PATH)"
    )
    
    parser.add_argument(
        "--host",
        type=str,
        help="Server host address (default: from config or localhost)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        help="Server port number (default: from config or 3456)"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level (default: INFO)"
    )
    
    # Transport mode arguments (mutually exclusive)
    transport_group = parser.add_mutually_exclusive_group()
    transport_group.add_argument(
        "--stdio",
        action="store_true",
        help="Run server in stdio mode (default: True)"
    )
    
    transport_group.add_argument(
        "--websocket",
        action="store_true",
        help="Run server in WebSocket mode"
    )
    
    transport_group.add_argument(
        "--http",
        action="store_true",
        help="Run server in HTTP mode"
    )
    
    transport_group.add_argument(
        "--combined",
        action="store_true",
        help="Run in combined mode (stdio + http + websocket)"
    )
    
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Initialize the database and exit"
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
    """Initialize the LanceDB database."""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Initializing LanceDB database...")
        
        # Create LanceDB configuration
        db_config = DatabaseConfig(
            data_path=getattr(config, 'lancedb_data_path', './data/lancedb_jive'),
            embedding_model=getattr(config, 'lancedb_embedding_model', 'all-MiniLM-L6-v2'),
            device=getattr(config, 'lancedb_device', 'cpu')
        )
        
        lancedb_manager = LanceDBManager(db_config)
        
        # Initialize LanceDB (includes connection and schema setup)
        await lancedb_manager.initialize()
        
        logger.info("Database initialization completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False
    finally:
        try:
            await lancedb_manager.cleanup()
        except:
            pass


async def perform_health_check(config: ServerConfig) -> bool:
    """Perform a comprehensive health check."""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Performing health check...")
        
        # Create LanceDB configuration
        db_config = DatabaseConfig(
            data_path=getattr(config, 'lancedb_data_path', './data/lancedb_jive'),
            embedding_model=getattr(config, 'lancedb_embedding_model', 'all-MiniLM-L6-v2'),
            device=getattr(config, 'lancedb_device', 'cpu'),
            enable_fts=True
        )
        
        # Initialize components
        lancedb_manager = LanceDBManager(db_config)
        health_monitor = HealthMonitor(config, lancedb_manager)
        
        # Initialize LanceDB
        await lancedb_manager.initialize()
        
        # Perform health checks
        overall_health_dict = await health_monitor.get_overall_health()
        
        # Print results
        print("\n=== MCP Jive Server Health Check ===")
        print(f"Overall Status: {overall_health_dict.get('status', 'unknown')}")
        print(f"Timestamp: {overall_health_dict.get('timestamp', 'unknown')}")
        
        # Extract component details if available
        components = overall_health_dict.get('details', {}).get('components', [])
        
        for component in components:
            component_name = component.get('component', 'unknown')
            component_status = component.get('status', 'unknown')
            component_message = component.get('message', '')
            
            print(f"\n--- {component_name.title()} ---")
            print(f"Status: {component_status}")
            if component_message:
                print(f"Message: {component_message}")
            
            # Print component details if available
            if 'details' in component:
                details = component['details']
                for key, value in details.items():
                    if isinstance(value, (int, float)):
                        print(f"{key.replace('_', ' ').title()}: {value}")
        
        # Print any issues
        if overall_health_dict.get('message'):
            print(f"\nMessage: {overall_health_dict['message']}")
                
        success = overall_health_dict.get('status') == "healthy"
        print(f"\nHealth Check: {'PASSED' if success else 'FAILED'}")
        
        return success
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        print(f"\nHealth Check: FAILED - {e}")
        return False
    finally:
        # Legacy cleanup - now handled by LanceDB
        pass


async def run_server(config: ServerConfig, full_config: Config, transport_mode: str = "stdio") -> None:
    """Run the MCP server."""
    logger = logging.getLogger(__name__)
    
    try:
        logger.info(f"Starting MCP Jive Server in {transport_mode} mode...")
        
        # Create server
        server = MCPServer(
            config=full_config
        )
        
        # Run server based on transport mode
        if transport_mode == "stdio":
            await server.run_stdio()
        elif transport_mode == "websocket":
            await server.run_websocket()
        elif transport_mode == "http":
            await server.run_http()
        elif transport_mode == "combined":
            await server.run_combined()
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
    
    # Set database path if provided
    if args.db_path:
        import os
        os.environ['LANCEDB_DATA_PATH'] = args.db_path
        logger.info(f"Using custom database path: {args.db_path}")
    logger.info("Starting MCP Jive Server...")
    
    try:
        # Load configuration
        full_config = Config()
        config = full_config.server
        
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
        elif args.combined:
            transport_mode = "combined"
            
        # Run the server
        asyncio.run(run_server(config, full_config, transport_mode))
        
    except KeyboardInterrupt:
        logger.info("Shutdown requested by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()