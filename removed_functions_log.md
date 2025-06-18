# Removed Unused Functions

The following functions were removed during cleanup:

- `reset_state`, `push_state`, `pop_state`, `current_state` from `mybot/utils/admin_state.py`
- `truncate_text` from `mybot/utils/text_utils.py`
- `get_parent_menu`, `get_child_menu`, `get_main_reply_keyboard`, `get_admin_content_daily_gifts_keyboard`, `get_admin_content_minigames_keyboard` from `mybot/utils/keyboard_utils.py`
- `get_plan_list_kb` from `mybot/keyboards/tarifas_kb.py`
- `get_invite_link_options_kb` from `mybot/keyboards/free_channel_admin_kb.py`
- `clear_user_data` method from `mybot/utils/menu_manager.py`

Backup copies of the original files are stored in `backups/unused_code/`.
