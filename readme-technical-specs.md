
## Technical Specifications

### Dependencies
- **PyQt5**: Core GUI framework with WebEngine for HTML rendering
- **markdown**: Markdown to HTML conversion with extensions
- **hashlib**: File integrity verification
- **shutil**: Advanced file operations
- **platform**: Cross-platform compatibility

### Key Classes
- `MarkdownManagerApp`: Main application window with tabbed interface
- `MarkdownTreeWidget`: Enhanced tree widget with drag-and-drop and lazy loading
- `ConfigManager`: Handles configuration and template management
  - Creates CSS user directory structure on first run
  - Copies template files (.tpl) to user CSS files
  - Provides direct template-to-user file reset functionality
  - Implements emergency fallback CSS when files are missing
- `MoveConfirmationDialog`: Advanced file operation confirmation with risk assessment
- `MoveProgressDialog`: Progress tracking for long-running operations

### Performance Optimizations
- **Lazy Loading**: Tree nodes load children only when expanded, reducing memory usage
- **Selective Refresh**: Updates only modified directories instead of full tree reload
- **State Preservation**: Maintains expanded nodes and selection across operations
- **Chunked MD5 Processing**: Memory-efficient hash calculation for large files during integrity verification

### Basic Operations
1. **File Management**: Use tree context menus or keyboard shortcuts
2. **Editing**: Click any `.md` file to open in editor
3. **Preview**: Switch to Preview tab for live HTML rendering
4. **Styling**: Use Style tab to customize appearance
5. **Saving**: Ctrl+S or click the Save button (changes color when unsaved)

### Advanced Features
- **Drag & Drop**: Drag files/folders to reorganize structure
- **Front Matter**: Use "Add Front Matter" button for blog-style headers
- **Style Reset**: "Reset Style" button restores default appearance
- **Tree Refresh**: Manual refresh preserves your current view state
