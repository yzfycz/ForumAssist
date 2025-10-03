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

12. **Post Content Viewer Enhancement (2025-10-02)**
    - Transformed post floor editor from editing mode to read-only viewing mode for better user experience
    - Modified TextCtrl to use wx.TE_READONLY and wx.TE_DONTWRAP styles for non-editable content display
    - Fixed wxPython sizer assertion errors by implementing proper parent-child sizer relationships
    - Enhanced dialog title and labels from "编辑" (Edit) to "浏览" (View) to reflect new functionality
    - Removed save button and simplified interface to include only close button for cleaner UX
    - Implemented comprehensive dialog state management with _floor_dialog_open flag to prevent duplicate opening
    - Added dedicated event handlers for close button and dialog close events to ensure proper state cleanup
    - Enhanced keyboard navigation with Escape and Backspace keys for quick dialog dismissal
    - Used wx.CallAfter for proper focus management and timing issues
    - Added exception safety with try-finally blocks to ensure state cleanup in all scenarios
    - Maintained all existing keyboard shortcuts and accessibility features

### Key Technical Improvements (Post Viewer Enhancement)
- **Read-Only Mode**: Converted editing functionality to viewing-only with proper style flags
- **Text Display Optimization**: Disabled automatic text wrapping while maintaining multi-line display capability
- **Dialog Architecture**: Implemented proper sizer hierarchy with separate main_sizer and panel sizer to resolve assertion errors
- **State Management**: Added _floor_dialog_open flag tracking with comprehensive cleanup in all exit paths
- **Event Handling**: Separated close button event handling from keyboard events for better control
- **Focus Management**: Used wx.CallAfter to set focus to content area for immediate screen reader access
- **Exception Safety**: Implemented robust error handling with state cleanup to prevent dialog lock-up
- **User Interface**: Simplified interface design with appropriate button labeling and dialog titles

13. **Forum Subsection First Content Page Auto-Detection (2025-10-02)**
   - Implemented binary search algorithm to automatically find the first content page in forum subsections with empty initial pages
   - Added `_find_first_content_page()` method using O(log n) time complexity for efficient page discovery
   - Enhanced `load_forum_section_with_type()` method to detect empty first pages and trigger automatic content search
   - Implemented comprehensive page offset management to maintain user-friendly pagination display
   - Updated all pagination methods (`load_next_page`, `load_previous_page`, `jump_to_page`) to handle page offsets correctly
   - Added encoding error handling for API responses to prevent search failures
   - Modified `display_threads()` method to accept and store API parameters for consistent pagination behavior
   - Ensured users see content pages as "page 1" with no ability to navigate to previous pages
   - Maintained backward compatibility with existing forum navigation functionality

### Key Technical Improvements (First Content Page Detection)
- **Binary Search Algorithm**: Efficient O(log n) search for finding first content page in large paginated subsections
- **Page Offset Management**: Complete offset system allowing seamless user experience when content starts on later pages
- **API Parameter Preservation**: Consistent parameter passing through all pagination operations for type-specific content
- **Error Handling**: Robust encoding error handling to prevent search interruption on problematic API responses
- **User Experience Optimization**: Transparent offset handling where users perceive found content as page 1
- **Backward Compatibility**: All existing functionality preserved while adding new smart detection capabilities

14. **Three-Level Forum Hierarchy Implementation (2025-10-03)**
    - Implemented complete three-level hierarchy structure for forum navigation (Forum → TypeID1 → TypeID2)
    - Enhanced tree view to display proper hierarchical relationships: 反馈 → 企业版/公益版 → 已解决/未解决
    - Modified tree building logic to correctly associate global TypeID2 (status) items with each TypeID1 category
    - Updated content loading methods to handle proper typeid1 + typeid2 parameter combinations for API calls
    - Enhanced pagination system to work with three-level hierarchy maintaining all existing functionality
    - Removed debug print statements from all source files for cleaner user experience
    - Verified functionality with real forum data showing correct thread counts for each combination

### Key Technical Improvements (Three-Level Hierarchy)
- **Hierarchical Data Structure**: Proper parent-child relationships between forum categories and status types
- **API Parameter Combination**: Correct typeid1 + typeid2 parameter passing for filtered content retrieval
- **Tree Architecture**: Enhanced tree building logic to support global typeid2 association with typeid1 categories
- **Content Loading**: Type-specific content loading methods that respect hierarchical relationships
- **Pagination Compatibility**: All pagination methods work seamlessly with three-level structure
- **Code Cleanup**: Removed all debug output for production-ready code quality

### Implementation Details
The three-level hierarchy correctly represents the forum structure:
```
反馈 (Forum ID: 4)
├── 企业版 (TypeID1: 1)
│   ├── 已解决 (TypeID2: 82) - 17 threads
│   └── 未解决 (TypeID2: 41) - 0 threads
├── 公益版 (TypeID1: 2)
│   ├── 已解决 (TypeID2: 82) - 20 threads
│   └── 未解决 (TypeID2: 41) - 19 threads
└── 其他分类...
    ├── 已解决
    └── 未解决
```

### Testing Results
- Verified correct API parameter combinations (typeid1 + typeid2) return expected thread counts
- Confirmed tree view displays proper hierarchical structure with expandable nodes
- Tested pagination functionality works correctly at all hierarchy levels
- Validated keyboard navigation and screen reader compatibility maintained

15. **List Numbering Feature Implementation (2025-10-03)**
    - Added configurable list numbering system that displays item positions in all list views
    - Implemented settings dialog with tabbed interface accessible via File → Settings menu
    - Enhanced ConfigManager with generic settings management methods for future extensibility
    - Added show_list_numbers configuration option stored in [Settings] section of config file
    - Updated all display methods to support optional numbering with consistent formatting
    - Implemented real-time list reloading when settings are changed for immediate effect
    - Added comprehensive error handling for DataViewListCtrl operations to prevent crashes

### Key Technical Improvements (List Numbering Feature)
- **Settings Architecture**: Implemented tabbed settings dialog with software settings tab for future expansion
- **Configuration Management**: Added generic get_setting() and set_setting() methods for managing application preferences
- **Numbering Logic**: Position-based numbering calculated after all items (including pagination controls) are added
- **Format Standardization**: All numbered items use consistent "，序号之总数项" format (e.g., "，1之24项")
- **Performance Optimization**: List rebuilding only occurs when numbering is enabled to minimize overhead
- **Error Handling**: Comprehensive try-catch blocks around DataViewListCtrl operations to handle API variations

### Implementation Details
**Settings Dialog Structure:**
```
Settings (Dialog)
└── Software Settings (Tab)
    └── [复选框] 显示列表序号
        说明：启用后将在列表中创建包含序号的隐藏列，格式为'1之24项'等
```

**Numbering Format Examples:**
- **Threads**: "测试标题 作者:张三;浏览:100;板块:技术讨论;发表时间:2025-01-01;回复:5;回复时间:2025-01-02;最后回复:李四 ，1之28项"
- **Posts**: "楼主 张三 说\n这是内容\n发表时间：2025-01-01 ，1之24项"
- **Messages**: "张三 ，1之10项"
- **Pagination**: "上一页(1) ，25之28项", "下一页(2) ，26之28项"
- **Page Jump**: "当前第1页共3页，回车输入页码跳转 ，27之28项"

**Menu Structure:**
```
文件 (File)
├── 切换账户 (保持原有位置)
├── 用户管理 (保持原有位置)
├── 设置 (新增) → 软件设置 → 显示列表序号
└── 退出 (保持原有位置)
```

**Configuration Structure:**
```ini
[Settings]
show_list_numbers = false  # 或 true
```

### Key Features
- **Optional Display**: Numbering is disabled by default, enabled via settings dialog
- **Comprehensive Coverage**: All list types support numbering (threads, posts, messages, conversations, pagination controls)
- **Real-time Updates**: Settings changes take effect immediately without requiring application restart
- **Accessibility Maintained**: All existing keyboard navigation and screen reader features preserved
- **Error Resilience**: Robust error handling prevents application crashes due to data inconsistencies
- **Future Extensible**: Settings architecture allows for easy addition of new configuration options

### Testing Results
- Verified settings dialog opens and functions correctly with proper sizer architecture
- Confirmed numbering appears correctly in all list types with proper format
- Tested real-time settings changes update lists immediately without requiring restart
- Validated pagination controls are included in numbering (e.g., "，25之28项" for last pagination item)
- Confirmed backward compatibility - existing functionality unchanged when numbering disabled
- Tested error handling with malformed API responses and missing data fields

16. **Keyboard Shortcuts Implementation (2025-10-03)**
    - Implemented comprehensive keyboard shortcuts system for enhanced accessibility and productivity
    - Added menu-level shortcuts with Alt+letter access keys and Ctrl+letter function shortcuts
    - Enhanced all dialog buttons with consistent Alt+letter activation shortcuts
    - Implemented accelerator table system for global keyboard shortcuts handling
    - Updated all UI text to display shortcut key hints for user guidance
    - Ensured no conflicts with existing Windows system shortcuts or accessibility tools

### Key Technical Improvements (Keyboard Shortcuts)
- **Menu Navigation**: Alt+F (文件), Alt+H (帮助) with submenu access via M/Q/P/A keys
- **Function Shortcuts**: Ctrl+M (账户管理), Ctrl+Q (切换账户), Ctrl+P (设置), F1 (关于)
- **Dialog Controls**: Standardized button shortcuts - O(确定), C(取消), S(发送), N(新建), E(编辑), D(删除), R(刷新), V(查看对话)
- **Accelerator Table**: Global shortcut handling using wx.AcceleratorTable for system-wide key capture
- **Text Display**: All UI elements show shortcut hints in parentheses (e.g., "设置(&P) Ctrl+P")
- **Accessibility**: Full keyboard navigation maintained with screen reader compatibility

### Implementation Details
**Menu Shortcuts:**
```
文件(&F)                    Alt+F
├── 账户管理(&M)            Ctrl+M (Account Management)
├── 切换账户(&Q)            Ctrl+Q (Switch Account - QieHuan)
├── 设置(&P)                Ctrl+P (Preferences/Settings)
└── 退出(&X)                Alt+F4 (Exit)

帮助(&H)                    Alt+H
└── 关于(&A)                F1 (About)
```

**Dialog Button Shortcuts:**
```
Common Dialog Controls:
- 确定(&O)                 Alt+O (OK/Confirm)
- 取消(&C)                 Alt+C (Cancel/Close)
- 发送(&S)                 Alt+S (Send)

Account Management:
- 新建 (Ctrl+N)           Ctrl+N only (no Alt shortcut)
- 编辑 (Ctrl+E)           Ctrl+E only (no Alt shortcut)
- 删除 (Ctrl+D)           Ctrl+D only (no Alt shortcut)
- 关闭                    Alt+C (Close)

Message Management:
- 刷新(&R) (F5)           Alt+R or F5 (Refresh)
- 查看对话(&V)            Alt+V (View Conversation)
```

**Technical Implementation:**
- Used wx.AcceleratorEntry and wx.AcceleratorTable for global shortcut handling
- Added & symbol in button labels for Alt+key navigation
- Implemented setup_keyboard_shortcuts() method in MainFrame for accelerator table binding
- Custom ID mapping (1001-1004) for menu shortcut event handling
- Preserved existing Ctrl+Enter and F5 shortcuts in message dialogs

### Key Features
- **Comprehensive Coverage**: All menus, dialogs, and common actions have keyboard shortcuts
- **User-Friendly Hints**: All UI elements display available shortcuts in parentheses
- **Conflict Avoidance**: Carefully selected shortcuts to avoid Windows system conflicts
- **Accessibility First**: Designed specifically for visually impaired users with screen readers
- **Backward Compatibility**: All existing functionality preserved with enhanced navigation
- **Consistent Patterns**: Standardized shortcut conventions across all interface elements

### Testing Results
- Verified all menu shortcuts work correctly with both Alt and Ctrl combinations
- Confirmed dialog button Alt+shortcuts activate proper actions
- Tested global accelerator table functionality without conflicts
- Validated shortcut hints display correctly in all UI text
- Confirmed screen reader compatibility with keyboard navigation
- Tested account management shortcuts (Ctrl+N/E/D) work without Alt interference
- Verified no conflicts with existing Windows accessibility tools or shortcuts

17. **Search Control Accessibility Enhancement (2025-10-03)**
    - Fixed critical screen reader accessibility issue where search control was read as "control 编辑框" instead of proper label
    - Analyzed successful accessibility patterns from account management dialog and applied them to search area
    - Resolved layout structure issues that were preventing proper label-control association for screen readers
    - Implemented proven 2-row, 2-column FlexGridSizer pattern for consistent accessibility behavior

### Key Technical Improvements (Search Accessibility)
- **Layout Structure Correction**: Changed from problematic 1×3 grid to proven 2×2 FlexGridSizer layout
- **Control Type Optimization**: Replaced complex wx.SearchCtrl with standard wx.TextCtrl for better accessibility support
- **Label Association**: Implemented proper StaticText label placement using verified pattern from working controls
- **Consistency Pattern**: Applied exact same layout approach as successful account management dialog fields

### Problem Analysis and Solution
**Root Cause Identified:**
- Original 3-column layout (label+search+button) broke label-control accessibility association
- wx.SearchCtrl's complex internal structure interfered with screen reader recognition
- Inconsistent layout pattern compared to other working accessible controls

**Technical Solution:**
```python
# Before (problematic):
grid_sizer = wx.FlexGridSizer(1, 3, 5, 5)  # 1行3列破坏了关联
self.search_ctrl = wx.SearchCtrl(...)      # 复合控件影响识别

# After (working):
grid_sizer = wx.FlexGridSizer(2, 2, 5, 5)  # 2行2列保持关联
self.search_ctrl = wx.TextCtrl(...)        # 标准控件支持更好
```

**Layout Structure:**
```
Row 1: [搜索标签:] [搜索框输入区域]
Row 2: [空标签]    [搜索按钮]
```

### Implementation Details
**Key Changes Made:**
- Changed grid layout from 1×3 to 2×2 FlexGridSizer for proper label association
- Replaced wx.SearchCtrl with standard wx.TextCtrl to avoid complex control structure issues
- Used same alignment flags as working controls: `wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL`
- Applied consistent spacing (5px gaps) matching account management dialog
- Maintained all existing functionality while improving accessibility

**Code Pattern Applied:**
```python
# 搜索标签 - 完全复制账户管理对话框的成功模式
search_label = wx.StaticText(search_panel, label="输入搜索关键词:")
self.search_ctrl = wx.TextCtrl(search_panel, style=wx.TE_PROCESS_ENTER)

# 2行2列布局
grid_sizer.Add(search_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
grid_sizer.Add(self.search_ctrl, 0, wx.EXPAND)
grid_sizer.Add(empty_label, 0, wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL)
grid_sizer.Add(search_button, 0, wx.ALIGN_LEFT)
```

### Testing Results
- **Before Fix**: Screen reader read "control 编辑框" (incorrect)
- **After Fix**: Screen reader correctly reads "输入搜索关键词: 编辑框" (correct)
- Verified search functionality remains fully operational
- Confirmed keyboard navigation (Tab/Enter) works properly
- Tested that the fix doesn't affect other UI elements or accessibility features
- Validated consistency with other accessible controls in the application

### Key Features
- **Screen Reader Compatibility**: Proper label-text association for assistive technologies
- **Keyboard Navigation**: Maintained full keyboard accessibility with Tab/Enter support
- **Visual Consistency**: Layout appearance unchanged for sighted users
- **Proven Pattern**: Implementation based on verified working accessibility patterns
- **Backward Compatibility**: All existing search functionality preserved
- **Minimal Impact**: Focused change with no side effects on other components

18. **Search Functionality and HTML Tag Cleaning Fixes (2025-10-03)**
    - Fixed search API data path issue where search was returning no results due to incorrect data structure access
    - Implemented comprehensive HTML tag cleaning across all search result display paths
    - Enhanced user experience with automatic focus jumping to first search result and empty result notifications
    - Added proper HTML tag cleaning in navigation restoration to prevent HTML code display when returning from post details

### Key Technical Improvements (Search and HTML Cleaning)
- **API Data Path Fix**: Corrected search method in forum_client.py to access `result.message` instead of `result.data`
- **HTML Tag Cleaning**: Implemented consistent HTML tag removal using existing `clean_html_tags()` utility function
- **Empty Result Handling**: Added user-friendly notifications with warning icon when no search results found
- **Automatic Focus Management**: Implemented automatic focus jumping to first search result for improved navigation
- **Navigation Consistency**: Ensured HTML tag cleaning is applied to all possible navigation paths including back navigation

### Implementation Details
**Fixed Search API Data Path:**
```python
# Before (forum_client.py)
message = result.get('data', {})

# After (forum_client.py)
message = result.get('message', {})
```

**HTML Tag Cleaning Implementation:**
- **Initial Search**: `search_content()` method cleans HTML tags before displaying results
- **Navigation Return**: `search_content_and_restore_focus()` method ensures clean display when returning from post details
- **Pagination Restoration**: `restore_to_correct_page()` method cleans HTML tags when restoring search results with pagination

**User Experience Enhancements:**
- Automatic focus jumps to first search result after successful search
- Warning dialog with appropriate icon displayed when no results found
- Consistent clean display across all navigation scenarios

### Testing Results
- Verified search functionality returns correct results with proper data structure access
- Confirmed HTML tags are properly cleaned in all display scenarios including back navigation
- Tested automatic focus jumping works correctly for improved keyboard navigation
- Validated empty result notifications show appropriate user-friendly messages
- Ensured consistency across all search result display paths and navigation scenarios

19. **Reply Content Line Break Enhancement (2025-10-03)**
    - Enhanced reply content processing to use `<p>` tags instead of `<br>` tags for better forum compatibility
    - Implemented line-by-line wrapping where each line of user input is wrapped with `<p>` and `</p>` tags
    - Improved display format to match forum's native HTML structure for proper line break rendering

### Key Technical Improvements (Reply Content Enhancement)
- **HTML Structure Compatibility**: Changed from `<br>` tags to `<p>` tags to match forum's native HTML format
- **Line-by-Line Processing**: Each line (including empty lines) is wrapped with paragraph tags for consistent formatting
- **HTML Tag Preservation**: User input HTML tags are preserved and work correctly within paragraph structure
- **Forum Integration**: Better integration with forum's content display system

### Implementation Details
**Content Processing Logic:**
```python
# Before (using <br> tags)
return text.replace('\n', '<br>')

# After (using <p> tags)
lines = text.split('\n')
wrapped_lines = []
for line in lines:
    wrapped_lines.append(f'<p>{line}</p>')
return ''.join(wrapped_lines)
```

**Example Transformation:**
```
User Input:
第一行内容

第二行内容
<b>加粗文字</b>

HTML Output:
<p>第一行内容</p>
<p></p>
<p>第二行内容</p>
<p><b>加粗文字</b></p>
<p></p>
```

### Key Features
- **Paragraph-Based Structure**: Each line becomes a separate paragraph for better HTML semantics
- **Empty Line Preservation**: Empty lines are preserved as empty paragraphs for user-controlled spacing
- **HTML Compatibility**: User-input HTML tags work correctly within the paragraph structure
- **Forum Native Format**: Output format matches forum's expected HTML structure for optimal display

20. **Code Generator Feature Implementation (2025-10-03)**
    - Implemented comprehensive code generator functionality in reply dialog for easy HTML code insertion
    - Added "添加代码(&J)" button to reply dialog with keyboard shortcut support
    - Created CodeGeneratorDialog class with dynamic field labels based on selected code type
    - Supported code types: 超链接, 音频, 图片 (in that order)
    - Implemented smart code insertion at cursor position with automatic focus management
    - Enhanced user experience with proper focus behavior and keyboard navigation

### Key Technical Improvements (Code Generator Feature)
- **Dynamic Dialog Interface**: Field labels automatically update based on selected code type
- **Smart Code Insertion**: Generated code is inserted at cursor position with proper focus restoration
- **Comprehensive Code Support**: Multiple code types with proper HTML formatting:
  - 超链接: `<a href="地址">名称</a>`
  - 音频: `<audio controls="controls" src="地址" title="名称"> </audio>`
  - 图片: `<a href="地址"><img alt="名称" src="地址" /></a>`
- **Focus Management**: Default focus on combo box for easy type selection, proper focus handling after insertion
- **Keyboard Accessibility**: Full keyboard navigation with Alt+J shortcut for code generator access

### Implementation Details
**Code Generator Dialog Structure:**
```
┌─────────────────────────┐
│ 添加代码                 │
├─────────────────────────┤
│ 代码类型: [超链接▼]      │
│                         │
│ 超链接名字: [        ]  │
│ 超链接地址: [        ]  │
│                         │
│ [确定]     [取消]        │
└─────────────────────────┘
```

**Dynamic Field Labels:**
- **超链接**: 超链接名字 + 超链接地址
- **音频**: 音频名称 + 音频地址
- **图片**: 图片名称 + 图片地址

**Code Insertion Logic:**
```python
# Insert generated code at cursor position
current_content = content_ctrl.GetValue()
cursor_pos = content_ctrl.GetInsertionPoint()
new_content = current_content[:cursor_pos] + generated_code + current_content[cursor_pos:]
content_ctrl.SetValue(new_content)
content_ctrl.SetInsertionPoint(cursor_pos + len(generated_code))
```

### Key Features
- **Multi-Type Support**: Three code types with optimized HTML formatting for forum use
- **User-Friendly Interface**: Simple dialog with clear labeling and intuitive layout
- **Smart Integration**: Seamless integration with existing reply dialog functionality
- **Focus Optimization**: Default focus on combo box for type selection, automatic focus return after insertion
- **Keyboard Navigation**: Full keyboard accessibility with proper tab order and shortcuts
- **Error Handling**: Input validation with user-friendly error messages

### Testing Results
- Verified all code types generate correct HTML output with proper formatting
- Confirmed dynamic label updates work correctly for different code types
- Tested code insertion at various cursor positions within existing content
- Validated keyboard navigation and focus management across all dialog elements
- Confirmed proper integration with existing reply dialog functionality