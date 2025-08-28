#!/usr/bin/env python3
"""
Environment Variables Cleanup Script
Safely removes unused environment variables from .env files in phases.
"""

import os
import shutil
from datetime import datetime
from typing import List, Set

# Define cleanup phases with risk levels
CLEANUP_PHASES = {
    "phase1_safe": {
        "description": "Safe removals - clearly unused AI and database providers",
        "risk": "LOW",
        "variables": [
            # Unused AI providers (if not using these)
            "GOOGLE_MODEL", "GOOGLE_TEMPERATURE", "GOOGLE_MAX_TOKENS",
            
            # Unused database providers (if only using LanceDB)
            "PINECONE_API_KEY", "PINECONE_ENVIRONMENT", "PINECONE_INDEX_NAME",
            "CHROMA_HOST", "CHROMA_PORT", "CHROMA_COLLECTION_NAME", "CHROMA_TIMEOUT",
            
            # Unused feature flags for unimplemented features
            "FEATURE_AUTO_EMBEDDING", "FEATURE_BATCH_OPERATIONS",
            "FEATURE_HYBRID_SEARCH", "FEATURE_REAL_TIME_SYNC",
            "FEATURE_SEMANTIC_SIMILARITY", "FEATURE_VECTOR_SEARCH",
        ]
    },
    "phase2_medium": {
        "description": "Medium risk - development and server configuration",
        "risk": "MEDIUM",
        "variables": [
            # Development tools (verify team workflow first)
            "COVERAGE_ENABLED", "COVERAGE_THRESHOLD",
            "LINTING_ENABLED", "FORMATTING_ENABLED",
            "TYPE_CHECKING_ENABLED",
            
            # Server configuration (verify deployment needs)
            "UVICORN_HOST", "UVICORN_PORT", "UVICORN_WORKERS", "UVICORN_LOG_LEVEL", "UVICORN_RELOAD", "UVICORN_ACCESS_LOG",
            "SERVER_HOST", "SERVER_PORT", "SERVER_WORKERS", "SERVER_LOG_LEVEL", "SERVER_RELOAD",
            
            # Unused OpenAI variables (if not using OpenAI)
            "OPENAI_MODEL", "OPENAI_TEMPERATURE", "OPENAI_MAX_TOKENS",
        ]
    },
    "phase3_careful": {
        "description": "Careful review needed - potential future use",
        "risk": "MEDIUM-HIGH",
        "variables": [
            # Backup and monitoring (might be used in production)
            "BACKUP_COMPRESSION", "BACKUP_INTERVAL", "BACKUP_RETENTION_DAYS",
            "METRICS_ENABLED", "METRICS_PATH", "METRICS_PORT",
            "HEALTH_CHECK_ENABLED", "HEALTH_CHECK_INTERVAL", "HEALTH_CHECK_PATH",
            
            # Cache configuration
            "CACHE_ENABLED", "CACHE_MAX_SIZE", "CACHE_CLEANUP_INTERVAL",
            
            # Migration tools
            "MIGRATION_BACKUP_PATH", "MIGRATION_BATCH_SIZE", "MIGRATION_LOG_PROGRESS",
            "MIGRATION_PARALLEL_WORKERS", "MIGRATION_RETRY_FAILED",
        ]
    }
}

# Variables that should definitely be kept (used in codebase)
KEEP_VARIABLES = {
    # Core MCP Jive configuration
    "MCP_JIVE_HOST", "MCP_JIVE_PORT", "MCP_JIVE_DEBUG", "MCP_JIVE_LOG_LEVEL",
    "MCP_JIVE_AUTO_RELOAD", "MCP_JIVE_SHOW_CONSOLIDATION_INFO",
    
    # MCP Jive configuration limits (used in tool_config.py)
    "MCP_ENVIRONMENT", "MCP_JIVE_ACCEPTANCE_CRITERIA_MAX",
    "MCP_JIVE_CONTEXT_TAGS_MAX", "MCP_JIVE_DESCRIPTION_MAX_LENGTH",
    "MCP_JIVE_ENABLE_AUTO_TRUNCATION", "MCP_JIVE_EXECUTION_TIMEOUT",
    "MCP_JIVE_MAX_PARALLEL_EXECUTIONS", "MCP_JIVE_MAX_RESPONSE_SIZE",
    "MCP_JIVE_NOTES_MAX_LENGTH", "MCP_JIVE_TRUNCATION_THRESHOLD",
    
    # Security and CORS
    "SECRET_KEY", "ENABLE_AUTH", "CORS_ENABLED", "CORS_ORIGINS",
    "RATE_LIMIT_ENABLED", "MAX_REQUESTS_PER_MINUTE",
    
    # Database configuration
    "LANCEDB_USE_EMBEDDED", "LANCEDB_HOST", "LANCEDB_PORT", "LANCEDB_TIMEOUT",
    "LANCEDB_PERSISTENCE_PATH", "LANCEDB_BACKUP_ENABLED", "LANCEDB_DATA_PATH",
    "LANCEDB_EMBEDDING_MODEL", "LANCEDB_DEVICE",
    
    # Performance
    "MAX_WORKERS", "REQUEST_TIMEOUT", "CONNECTION_TIMEOUT",
    "ENABLE_METRICS", "ENABLE_HEALTH_CHECKS", "ENABLE_PROFILING",
    
    # Tools configuration
    "ENABLE_TASK_MANAGEMENT", "ENABLE_WORKFLOW_EXECUTION",
    "ENABLE_SEARCH_TOOLS", "ENABLE_VALIDATION_TOOLS", "ENABLE_SYNC_TOOLS",
    "MAX_TASK_DEPTH", "AUTO_DEPENDENCY_VALIDATION",
    "SEARCH_RESULT_LIMIT", "SEMANTIC_SEARCH_THRESHOLD",
    
    # Tool configuration
    "MCP_JIVE_CACHE_TTL", "MCP_JIVE_MAX_CONCURRENT",
    "MCP_JIVE_AI_ORCHESTRATION", "MCP_JIVE_QUALITY_GATES",
    
    # Tool configuration - additional variables found in tool_config.py
    "MCP_JIVE_TOOL_CACHING",
    "MCP_JIVE_MIGRATION_MODE", "MCP_JIVE_MIGRATION_LOG", "MCP_JIVE_MIGRATION_DRY_RUN",
    "MCP_JIVE_ADVANCED_ANALYTICS", "MCP_JIVE_WORKFLOW_ORCHESTRATION",
    
    # Development
    "ENABLE_HOT_RELOAD", "ENABLE_DEBUG_LOGGING", "TEST_MODE",
    "MOCK_AI_RESPONSES", "ENABLE_TYPE_CHECKING", "ENABLE_LINTING",
}

def backup_file(file_path: str) -> str:
    """Create a backup of the file with timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{file_path}.backup_{timestamp}"
    shutil.copy2(file_path, backup_path)
    return backup_path

def read_env_file(file_path: str) -> List[str]:
    """Read env file and return lines."""
    try:
        with open(file_path, 'r') as f:
            return f.readlines()
    except FileNotFoundError:
        print(f"Warning: {file_path} not found")
        return []

def write_env_file(file_path: str, lines: List[str]):
    """Write lines to env file."""
    with open(file_path, 'w') as f:
        f.writelines(lines)

def remove_variables_from_lines(lines: List[str], variables_to_remove: Set[str]) -> tuple[List[str], List[str]]:
    """Remove specified variables from env file lines."""
    new_lines = []
    removed_variables = []
    
    for line in lines:
        line_stripped = line.strip()
        
        # Skip empty lines and comments
        if not line_stripped or line_stripped.startswith('#'):
            new_lines.append(line)
            continue
        
        # Check if this line defines a variable to remove
        if '=' in line_stripped:
            var_name = line_stripped.split('=')[0].strip()
            if var_name in variables_to_remove:
                # Add comment indicating removal
                new_lines.append(f"# REMOVED: {line}")
                removed_variables.append(var_name)
                continue
        
        new_lines.append(line)
    
    return new_lines, removed_variables

def cleanup_phase(phase_name: str, files_to_clean: List[str], dry_run: bool = True):
    """Execute a cleanup phase."""
    phase_info = CLEANUP_PHASES[phase_name]
    variables_to_remove = set(phase_info["variables"])
    
    print(f"\n=== {phase_name.upper()} ===")
    print(f"Description: {phase_info['description']}")
    print(f"Risk Level: {phase_info['risk']}")
    print(f"Variables to remove: {len(variables_to_remove)}")
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No files will be modified")
    else:
        print("\n⚠️  LIVE MODE - Files will be modified")
    
    total_removed = 0
    
    for file_path in files_to_clean:
        if not os.path.exists(file_path):
            print(f"\nSkipping {file_path} (not found)")
            continue
        
        print(f"\nProcessing {file_path}...")
        
        # Read current file
        lines = read_env_file(file_path)
        if not lines:
            continue
        
        # Remove variables
        new_lines, removed_vars = remove_variables_from_lines(lines, variables_to_remove)
        
        if removed_vars:
            print(f"  Variables to remove: {', '.join(removed_vars)}")
            total_removed += len(removed_vars)
            
            if not dry_run:
                # Create backup
                backup_path = backup_file(file_path)
                print(f"  Backup created: {backup_path}")
                
                # Write updated file
                write_env_file(file_path, new_lines)
                print(f"  ✅ Updated {file_path}")
            else:
                print(f"  🔍 Would remove {len(removed_vars)} variables")
        else:
            print(f"  No variables to remove from this file")
    
    print(f"\nPhase summary: {total_removed} variables processed")
    return total_removed

def add_missing_variables(files_to_update: List[str], dry_run: bool = True):
    """Add variables that are used in code but missing from .env files."""
    missing_vars = {
        "MCP_JIVE_MIGRATION_LOG": "logs/migration.log"
    }
    
    print(f"\n=== ADDING MISSING VARIABLES ===")
    print(f"Variables to add: {len(missing_vars)}")
    
    if dry_run:
        print("\n🔍 DRY RUN MODE - No files will be modified")
    else:
        print("\n⚠️  LIVE MODE - Files will be modified")
    
    for file_path in files_to_update:
        if not os.path.exists(file_path):
            print(f"\nSkipping {file_path} (not found)")
            continue
        
        print(f"\nProcessing {file_path}...")
        
        lines = read_env_file(file_path)
        if not lines:
            continue
        
        # Check which variables are missing
        existing_vars = set()
        for line in lines:
            line_stripped = line.strip()
            if line_stripped and not line_stripped.startswith('#') and '=' in line_stripped:
                var_name = line_stripped.split('=')[0].strip()
                existing_vars.add(var_name)
        
        vars_to_add = []
        for var_name, var_value in missing_vars.items():
            if var_name not in existing_vars:
                vars_to_add.append((var_name, var_value))
        
        if vars_to_add:
            print(f"  Variables to add: {', '.join([v[0] for v in vars_to_add])}")
            
            if not dry_run:
                # Create backup
                backup_path = backup_file(file_path)
                print(f"  Backup created: {backup_path}")
                
                # Add variables at the end
                new_lines = lines.copy()
                new_lines.append("\n# Added missing variables\n")
                for var_name, var_value in vars_to_add:
                    new_lines.append(f"{var_name}={var_value}\n")
                
                write_env_file(file_path, new_lines)
                print(f"  ✅ Updated {file_path}")
            else:
                print(f"  🔍 Would add {len(vars_to_add)} variables")
        else:
            print(f"  No missing variables to add")

def main():
    """Main cleanup function."""
    print("Environment Variables Cleanup Script")
    print("====================================")
    
    files_to_clean = [".env.example", ".env.dev"]
    
    # Check if files exist
    existing_files = [f for f in files_to_clean if os.path.exists(f)]
    if not existing_files:
        print("Error: No .env files found to clean")
        return
    
    print(f"Files to process: {', '.join(existing_files)}")
    
    # Ask for mode
    mode = input("\nRun in dry-run mode? (y/n, default=y): ").strip().lower()
    dry_run = mode != 'n'
    
    if dry_run:
        print("\n🔍 Running in DRY RUN mode - no files will be modified")
    else:
        print("\n⚠️  Running in LIVE mode - files will be modified")
        confirm = input("Are you sure? (yes/no): ").strip().lower()
        if confirm != 'yes':
            print("Cancelled.")
            return
    
    # Ask which phase to run
    print("\nAvailable cleanup phases:")
    for i, (phase_name, phase_info) in enumerate(CLEANUP_PHASES.items(), 1):
        print(f"{i}. {phase_name}: {phase_info['description']} (Risk: {phase_info['risk']})")
    print(f"{len(CLEANUP_PHASES) + 1}. all: Run all phases")
    print(f"{len(CLEANUP_PHASES) + 2}. add_missing: Add missing variables only")
    
    choice = input(f"\nSelect phase (1-{len(CLEANUP_PHASES) + 2}, default=1): ").strip()
    
    if choice == str(len(CLEANUP_PHASES) + 2) or choice.lower() == 'add_missing':
        # Add missing variables only
        add_missing_variables(existing_files, dry_run)
    elif choice == str(len(CLEANUP_PHASES) + 1) or choice.lower() == 'all':
        # Run all phases
        total_removed = 0
        for phase_name in CLEANUP_PHASES.keys():
            removed = cleanup_phase(phase_name, existing_files, dry_run)
            total_removed += removed
        
        print(f"\n=== TOTAL SUMMARY ===")
        print(f"Total variables processed: {total_removed}")
        
        # Also add missing variables
        add_missing_variables(existing_files, dry_run)
    else:
        # Run specific phase
        try:
            phase_index = int(choice) - 1 if choice else 0
            phase_names = list(CLEANUP_PHASES.keys())
            if 0 <= phase_index < len(phase_names):
                phase_name = phase_names[phase_index]
                cleanup_phase(phase_name, existing_files, dry_run)
            else:
                print("Invalid choice, running phase 1")
                cleanup_phase("phase1_safe", existing_files, dry_run)
        except ValueError:
            print("Invalid choice, running phase 1")
            cleanup_phase("phase1_safe", existing_files, dry_run)
    
    if dry_run:
        print("\n🔍 Dry run completed. Run with 'n' to make actual changes.")
    else:
        print("\n✅ Cleanup completed. Check the backup files if you need to restore.")

if __name__ == "__main__":
    main()