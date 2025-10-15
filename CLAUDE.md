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

## Key Features and Implementation

### Data Management
- **DataViewListCtrl Migration**: Replaced wx.ListCtrl with wx.dataview.DataViewListCtrl for better long text handling and screen reader optimization
- **List Data Architecture**: Uses separate `list_data` array for metadata storage instead of hidden columns
- **Display Format**: Comprehensive information display: `标题 作者:用户名;浏览:数量;板块:板块名;发表时间:时间;回复:数量;回复时间:时间;最后回复:用户名`

### Navigation System
- **Multi-Level Navigation**: Support for complex navigation flows (forum list → thread detail → user content → thread detail → back to user content → back to original forum list)
- **State Preservation**: Complete state saving across all navigation levels with automatic restoration
- **Focus Management**: Intelligent cursor position memory and restoration for accessibility

### User Interface Features
- **Hierarchical Tree View**: Three-level forum hierarchy (Forum → TypeID1 → TypeID2)
- **List Numbering**: Optional numbering system for better orientation in lists
- **Keyboard Shortcuts**: Comprehensive shortcut system including Alt+letter menus, Ctrl+letter functions, and dialog shortcuts
- **Context Menus**: Right-click and Application Key context menus with letter shortcuts

### Content Management
- **Search Functionality**: Full-text search with HTML tag cleaning and result navigation
- **User Content**: Complete user content navigation with pagination support
- **Reply System**: Enhanced reply functionality with code generator and HTML formatting
- **Filter Mode**: "只看他" (View Only) feature for filtering posts by specific users

### Special Features
- **Post Content Viewer**: Read-only dialog for viewing individual post floors with resource extraction
- **Settings Dialog**: Tabbed interface for application preferences
- **Multi-Account Support**: Switch between multiple forum accounts seamlessly

## Recent Major Fixes (2025-10)

1. **State Saving Logic Fix** (2025-10-15)
   - Fixed navigation from thread lists back to original forum lists
   - Restored simple state saving condition from reference version
   - Maintained all user content navigation functionality

2. **User Content Navigation Implementation** (2025-10-15)
   - Complete multi-level navigation system for user content
   - Page position and focus memory across navigation
   - Title format standardization

3. **Filter Mode Implementation** (2025-10-12)
   - "只看他" feature with original pagination structure
   - Original floor number preservation
   - Direct return navigation to forum lists

4. **Navigation and Reply Enhancements** (2025-10-11)
   - Thread list state preservation without API refresh
   - Reply page position maintenance
   - Enhanced error handling for reply operations

5. **Keyboard Shortcuts and Context Menu** (2025-10-09)
   - Fixed Ctrl+Enter and Shift+Enter in post details
   - Comprehensive letter shortcuts for context menus
   - Data structure compatibility improvements

## Critical Implementation Details

### State Management
```python
# State preservation for navigation
self.saved_list_state = {
    'list_data': self.list_data.copy(),
    'current_pagination': getattr(self, 'current_pagination', {}).copy(),
    'current_content_type': getattr(self, 'current_content_type', ''),
    'selected_index': selected if selected != -1 else 0,
    'window_title': self.GetTitle()
}
```

### API Response Handling
```python
# Standard API response structure
message = result.get('message', {})
threadlist = message.get('threadlist', [])
pagination = {
    'page': message.get('page', 1),
    'totalpage': message.get('totalpage', 1)
}
```

### Display Format
```python
# Standard list item display format
display_text = f"{title} 作者:{author};浏览:{views};板块:{forum};发表时间:{time};回复:{replies};回复时间:{reply_time};最后回复:{last_user}"
```

### Keyboard Event Handling
```python
# Post detail keyboard shortcuts
if event.ControlDown() and keycode == wx.WXK_RETURN:
    self.handle_reply_to_floor(selected_row)
    return  # Prevent event propagation

if event.ShiftDown() and keycode == wx.WXK_RETURN:
    self.handle_view_user_profile(selected_row)
    return
```

## Menu Structure and Shortcuts

### File Menu
```
文件(&F)                    Alt+F
├── 账户管理(&M)            Ctrl+M
├── 切换账户(&Q)            Ctrl+Q
├── 设置(&P)                Ctrl+P
└── 退出(&X)                Alt+F4
```

### Help Menu
```
帮助(&H)                    Alt+H
└── 关于(&A)                F1
```

### Context Menu Shortcuts
- **Thread List**: 刷新(&R), 网页打开(&W), 拷贝帖子标题(&C), 拷贝帖子地址(&D)
- **Post Detail**: 回复用户(&R), 查看资料(&H), 筛选只看(&P), 编辑楼层(&E)

## Development Best Practices

### Code Organization
- Keep state management logic centralized in MainFrame
- Use consistent error handling patterns across all methods
- Maintain separation between API calls and UI updates
- Implement proper focus management for all interactive elements

### Testing Strategy
- Test all navigation flows with real forum data
- Verify keyboard accessibility across all features
- Test state restoration after various navigation scenarios
- Validate screen reader compatibility

### Performance Considerations
- Use DataViewListCtrl for efficient large list handling
- Implement pagination to avoid loading excessive data
- Cache frequently accessed data to reduce API calls
- Use background threads for long-running operations

### Error Handling
- Implement graceful degradation for API failures
- Provide user-friendly error messages
- Use try-catch blocks around all external API calls
- Maintain application stability during network issues

## Configuration Management

### Settings Structure
```ini
[Settings]
show_list_numbers = false

[Forum_争渡论坛]
url = http://www.zd.hk/
username1 = user1
nickname1 = 用户1
password1 = [encrypted]
```

### Security Considerations
- All passwords stored with AES encryption
- No persistent credentials except encrypted passwords
- Session cookies stored in memory only
- Secure API key management