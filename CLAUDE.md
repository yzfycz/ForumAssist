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

6. **Multi-Account Support Implementation (2025-09-29)**
   - Enhanced ConfigManager to support multiple accounts per forum with new configuration structure
   - Updated AccountManager to prevent duplicate username creation within the same forum
   - Added account switching functionality to MainFrame file menu
   - Maintained existing account selection interface with list-based display
   - Implemented comprehensive account CRUD operations (Create, Read, Update, Delete)
   - Added username duplication validation for account creation and editing
   - Enhanced configuration file structure to support multiple accounts per forum
   - Preserved existing encryption and security measures for password storage

7. **Hierarchical Tree View Implementation (2025-09-29)**
   - Implemented hierarchical forum structure display using existing API data
   - Enhanced tree view to show multi-level forum categories (level 0: forum, level 1: typeid1, level 2: typeid2)
   - Removed unwanted "分类▼" and "状态▼" nodes from tree display
   - Eliminated level prefixes (第0级, 第1级) as screen readers handle this automatically
   - Added proper tree node data storage with type information for content loading
   - Implemented type-specific content loading methods for different forum categories
   - Fixed account creation dialog to default select first forum option

8. **Message Privacy Enhancement (2025-09-29)**
   - Modified message list display to hide message content, showing only usernames
   - Enhanced message conversation view to display full content when opening detailed conversation
   - Fixed field name mapping issues between HTML parser and display methods
   - Implemented proper message ordering to show oldest messages first, newest at bottom
   - Added window maximization on application startup for better visibility

9. **Thread Detail Pagination and Focus Management Fixes (2025-09-30)**
   - Fixed critical thread detail pagination issue where multi-page threads only showed "page 1 of 1"
   - Added auth parameter extraction from login response and passing to thread detail API calls
   - Corrected pagination data extraction from API response (message.page/totalpage instead of message.pagination)
   - Fixed floor numbering display to show actual floor numbers (21st floor, 22nd floor, etc.) on page 2+
   - Implemented intelligent keyboard cursor position memory and restoration
   - Enhanced screen reader compatibility with automatic focus on original post (index 0)
   - Unified window title format across all functions: "论坛名字-<昵称>-论坛助手"
   - Fixed title to remain constant when entering thread details instead of changing with each thread
   - Cleaned up all debug console output for cleaner user experience
   - Resolved syntax errors causing program startup failures due to indentation issues

### Key Technical Improvements
- **Auth Parameter Flow**: Added auth extraction in AuthenticationManager and passing to ForumClient for complete content access
- **Focus Management System**: Implemented saved_list_index and saved_page_info for precise focus restoration
- **Floor Calculation Logic**: Enhanced to consider current page number for correct floor display across multiple pages
- **Pagination Data Pipeline**: Fixed data corruption issues between API response and display methods
- **Title Format Standardization**: All functions now use consistent "forum-<nickname>-forum助手" format
- **Code Cleanup**: Removed all debug print statements and fixed indentation errors

### Multi-Account Configuration Structure
```
[Forum_争渡论坛]
url = http://www.zd.hk/
username1 = user1
nickname1 = 用户1
password1 = [encrypted_password]
username2 = user2
nickname2 = 用户2
password2 = [encrypted_password]
```

### Key Implementation Details
- **Backward Compatibility**: Existing configuration files are automatically supported
- **Security**: Password encryption and decryption maintained with AES encryption
- **User Experience**: Account selection interface remains unchanged with familiar list layout
- **Data Integrity**: Duplicate username prevention ensures consistent account management
- **Menu Integration**: Added "切换账户" option to file menu for easy account switching

10. **DataViewListCtrl Migration and Screen Reader Optimization (2025-10-02)**
    - Replaced wx.ListCtrl with wx.dataview.DataViewListCtrl for better long text handling and auto-wrapping
    - Completely resolved text truncation issues in post detail display when content exceeds normal length
    - Implemented new data storage architecture using separate `list_data` array instead of hidden columns
    - Eliminated "数据: XXX" information being read by screen readers from hidden DataViewListCtrl columns
    - Updated all display methods to use single-column layout with metadata storage:
      * `display_threads`: Stores thread ID and type information in `list_data`
      * `display_posts`: Stores floor index and post data for thread details
      * `display_messages`: Stores user ID and message data for private messages
      * `display_message_conversation`: Stores conversation message data
      * `add_pagination_controls`: Stores pagination control metadata
    - Modified event handling methods to retrieve data from `list_data` array instead of hidden columns
    - Enhanced regex-based data cleaning to remove any residual "数据: XXX" information from display text
    - Maintained native screen reader compatibility without requiring special adaptations
    - Preserved all existing functionality including keyboard navigation, pagination, and content loading

### Key Technical Improvements (DataViewListCtrl Migration)
- **Data Storage Architecture**: Replaced hidden columns with separate `list_data` array for metadata storage
- **Screen Reader Optimization**: Eliminated hidden column data being read by assistive technologies
- **Text Display Enhancement**: DataViewListCtrl provides better long text handling and automatic wrapping
- **Event Handling Update**: Modified all interaction methods to work with new data storage approach
- **Data Cleaning Enhancement**: Comprehensive regex patterns to remove unwanted data information
- **Accessibility Preservation**: Maintained native screen reader support without special adaptations
- **Backward Compatibility**: All existing functionality preserved with improved user experience

11. **Dialog Event Handling and User Experience Fixes (2025-10-02)**
    - Fixed dialog cancel buttons requiring two clicks to close due to improper event handling
    - Resolved page jump dialog Enter key issues by implementing custom dialog with proper key binding
    - Added comprehensive dialog state management to prevent duplicate dialog opening
    - Implemented proper sizer parent-child relationships to fix wxPython assertion errors
    - Enhanced focus management using wx.CallAfter to avoid timing issues with dialog initialization
    - Added dialog-specific event handlers for cancel buttons and close events
    - Fixed sizer architecture: panel.SetSizer() for child panels, dialog.SetSizerAndFit() for main dialog sizer
    - Implemented dialog state flags (_reply_dialog_open, _page_dialog_open) to prevent concurrent opening
    - Added comprehensive exception handling with state cleanup to prevent dialog lock-up
    - Improved user experience with automatic focus setting and text selection in input fields

### Key Technical Improvements (Dialog Fixes)
- **Dialog State Management**: Implemented robust state tracking to prevent duplicate dialog instances
- **Event Handling Optimization**: Added dedicated event handlers for cancel buttons and dialog close events
- **Sizer Architecture Fix**: Corrected parent-child sizer relationships to resolve wxPython assertion warnings
- **Focus Management Enhancement**: Used wx.CallAfter for proper focus timing in dialog initialization
- **Keyboard Navigation**: Implemented proper Enter key handling in custom page jump dialog
- **Exception Safety**: Added comprehensive state cleanup in exception handlers to prevent dialog lock-up
- **User Experience**: Improved input field behavior with automatic focus and text selection