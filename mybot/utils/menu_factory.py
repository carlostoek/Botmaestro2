from typing import Optional
from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.ext.asyncio import AsyncSession

async def menu_factory(
    user_id: int, 
    session: AsyncSession,
    menu_type: str = "main"
) -> Optional[InlineKeyboardMarkup]:
    """Factory para crear menús basados en el rol del usuario"""
    # Importación diferida para evitar problemas de circularidad
    from utils.user_roles import get_user_role
    
    role = await get_user_role(user_id, session)
    
    builder = InlineKeyboardBuilder()
    
    if role == "admin":
        if menu_type == "main":
            builder.button(text="Admin Panel", callback_data="admin_panel")
            builder.button(text="User Management", callback_data="user_mgmt")
    elif role == "vip":
        if menu_type == "main":
            builder.button(text="VIP Features", callback_data="vip_features")
    else:
        if menu_type == "main":
            builder.button(text="Basic Options", callback_data="basic_options")
    
    builder.adjust(1)
    return builder.as_markup()