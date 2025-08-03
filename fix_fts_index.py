#!/usr/bin/env python3
"""
Fix FTS Index Creation for Task Table

This script manually creates the FTS index for the Task table to enable full-text search.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from mcp_jive.lancedb_manager import LanceDBManager, DatabaseConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def fix_fts_index():
    """Create FTS index for Task table."""
    try:
        # Initialize LanceDB manager
        config = DatabaseConfig(
            data_path="./data/lancedb",
            embedding_model="all-MiniLM-L6-v2",
            enable_fts=True
        )
        
        db_manager = LanceDBManager(config)
        await db_manager.initialize()
        
        logger.info("🔍 Checking Task table...")
        
        # Get Task table
        table = db_manager.get_table("Task")
        row_count = table.count_rows()
        
        logger.info(f"📊 Task table has {row_count} rows")
        
        if row_count > 0:
            logger.info("🔧 Creating FTS index for Task table...")
            
            # Create FTS index
            text_fields = ['title', 'description', 'status', 'priority']
            
            try:
                table.create_fts_index(
                    text_fields,
                    replace=True,  # Replace if exists
                    use_tantivy=True,  # Use modern Tantivy implementation
                    with_position=True,  # Enable phrase queries
                    base_tokenizer="simple",  # Split by whitespace and punctuation
                    language="English",
                    lower_case=True,  # Case-insensitive search
                    stem=True,  # Enable stemming
                    remove_stop_words=True,  # Remove common words
                    ascii_folding=True  # Handle accented characters
                )
                logger.info(f"✅ Successfully created FTS index for Task table fields: {text_fields}")
                
                # Test the FTS index
                logger.info("🧪 Testing FTS index...")
                test_results = table.search("authentication", query_type="fts").limit(5).to_pandas()
                logger.info(f"✅ FTS test successful - found {len(test_results)} results")
                
            except Exception as e:
                logger.error(f"❌ Failed to create FTS index: {e}")
                return False
                
        else:
            logger.warning("⚠️ Task table is empty - no FTS index needed")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Error fixing FTS index: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(fix_fts_index())
    if success:
        print("\n✅ FTS index fix completed successfully!")
        print("🔄 Please restart the MCP server to ensure changes take effect.")
    else:
        print("\n❌ FTS index fix failed!")
        sys.exit(1)