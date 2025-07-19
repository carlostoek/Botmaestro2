# utils/keyboard_utils.py
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from database.models import User
from utils.messages import BOT_MESSAGES


def get_main_menu_keyboard():
    """Returns the main inline menu keyboard."""
    keyboard = [
        [InlineKeyboardButton(text="💎 Mi Diván", callback_data="vip_subscription")],
        [
            InlineKeyboardButton(text="🎯 Misiones", callback_data="menu:missions"),
            InlineKeyboardButton(text="🎁 Regalo Diario", callback_data="daily_gift")
        ],
        [
            InlineKeyboardButton(text="🏆 Mi Perfil", callback_data="menu:profile"),
            InlineKeyboardButton(text="🗺️ Mochila", callback_data="open_backpack")
        ],
        [
            InlineKeyboardButton(text="💝 Recompensas", callback_data="menu:rewards"),
            InlineKeyboardButton(text="👑 Ranking", callback_data="menu:ranking")
        ],
        [InlineKeyboardButton(text="🏛️ Subastas", callback_data="auction_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_profile_keyboard():
    """Returns the keyboard for the profile section."""
    keyboard = [
        [
            InlineKeyboardButton(text="🔄 Actualizar", callback_data="menu:profile"),
            InlineKeyboardButton(text="🏠 Menú Principal", callback_data="menu_principal")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_missions_keyboard(missions: list, offset: int = 0):
    """Returns the keyboard for missions, with pagination."""
    keyboard = []
    # Display up to 4 missions per page for better readability
    for mission in missions[offset : offset + 4]:
        status_emoji = "✅" if hasattr(mission, 'completed') and mission.completed else "🎯"
        keyboard.append(
            [
                InlineKeyboardButton(
                    text=f"{status_emoji} {mission.name} ({mission.reward_points} besitos)",
                    callback_data=f"mission_{mission.id}",
                )
            ]
        )

    # Add navigation buttons if there are more missions
    nav_buttons = []
    if offset > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Anterior", callback_data=f"missions_page_{offset - 4}"
            )
        )
    if offset + 4 < len(missions):
        nav_buttons.append(
            InlineKeyboardButton(
                text="Siguiente ➡️", callback_data=f"missions_page_{offset + 4}"
            )
        )
    if nav_buttons:
        keyboard.append(nav_buttons)

    # Action buttons
    keyboard.append([
        InlineKeyboardButton(text="🔄 Actualizar", callback_data="menu:missions"),
        InlineKeyboardButton(text="🏠 Menú Principal", callback_data="menu_principal")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_reward_keyboard(
    rewards: list, claimed_ids: set[int], offset: int = 0
) -> InlineKeyboardMarkup:
    """Return reward keyboard with pagination and claim status."""

    keyboard = []
    # Display up to 4 rewards per page
    for reward in rewards[offset : offset + 4]:
        if reward.id in claimed_ids:
            text = f"✅ {reward.title}"
            callback = f"claimed_{reward.id}"
        else:
            text = f"🎁 {reward.title} ({reward.required_points} besitos)"
            callback = f"claim_reward_{reward.id}"
        keyboard.append([InlineKeyboardButton(text=text, callback_data=callback)])

    # Navigation buttons
    nav_buttons = []
    if offset > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Anterior", callback_data=f"rewards_page_{offset - 4}"
            )
        )
    if offset + 4 < len(rewards):
        nav_buttons.append(
            InlineKeyboardButton(
                text="Siguiente ➡️", callback_data=f"rewards_page_{offset + 4}"
            )
        )
    if nav_buttons:
        keyboard.append(nav_buttons)

    # Action buttons
    keyboard.append([
        InlineKeyboardButton(text="🔄 Actualizar", callback_data="menu:rewards"),
        InlineKeyboardButton(text="🏠 Menú Principal", callback_data="menu_principal")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_ranking_keyboard():
    """Returns the keyboard for the ranking section."""
    keyboard = [
        [
            InlineKeyboardButton(text="🔄 Actualizar", callback_data="menu:ranking"),
            InlineKeyboardButton(text="🏠 Menú Principal", callback_data="menu_principal")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_reaction_keyboard(
    message_id: int,
    like_text: str = "💋 Me encanta",
    dislike_text: str = "😴 No me gusta",
):
    """Return an inline keyboard with like/dislike buttons for channel posts."""
    keyboard = [
        [
            InlineKeyboardButton(
                text=like_text, callback_data=f"reaction_like_{message_id}"
            ),
            InlineKeyboardButton(
                text=dislike_text, callback_data=f"reaction_dislike_{message_id}"
            ),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_custom_reaction_keyboard(
    message_id: int, buttons: list[str]
) -> InlineKeyboardMarkup:
    """Return an inline keyboard using custom button texts for reactions."""
    if len(buttons) >= 2:
        like, dislike = buttons[0], buttons[1]
    else:
        like, dislike = "💋", "😴"
    return get_reaction_keyboard(message_id, like, dislike)


def get_admin_manage_users_keyboard():
    """Returns the keyboard for user management options in the admin panel."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Sumar Besitos", callback_data="admin_add_points"
                )
            ],
            [
                InlineKeyboardButton(
                    text="➖ Restar Besitos",
                    callback_data="admin_deduct_points",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔍 Ver Perfil de Usuario", callback_data="admin_view_user"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔎 Buscar Usuario", callback_data="admin_search_user"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📢 Notificar a Usuarios", callback_data="admin_notify_users"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Volver al Panel Admin",
                    callback_data="admin_main_menu",
                )
            ],
        ]
    )
    return keyboard


def get_admin_manage_content_keyboard():
    """Returns the keyboard for content management options."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👥 Gestionar Usuarios", callback_data="admin_manage_users"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎯 Misiones", callback_data="admin_content_missions"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏅 Insignias", callback_data="admin_content_badges"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📈 Niveles", callback_data="admin_content_levels"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎁 Catálogo del Diván",
                    callback_data="admin_content_rewards",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🏛️ Subastas", callback_data="admin_auction_main"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎁 Regalos Diarios", callback_data="admin_content_daily_gifts"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🕹 Minijuegos", callback_data="admin_content_minigames"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗺️ Administrar Pistas",
                    callback_data="admin_content_lore_pieces",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🎉 Eventos y Sorteos",
                    callback_data="admin_manage_events_sorteos",
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Volver al Panel Admin",
                    callback_data="admin_main_menu",
                )
            ],
        ]
    )
    return keyboard


def get_admin_content_missions_keyboard():
    """Keyboard for mission management options."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Crear Misión", callback_data="admin_create_mission"
                )
            ],
            [
                InlineKeyboardButton(
                    text="✅/❌ Activar/Desactivar",
                    callback_data="admin_toggle_mission",
                )
            ],
            [
                InlineKeyboardButton(
                    text="👁 Ver Activas", callback_data="admin_view_missions"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Eliminar", callback_data="admin_delete_mission"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Volver", callback_data="admin_manage_content"
                )
            ],
        ]
    )
    return keyboard


def get_admin_content_badges_keyboard():
    """Keyboard for badge management options."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="➕ Crear Insignia", callback_data="admin_create_badge"
                )
            ],
            [
                InlineKeyboardButton(
                    text="👁 Ver Insignias", callback_data="admin_view_badges"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🗑 Eliminar Insignia", callback_data="admin_delete_badge"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Volver", callback_data="admin_manage_content"
                )
            ],
        ]
    )
    return keyboard


def get_admin_content_levels_keyboard():
    """Keyboard for level management options."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Añadir Nivel", callback_data="admin_level_add")
            ],
            [
                InlineKeyboardButton(text="📝 Editar Nivel", callback_data="admin_level_edit")
            ],
            [
                InlineKeyboardButton(text="🗑 Eliminar Nivel", callback_data="admin_level_delete")
            ],
            [
                InlineKeyboardButton(text="📋 Ver Niveles", callback_data="admin_levels_view")
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Volver", callback_data="admin_manage_content"
                )
            ],
        ]
    )
    return keyboard


def get_admin_content_rewards_keyboard():
    """Keyboard for reward catalogue management options."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Añadir Recompensa", callback_data="admin_reward_add")
            ],
            [
                InlineKeyboardButton(text="🗑️ Eliminar Recompensa", callback_data="admin_reward_delete")
            ],
            [
                InlineKeyboardButton(text="📝 Editar Recompensa", callback_data="admin_reward_edit")
            ],
            [
                InlineKeyboardButton(text="📋 Ver Recompensas", callback_data="admin_reward_view")
            ],
            [
                InlineKeyboardButton(text="⬅️ Volver", callback_data="admin_manage_content")
            ],
        ]
    )
    return keyboard


def get_admin_content_auctions_keyboard():
    """Keyboard for auction management options."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🏛️ Gestionar Subastas", callback_data="admin_auction_main"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📊 Estadísticas", callback_data="admin_auction_stats"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Volver", callback_data="admin_manage_content"
                )
            ],
        ]
    )
    return keyboard


def get_admin_content_daily_gifts_keyboard():
    """Keyboard for daily gift configuration options."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Botón de prueba", callback_data="admin_game_test"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Volver", callback_data="admin_manage_content"
                )
            ],
        ]
    )
    return keyboard


def get_admin_content_minigames_keyboard():
    """Keyboard placeholder for minigames options."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Botón de prueba", callback_data="admin_game_test"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Volver", callback_data="admin_manage_content"
                )
            ],
        ]
    )
    return keyboard


def get_root_menu():
    """Returns the inline keyboard for the root menu."""
    keyboard = [
        [
            InlineKeyboardButton(text="🏆 Mi Perfil", callback_data="menu:profile"),
            InlineKeyboardButton(text="🎯 Misiones", callback_data="menu:missions")
        ],
        [
            InlineKeyboardButton(text="🎁 Recompensas", callback_data="menu:rewards"),
            InlineKeyboardButton(text="👑 Ranking", callback_data="menu:ranking")
        ],
        [InlineKeyboardButton(text="🏛️ Subastas", callback_data="auction_main")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_parent_menu(parent_name: str):
    """Returns the keyboard for a parent menu based on its name."""
    if parent_name == "profile":
        return get_profile_keyboard()
    elif parent_name == "missions":
        return get_missions_keyboard([])
    elif parent_name == "rewards":
        return get_reward_keyboard([], set())
    elif parent_name == "ranking":
        return get_ranking_keyboard()
    else:
        return get_root_menu()


def get_child_menu(menu_name: str):
    """Returns the keyboard for a child menu based on its name."""
    if menu_name == "profile":
        return get_profile_keyboard()
    elif menu_name == "missions":
        return get_missions_keyboard([])
    elif menu_name == "rewards":
        return get_reward_keyboard([], set())
    elif menu_name == "ranking":
        return get_ranking_keyboard()
    else:
        return get_root_menu()


def get_main_reply_keyboard():
    """
    Returns the main ReplyKeyboardMarkup with persistent buttons.
    """
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏆 Mi Perfil"), KeyboardButton(text="🎯 Misiones")],
            [KeyboardButton(text="🎁 Recompensas"), KeyboardButton(text="🏛️ Subastas")],
            [KeyboardButton(text="👑 Ranking")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
    return keyboard


def get_back_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    """Return a simple keyboard with a single back button."""
    keyboard = [[InlineKeyboardButton(text="🔙 Volver", callback_data=callback_data)]]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_post_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Keyboard used to confirm publishing a channel post."""
    keyboard = [
        [InlineKeyboardButton(text="✅ Publicar", callback_data="confirm_channel_post")],
        [InlineKeyboardButton(text="🔙 Volver", callback_data="admin_vip")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_reward_type_keyboard() -> InlineKeyboardMarkup:
    """Keyboard to select reward type."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🏅 Insignia", callback_data="reward_type_badge")],
            [InlineKeyboardButton(text="📁 Archivo", callback_data="reward_type_file")],
            [InlineKeyboardButton(text="🔓 Acceso", callback_data="reward_type_access")],
        ]
    )
    return keyboard


def get_mission_completed_keyboard() -> InlineKeyboardMarkup:
    """Keyboard shown after completing a mission."""
    keyboard = [
        [
            InlineKeyboardButton(
                text=BOT_MESSAGES["view_all_missions_button_text"],
                callback_data="menu:missions",
            )
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_users_list_keyboard(
    users: list[User], offset: int, total_count: int, limit: int = 5
) -> InlineKeyboardMarkup:
    """Return a keyboard for the paginated list of users with action buttons."""
    keyboard: list[list[InlineKeyboardButton]] = []

    for user in users:
        keyboard.append(
            [
                InlineKeyboardButton(
                    text="➕", callback_data=f"admin_user_add_{user.id}"
                ),
                InlineKeyboardButton(
                    text="➖", callback_data=f"admin_user_deduct_{user.id}"
                ),
                InlineKeyboardButton(
                    text="👁", callback_data=f"admin_user_view_{user.id}"
                ),
            ]
        )

    nav_buttons: list[InlineKeyboardButton] = []
    if offset > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="⬅️", callback_data=f"admin_users_page_{offset - limit}"
            )
        )
    if offset + limit < total_count:
        nav_buttons.append(
            InlineKeyboardButton(
                text="➡️", callback_data=f"admin_users_page_{offset + limit}"
            )
        )
    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append(
        [InlineKeyboardButton(text="🔙 Volver", callback_data="admin_main_menu")]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_badge_selection_keyboard(badges: list) -> InlineKeyboardMarkup:
    rows = []
    for b in badges:
        label = f"{b.emoji or ''} {b.name}".strip()
        rows.append(
            [InlineKeyboardButton(text=label, callback_data=f"select_badge_{b.id}")]
        )
    rows.append(
        [InlineKeyboardButton(text="🔙 Volver", callback_data="admin_content_badges")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)
    
