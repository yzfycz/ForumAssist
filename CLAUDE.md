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
# Create temporary debug scripts as needed for API testing
# All temporary test files should be deleted after use
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

**Data Transformation**: User content APIs return `threadlist` format requiring conversion to displayable format. Must extract `thread` and `post` objects appropriately. For user posts, each item contains both thread info (subject, views, etc.) and post info (dateline_fmt, message, etc.).

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

### Recent Fixes (2025-09-29)
1. **User Content Display Fixes**
   - Fixed "我的发表" and "我的回复" not displaying content due to pagination data extraction errors
   - Corrected `get_user_posts` and `get_user_threads` methods to extract pagination info from `message.page` and `message.totalpage` instead of `message.pagination`
   - Fixed data transformation logic in `load_my_threads` method - items are direct thread objects, not nested
   - Unified data format consistency between user threads and posts

2. **Home Content Pagination Support**
   - Added pagination support to "最新发表" and "最新回复" features
   - Enhanced `get_home_content` method with page parameter support
   - Updated return structure to include pagination information
   - Added `current_orderby` state management for sorting context

3. **Pagination Logic Enhancement**
   - Fixed user posts handling in all pagination methods (next, previous, jump)
   - Added home content type support to all pagination handlers
   - Improved data format conversion for threadlist-based user content
   - Maintained consistent pagination behavior across all content types

4. **List Display Format Overhaul (2025-09-29)**
   - Implemented new comprehensive display format for all list types: `标题 作者:用户名;浏览:数量;板块:板块名;发表时间:时间;回复:数量;回复时间:时间;最后回复:用户名`
   - Changed from multi-column to single-column display (2000px width) to accommodate full information
   - Fixed "我的回复" data transformation to properly extract last username from `post.username` or fallback to `thread.lastusername`
   - Fixed column index errors in pagination controls for single-column layout
   - Enhanced information density while maintaining accessibility

### Key Implementation Details
- **Data Structure Consistency**: All user content methods now return unified `threadlist` format
- **Complete Pagination Coverage**: All content types now support full pagination functionality (我的发表: 58 pages, 我的回复: 116 pages)
- **State Management**: Added sorting context tracking for home content navigation
- **Backward Compatibility**: Maintained existing UI patterns while enhancing functionality
- **Display Format**: Standardized information-rich display format across all list types
- **Performance**: Optimized column width and data extraction for complete information display

### Testing and Validation
- Verified pagination functionality across all content types with real user data
- Tested data transformation logic for proper field extraction and display
- Validated new display format shows complete information without truncation
- Confirmed accessibility with keyboard navigation and screen reader compatibility

### Recent Fixes (2025-09-29)
5. **Reply List Navigation Fix**
   - Fixed issue where users couldn't enter threads from "我的回复" list by pressing Enter
   - Added 'user_posts' to the list activation condition in on_list_activated method (main_frame.py:691)
   - Ensured consistent navigation behavior across all user content types
   - Maintained proper thread detail loading for reply-based content