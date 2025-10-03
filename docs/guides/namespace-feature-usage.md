# Namespace Feature Usage Guide

**Status**: ✅ COMPLETED | **Priority**: Medium | **Last Updated**: 2024-12-19
**Assigned Team**: Frontend Team | **Progress**: 100%
**Dependencies**: 0 Blocking | 0 Related

## Status History
| Date | Status | Updated By | Notes |
|------|--------|------------|-------|
| 2024-12-19 | COMPLETED | AI Agent | Initial implementation completed |

## Overview

The namespace feature allows users to organize and isolate work items across different projects or environments. This guide covers how to use the namespace functionality in both the frontend UI and backend API.

## Frontend Usage

### Namespace Selector

The namespace selector is located in the application header, next to the connection status indicator.

#### Features:
- **Visual Project Switching**: Dropdown menu showing available namespaces
- **Active Namespace Indicator**: Shows currently selected namespace with "Active" chip
- **Connection Awareness**: Disabled when not connected to server
- **Loading States**: Shows loading indicator during namespace changes
- **Persistent Selection**: Remembers last selected namespace in localStorage

#### Available Namespaces:
- `default` - Default Project (main workspace)
- `project-alpha` - Project Alpha
- `project-beta` - Project Beta  
- `development` - Development environment
- `staging` - Staging environment

#### How to Switch Namespaces:
1. Click on the namespace dropdown in the header
2. Select the desired project from the list
3. The application will automatically refresh work items for the new namespace
4. The selection is saved and will persist across browser sessions

### Automatic Data Refresh

When switching namespaces:
- Work item lists automatically refresh
- All data is filtered to the selected namespace
- UI components listen for namespace change events
- Loading states are shown during transitions

## Backend Implementation

### Namespace Context

The backend supports namespace isolation through:

#### Database Separation
- Each namespace uses a separate LanceDB database
- Database paths: `data/lancedb/{namespace}/` (or `data/lancedb/` for default)
- Complete data isolation between namespaces

#### MCP Tool Registry
- Namespace-aware tool registration
- Tools can be scoped to specific namespaces
- Context switching through `set_namespace_context` tool

#### Storage Layer
- `WorkItemStorage` supports namespace parameter
- All CRUD operations respect namespace context
- Automatic namespace validation and creation

### API Usage

#### Setting Namespace Context
```python
# Set namespace context (None for default)
registry.set_namespace_context("project-alpha")

# Create work item in current namespace
work_item = storage.create_work_item({
    "title": "Feature Implementation",
    "description": "Implement new feature",
    "item_type": "feature",
    "status": "pending"
})
```

#### Namespace-Aware Operations
```python
# List work items in specific namespace
work_items = storage.list_work_items(namespace="project-alpha")

# Search across namespace
results = storage.search_work_items(
    query="feature",
    namespace="project-alpha"
)
```

## Configuration

### Frontend Configuration

Namespace settings are managed through the `NamespaceContext`:

```typescript
// Available in components via useNamespace hook
const {
  currentNamespace,     // Currently selected namespace
  availableNamespaces,  // List of available namespaces
  setNamespace,         // Function to change namespace
  isLoading,           // Loading state
  error                // Error state
} = useNamespace();
```

### Backend Configuration

Namespace configuration in `config.py`:

```python
class DatabaseConfig:
    namespace: Optional[str] = None  # Current namespace
    base_path: str = "data/lancedb"  # Base database path
    
class Config:
    database: DatabaseConfig
    # ... other config
```

## Testing

### Namespace Isolation Tests

The namespace feature includes comprehensive tests:

- **Data Isolation**: Ensures work items don't leak between namespaces
- **Database Separation**: Verifies separate database instances
- **Context Switching**: Tests namespace change functionality
- **Backward Compatibility**: Ensures existing clients work with default namespace

### Running Tests

```bash
# Run namespace isolation tests
python tests/test_namespace_isolation.py

# Run full test suite
pytest tests/
```

## Best Practices

### Namespace Naming
- Use descriptive names: `project-name`, `environment-type`
- Avoid special characters except hyphens
- Keep names short but meaningful
- Use consistent naming conventions across projects

### Data Organization
- Use `default` namespace for general/shared work items
- Create project-specific namespaces for isolated work
- Use environment namespaces (`dev`, `staging`, `prod`) for deployment tracking
- Regularly clean up unused namespaces

### Performance Considerations
- Each namespace maintains its own database connection
- Switching namespaces triggers data refresh
- Consider namespace count impact on memory usage
- Monitor database file sizes per namespace

## Troubleshooting

### Common Issues

#### Namespace Not Switching
- Check WebSocket connection status
- Verify server is running and accessible
- Check browser console for JavaScript errors
- Ensure namespace exists in available list

#### Data Not Loading
- Verify namespace has been properly initialized
- Check database permissions in namespace directory
- Ensure work items exist in the selected namespace
- Review server logs for database connection errors

#### Performance Issues
- Monitor database file sizes
- Consider archiving old namespaces
- Check memory usage with multiple namespaces
- Optimize work item queries for large datasets

### Debug Commands

```bash
# Check namespace databases
ls -la data/lancedb/

# View namespace-specific data
ls -la data/lancedb/project-alpha/

# Check server logs
tail -f logs/mcp-jive.log
```

## Migration Guide

### Existing Data

Existing work items automatically use the `default` namespace:
- No migration required for existing installations
- Data remains accessible in default namespace
- New namespaces start empty

### Adding New Namespaces

1. **Frontend**: Add to `availableNamespaces` array in `NamespaceContext`
2. **Backend**: Namespace databases are created automatically on first use
3. **Testing**: Add namespace to test configurations

## Security Considerations

- Namespaces provide data isolation, not security boundaries
- All namespaces accessible to authenticated users
- Consider access controls for sensitive project data
- Regular backup of namespace-specific databases

## Future Enhancements

### Planned Features
- **Dynamic Namespace Creation**: UI for creating new namespaces
- **Namespace Permissions**: Role-based access to namespaces
- **Cross-Namespace Search**: Search across multiple namespaces
- **Namespace Templates**: Pre-configured namespace setups
- **Data Migration Tools**: Move work items between namespaces

### API Extensions
- REST endpoints for namespace management
- Bulk operations across namespaces
- Namespace analytics and reporting
- Export/import functionality per namespace

---

## Related Documentation

- [Architecture: Namespace Architecture](architecture/namespace-architecture.md)
- [API Reference: Work Item Storage](api/work-item-storage.md)
- [Testing: Namespace Isolation Tests](testing/namespace-tests.md)
- [Configuration: Database Settings](configuration/database.md)

---

*This documentation is maintained as part of the MCP Jive project. For questions or updates, please refer to the project repository.*