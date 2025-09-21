# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ForumAssist is a Windows-based accessible forum client specifically designed for visually impaired users. Built with Python and WxPython, it provides 100% keyboard-operable access to forums with full screen reader support. The project currently supports Zhengdu Forum (zd.hk) with plans to expand to other forum platforms.

## Common Commands

### Running the Application
```bash
# Main entry point
python main.py

# Install dependencies
pip install -r requirements.txt
```

### Testing and Debugging
```bash
# Test specific API endpoints (create debug scripts as needed)
python debug_api_endpoints.py

# Test data formatting logic
python test_data_formatting.py

# Test pagination functionality
python test_pagination.py
```

### Development Setup
```bash
# Run linter (if available)
flake8 src/ --max-line-length=120

# Type checking (if mypy is installed)
mypy src/ --ignore-missing-imports
```

## Architecture Overview

### Core Components

**Authentication Flow**: The app uses real-time authentication with `AuthenticationManager` maintaining session cookies in memory only. No persistent credentials are stored except encrypted passwords in config files.

**Data Pipeline**: ForumClient → API Integration → Data Transformation → Display Methods. All API responses follow the pattern `result.message.{data_structure}` rather than `result.data`.

**UI Architecture**: Single-window design with tree navigation (left) and list content (right). All interactions must be keyboard-accessible with proper focus management.

### Key Classes and Responsibilities

**MainFrame** (`src/main_frame.py`): Central UI controller managing tree/list views, keyboard navigation, pagination, and state restoration. Handles complex focus management for accessibility.

**AuthenticationManager** (`src/auth_manager.py`): Manages login sessions and user info. Merges forum config with API user data, handles session lifecycle.

**ForumClient** (`src/forum_client.py`): API client with data parsing logic. All methods expect data in `result.message` structure, not `result.data`.

**AccountManager** (`src/account_manager.py`): Modal dialog for account management with ComboBox selection and login validation.

**ConfigManager** (`src/config_manager.py`): Handles INI file operations with AES encryption for passwords.

### Critical Design Patterns

**Pagination System**: Always displays 4 control items per design spec:
1. Previous page: "上一页(page_num)"
2. Next page: "下一页(page_num)"
3. Page jump: "当前第X页共Y页，回车输入页码跳转"
4. Reply option: "回复帖子" (thread detail only)

**State Restoration**: Backspace navigation saves previous state (content_type, selected_index, tid) and restores both window title and focus position.

**Data Transformation**: User posts/threads APIs return `threadlist` format requiring conversion to displayable format. Must extract `thread` and `post` objects appropriately.

**Accessibility Requirements**: 100% keyboard navigation with proper focus management, screen reader friendly labels, and logical tab order.

### API Integration Notes

**Response Structure**: All successful API responses use:
```json
{
  "status": 1,
  "message": {
    // actual data structure varies by endpoint
  }
}
```

**Authentication**: Requires appkey/seckey in login requests. Sessions managed via requests.Session cookies.

**Data Parsing**: Forum data is nested - thread lists may contain thread objects, user data combines config + API responses.

## Configuration

### API Settings
Edit `config/api_config.py` for forum endpoints and credentials:
- `APPKEY`/`SECKEY`: Forum API authentication
- `API_ENDPOINTS`: Map of endpoint names to URL paths
- `ORDERBY_OPTIONS`: Sorting parameters for different content types

### User Configuration
Accounts stored in `config/forums.ini` (auto-created):
- Forum URLs, usernames, encrypted passwords
- AES encryption using `src/utils/crypto.py`

## Development Notes

### Accessibility Implementation
- All interactive elements must be keyboard-navigable
- Use proper ARIA labels and focus management
- Implement logical tab order and screen reader compatibility
- Support standard keyboard shortcuts (Tab, Enter, Esc, arrows)

### State Management
- Previous state saved before navigation changes
- Focus restoration uses dual lookup (TID + index fallback)
- Window titles reflect current context: `{function}-{user_nickname}-论坛助手`

### Error Handling
- Network errors: Show user-friendly messages with retry options
- API failures: Parse error responses and display meaningful feedback
- Authentication issues: Guide users to re-login with proper error messages

### Testing Considerations
- Test keyboard navigation flow thoroughly
- Verify focus restoration after navigation
- Validate API response parsing with real forum data
- Check accessibility with screen readers when possible

### Recent Fixes (2025-09-21)
1. **HTML Content Display Enhancement**
   - Added `clean_html_tags` method to filter HTML tags while preserving line breaks
   - Converts `<br>`, `<p>`, `<div>` tags to appropriate line breaks
   - Handles HTML entities (`&nbsp;`, `&lt;`, `&gt;`, etc.)
   - Maintains paragraph structure and text formatting in post details

2. **Pagination Controls Visibility**
   - Optimized pagination control display format
   - Simplified page jump text: "第X页/共Y页 (回车跳转)"
   - Set multi-column display to prevent text truncation
   - Ensured pagination controls are always visible per design requirements

3. **Focus Restoration Improvements**
   - Fixed interference from pagination controls on focus restoration
   - Exclude pagination control items (negative TID values) during focus lookup
   - Enhanced dual lookup mechanism: TID-based search with index fallback
   - Improved backspace navigation to correctly restore focus to previously opened posts

### Key Implementation Details
- **HTML Processing**: Smart HTML tag removal that preserves document structure
- **Focus Management**: Handles pagination control interference in list navigation
- **UI Consistency**: Pagination controls follow the 4-item design specification