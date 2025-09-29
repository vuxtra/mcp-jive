# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - $(date +%Y-%m-%d)

📝 Add E2E test runner, bug fix test runner, and configuration validation tool
✨ feat: implement automated release process with semantic versioning
✨ feat(tools): update documentation to reflect addition of jive_reorder_work_items and total of 8 consolidated tools
✨ feat(namespace): enhance namespace handling across components and API interactions
✨ feat(workitems): add simple work items tab component and improve API handling
🔧 refactor(workitems): move namespace handling to component level to avoid circular dependency
✨ feat: update work items handling and UI improvements
✨ feat(namespace): add multi-tenant namespace support for data isolation
🐛 fix(api): correct response data field name from 'data' to 'result'
✨ feat(server): add WebSocket support and improve MCP protocol handling
✨ feat(server): add WebSocket support for real-time updates and event broadcasting
✨ feat(server): change default transport mode to combined
✨ feat(work-items): add real-time updates and improved reordering
🔧 style(ui): adjust layout spacing and height in tab components
✨ feat(websocket): implement robust WebSocket connection handling and debug tools
✨ feat: add dark mode support and improve WebSocket handling
🔧 refactor(frontend): remove timeline tab and improve work items table layout
✨ feat(analytics): enhance analytics tab with detailed metrics and predictions
✨ feat(search): improve search functionality and progress calculation
🔧 refactor(tools): remove tool mode configuration and consolidate to unified tools
✨ feat(work-items): implement hierarchical ordering and drag-and-drop reordering
✨ feat: initialize frontend with Next.js and Material-UI
🔧 refactor(scripts): remove unused scripts and cleanup env variables
✨ feat: implement consolidated CLI and tool configuration system
🐛 fix(execution_planner): handle numpy array in success criteria check
🐛 fix(planning): handle missing constraints attribute in ai_guidance_generator
✨ feat(execution_planner): add safe attribute access for execution_environment
✨ feat(planning): add planning module with execution guidance and prompt templates
✨ feat: add unified mcp-server.py entry point and refactor work item access
🔧 refactor(tools): consolidate tools and remove AI dependencies
✨ feat: implement consolidated tools and remove AI dependencies
✨ feat(tools): implement consolidated tools and backward compatibility
✨ feat: consolidate MCP Jive and MCP Server into unified system
✨ feat(server): improve stdio server shutdown handling
🔧 refactor: migrate mcp_server to mcp_jive and update imports
🔧 refactor(database): migrate lancedb_manager to mcp_jive module and update imports
🐛 fix(lancedb): add safe comparison for numpy arrays in conflict detection
🔧 refactor(database): migrate from Weaviate to LanceDB as primary database
🔧 refactor(database): migrate from Weaviate to LanceDB for vector storage
✨ feat(identifier): add flexible work item identifier resolution
📝 Document WEAVIATE_DATA_PATH configuration option
📝 Remove remaining src/data files from git tracking
📝 Clean up Weaviate data folder structure
✨ feat: add HTTP mode and stdio support to dev server
✨ feat: update Weaviate schema and configuration for v4 compatibility
✨ feat(ai-orchestration): implement rate limiting and MCP tools for AI orchestration
✨ feat(task-storage): implement task storage and sync system
✨ feat: initialize core infrastructure and implement MCP tools
🔧 docs: update PRDs with security boundaries and tool refinements
✨ feat: add initial project structure and PRD documents

