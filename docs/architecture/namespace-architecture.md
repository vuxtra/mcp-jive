# Namespace Architecture for MCP-Jive Server

**Status**: 📋 DRAFT | **Priority**: High | **Last Updated**: 2025-01-13
**Assigned Team**: AI Agent | **Progress**: 0%
**Dependencies**: 0 Blocking | 0 Related

## Status History
| Date | Status | Updated By | Notes |
|------|--------|------------|-------|
| 2025-01-13 | DRAFT | AI Agent | Initial architecture design |

## Purpose

Design a comprehensive namespace architecture that enables the MCP-Jive server to support multiple isolated projects/namespaces while maintaining backward compatibility with existing MCP clients and the web application.

## Architecture Overview

### Core Requirements

1. **Namespace Isolation**: Complete data separation between different projects/namespaces
2. **Backward Compatibility**: Existing MCP clients continue working without changes
3. **Default Namespace**: "default" namespace used when no namespace is specified
4. **Environment Variable Support**: `MCP_JIVE_NAMESPACE` environment variable for namespace configuration
5. **Request-Level Namespace**: Support namespace specification in MCP requests
6. **Web UI Support**: Frontend namespace selection and switching

### Namespace Implementation Strategy

#### 1. LanceDB Directory-Based Namespaces

**Current Structure:**
```
data/
└── lancedb/
    ├── work_items/
    ├── executions/
    └── progress/
```

**New Namespace Structure:**
```
data/
└── namespaces/
    ├── default/
    │   ├── work_items/
    │   ├── executions/
    │   └── progress/
    ├── project-alpha/
    │   ├── work_items/
    │   ├── executions/
    │   └── progress/
    └── project-beta/
        ├── work_items/
        ├── executions/
        └── progress/
```

#### 2. Namespace Resolution Hierarchy

**Priority Order:**
1. **Request-level namespace** (from MCP request metadata)
2. **Environment variable** (`MCP_JIVE_NAMESPACE`)
3. **Default namespace** ("default")

#### 3. MCP Protocol Integration

**Namespace Specification Methods:**

**Method 1: Environment Variable**
```bash
export MCP_JIVE_NAMESPACE="project-alpha"
./bin/mcp-jive server start
```

**Method 2: Request Metadata** (Future Enhancement)
```json
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "jive_manage_work_item",
    "arguments": {...},
    "_namespace": "project-alpha"
  }
}
```

## Component Architecture

### 1. Namespace Manager

**Location**: `src/mcp_jive/namespace/namespace_manager.py`

**Responsibilities:**
- Namespace resolution and validation
- Directory creation and management
- Namespace metadata tracking
- Migration utilities

**Key Methods:**
```python
class NamespaceManager:
    def resolve_namespace(self, request_namespace: Optional[str] = None) -> str
    def get_namespace_path(self, namespace: str) -> Path
    def create_namespace(self, namespace: str) -> bool
    def list_namespaces(self) -> List[str]
    def validate_namespace(self, namespace: str) -> bool
    def migrate_default_data(self) -> bool
```

### 2. Enhanced LanceDB Manager

**Modifications to**: `src/mcp_jive/lancedb_manager.py`

**Changes:**
- Accept namespace parameter in constructor
- Dynamic database path based on namespace
- Namespace-aware table initialization

**Enhanced Constructor:**
```python
class LanceDBManager:
    def __init__(self, config: DatabaseConfig, namespace: str = "default"):
        self.namespace = namespace
        self.db_path = self._get_namespace_db_path(namespace)
        # ... existing initialization
```

### 3. MCP Server Namespace Integration

**Modifications to**: `src/mcp_jive/server.py`

**Changes:**
- Namespace resolution in server initialization
- Environment variable reading
- Namespace-aware component creation

**Enhanced Server Initialization:**
```python
class MCPServer:
    def __init__(self, config: ServerConfig, namespace: Optional[str] = None):
        self.namespace_manager = NamespaceManager()
        self.current_namespace = self.namespace_manager.resolve_namespace(namespace)
        # ... create components with namespace
```

### 4. Frontend Namespace Support

**New Components:**
- Namespace selector dropdown
- Namespace management interface
- Namespace-aware API calls

**API Endpoints:**
```
GET /api/namespaces - List available namespaces
POST /api/namespaces - Create new namespace
GET /api/namespaces/{namespace}/status - Get namespace status
```

## Implementation Plan

### Phase 1: Core Namespace Infrastructure

1. **Create NamespaceManager**
   - Implement namespace resolution logic
   - Add directory management utilities
   - Create validation methods

2. **Enhance LanceDBManager**
   - Add namespace parameter support
   - Implement namespace-aware database paths
   - Update table initialization for namespaces

3. **Update Server Initialization**
   - Add environment variable reading
   - Integrate namespace resolution
   - Update component creation with namespace

### Phase 2: Data Migration and Compatibility

1. **Migration Utilities**
   - Create migration script for existing data
   - Move current data to "default" namespace
   - Validate data integrity after migration

2. **Backward Compatibility Testing**
   - Test existing MCP clients
   - Validate web application functionality
   - Ensure no breaking changes

### Phase 3: Frontend Integration

1. **Namespace API**
   - Implement namespace management endpoints
   - Add namespace listing and creation
   - Update existing APIs for namespace awareness

2. **UI Components**
   - Create namespace selector component
   - Add namespace management interface
   - Update navigation and state management

### Phase 4: Advanced Features

1. **Request-Level Namespace Support**
   - Implement MCP request metadata parsing
   - Add per-request namespace override
   - Update tool registry for namespace awareness

2. **Namespace Administration**
   - Add namespace deletion and archiving
   - Implement namespace export/import
   - Create namespace analytics and monitoring

## Quality Attributes

### Scalability
- **Strategy**: Directory-based isolation allows unlimited namespaces
- **Implementation**: Each namespace has independent LanceDB instance
- **Monitoring**: Track namespace count and storage usage

### Performance
- **Strategy**: Lazy namespace initialization and caching
- **Implementation**: Load namespaces on-demand, cache active instances
- **Monitoring**: Track namespace switching performance

### Security
- **Strategy**: Complete data isolation between namespaces
- **Implementation**: Separate database directories, no cross-namespace access
- **Validation**: Namespace name validation and sanitization

### Reliability
- **Strategy**: Graceful fallback to default namespace
- **Implementation**: Robust error handling and namespace validation
- **Recovery**: Automatic namespace creation and repair utilities

## Migration Strategy

### Existing Data Migration

1. **Pre-Migration Backup**
   ```bash
   cp -r data/lancedb data/lancedb.backup.$(date +%Y%m%d)
   ```

2. **Migration Process**
   ```bash
   # Create namespace structure
   mkdir -p data/namespaces/default
   
   # Move existing data
   mv data/lancedb/* data/namespaces/default/
   
   # Update configuration
   # (handled by migration script)
   ```

3. **Validation**
   - Verify all data accessible in default namespace
   - Test existing MCP client connections
   - Validate web application functionality

### Rollback Plan

1. **Emergency Rollback**
   ```bash
   # Stop server
   # Restore backup
   rm -rf data/namespaces
   mv data/lancedb.backup.YYYYMMDD data/lancedb
   # Restart server
   ```

## Testing Strategy

### Unit Tests
- NamespaceManager functionality
- LanceDBManager namespace support
- Namespace resolution logic

### Integration Tests
- End-to-end namespace isolation
- MCP client compatibility
- Web application namespace switching

### Performance Tests
- Namespace switching latency
- Concurrent namespace access
- Large namespace count handling

## Configuration

### Environment Variables

```bash
# Default namespace for server instance
MCP_JIVE_NAMESPACE=project-alpha

# Namespace data directory (optional)
MCP_JIVE_NAMESPACE_DIR=/custom/path/namespaces

# Enable namespace debugging (optional)
MCP_JIVE_NAMESPACE_DEBUG=true
```

### Server Configuration

```python
# config.py additions
@dataclass
class NamespaceConfig:
    default_namespace: str = "default"
    namespace_dir: Optional[str] = None
    auto_create_namespaces: bool = True
    namespace_validation_strict: bool = True
```

## Security Considerations

### Namespace Isolation
- **File System**: Separate directories prevent cross-namespace access
- **Database**: Independent LanceDB instances per namespace
- **API**: Namespace validation in all endpoints

### Namespace Validation
- **Allowed Characters**: Alphanumeric, hyphens, underscores only
- **Length Limits**: 3-50 characters
- **Reserved Names**: "admin", "system", "config" prohibited

### Access Control (Future)
- **Authentication**: Namespace-based user authentication
- **Authorization**: Role-based namespace access
- **Audit**: Namespace access logging

## Monitoring and Observability

### Metrics
- Active namespace count
- Namespace switching frequency
- Storage usage per namespace
- Performance metrics per namespace

### Logging
- Namespace resolution events
- Namespace creation/deletion
- Cross-namespace access attempts
- Migration and maintenance operations

## Future Enhancements

### Advanced Namespace Features
1. **Namespace Templates**: Pre-configured namespace setups
2. **Namespace Sharing**: Controlled cross-namespace data sharing
3. **Namespace Archiving**: Long-term storage and retrieval
4. **Namespace Analytics**: Usage patterns and insights

### Enterprise Features
1. **Multi-Tenant Support**: Organization-level namespace grouping
2. **Namespace Quotas**: Storage and resource limits
3. **Backup Integration**: Automated namespace backup
4. **Compliance**: Data retention and audit trails

## Conclusion

This namespace architecture provides a robust foundation for multi-project support while maintaining backward compatibility and ensuring complete data isolation. The phased implementation approach minimizes risk and allows for thorough testing at each stage.

The directory-based approach leverages LanceDB's natural capabilities and provides a scalable solution that can grow with user needs. The comprehensive migration strategy ensures existing users experience no disruption during the transition.