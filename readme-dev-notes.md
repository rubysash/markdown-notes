
## Development Notes

### Code Architecture
- **Modular Design**: Separated concerns across logical modules
- **Event-Driven**: Qt signals and slots for responsive UI
- **Error Resilient**: Comprehensive exception handling throughout
- **Memory Efficient**: Lazy loading and selective updates minimize resource usage

### Extension Points
- Custom CSS themes through template system
- Pluggable markdown extensions
- Configurable front matter templates
- Extensible file operation dialogs

### Best Practices Implemented
- PEP8 compliant code formatting
- DRY principles throughout codebase
- Comprehensive error handling
- Security-first approach to file operations
- Performance optimization for large file trees

---

## Known Limitations
- Currently supports only `.md` files for editing (by design)
- Large directory trees may take time to initially populate
- Cross-drive operations can be slower due to integrity verification
- Very large files may experience slower MD5 calculation during cross-drive moves

---

## Known Issues
- Folders are not displayed or allowed outside of the application folder
- Folders are allowed on other drives, but not same drive
- IMages only Work from Root
- Minor Debug messages
- creates a print_something.html but does not purge it

## Future Enhancements

Thoughts about future plans include:

- Plugin system for custom markdown extensions
- Advanced search and filtering capabilities
- Integrated version control support
- image paste/capture/clipboard help
- image paste/save into 'static' folder as per hugo
- search and replace all text in a folder
- export all button to create zip of all docs structure
- autosave when changing between files, checkbox to enable
- standardize file names and casing
- Tutorial for MD
- Code Snippets for various MD/hugo templates
- Youtube frame
- Spell checking
- Auto _index.md creation

--