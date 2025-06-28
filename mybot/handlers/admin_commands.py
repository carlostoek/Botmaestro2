# mybot/handlers/admin_commands.py

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy import select
from database.models import LorePiece, UserLorePiece, User
from database import get_session
from backpack import desbloquear_pista_narrativa
import random
from datetime import datetime

router = Router()

# Pistas de prueba predefinidas
TEST_HINTS = [
    {
        "code_name": "TEST_MEMORIA_01",
        "title": "Primera Memoria",
        "description": "Diana te susurra un recuerdo íntimo del pasado...",
        "content": "🌙 *En las noches de luna llena, Diana solía escribir cartas que nunca envió. Esta es una de ellas...*",
        "content_type": "text",
        "category": "memorias",
        "rarity": "common"
    },
    {
        "code_name": "TEST_FRAGMENTO_01", 
        "title": "Fragmento del Mapa Perdido",
        "description": "Una pieza del camino hacia el corazón de Diana",
        "content": "🗺️ *Este fragmento muestra un sendero oculto que lleva a un jardín secreto donde Diana guarda sus tesoros más preciados.*",
        "content_type": "text",
        "category": "fragmentos",
        "rarity": "rare"
    },
    {
        "code_name": "TEST_SECRETO_01",
        "title": "Secreto del Diván",
        "description": "Una verdad íntima que Diana ha decidido compartir contigo",
        "content": "🔮 *El Diván no es solo un lugar... es un estado del alma. Solo quienes comprenden esto pueden acceder a sus misterios más profundos.*",
        "content_type": "text", 
        "category": "secretos",
        "rarity": "legendary"
    },
    {
        "code_name": "TEST_LLAVE_01",
        "title": "Llave de Cristal",
        "description": "Una llave que abre puertas que no sabías que existían",
        "content": "🗝️ *Esta llave de cristal vibra con energía cuando te acercas a secretos ocultos. Diana la creó especialmente para ti.*",
        "content_type": "text",
        "category": "llaves", 
        "rarity": "epic"
    }
]

@router.message(Command("test_hint"))
async def cmd_test_hint(message: Message):
    """Comando para generar pista de prueba - Solo admins"""
    user_id = message.from_user.id
    
    # Verificar si es admin (ajusta según tu sistema)
    ADMIN_IDS = [1280444712]  # Reemplaza con IDs de admins
    if user_id not in ADMIN_IDS:
        await message.answer("❌ Solo administradores pueden usar este comando")
        return
    
    # Obtener usuario objetivo del comando
    args = message.text.split()
    if len(args) > 1:
        try:
            target_user_id = int(args[1])
        except ValueError:
            await message.answer("❌ ID de usuairio inválido")
            return
    else:
        target_user_id = user_id
    
    session_factory = await get_session()
    async with session_factory() as session:
        # Verificar que el usuario objetivo existe
        user_result = await session.execute(
            select(User).where(User.id == target_user_id)
        )
        target_user = user_result.scalar_one_or_none()
        
        if not target_user:
            await message.answer(f"❌ Usuario {target_user_id} no encontrado")
            return
        
        # Seleccionar pista aleatoria
        test_hint = random.choice(TEST_HINTS)
        
        # Verificar si la pista ya existe en BD
        existing_hint = await session.execute(
            select(LorePiece).where(LorePiece.code_name == test_hint["code_name"])
        )
        lore_piece = existing_hint.scalar_one_or_none()
        
        # Crear pista si no existe
        if not lore_piece:
            lore_piece = LorePiece(
                code_name=test_hint["code_name"],
                title=test_hint["title"],
                description=test_hint["description"],
                content=test_hint["content"],
                content_type=test_hint["content_type"],
                category=test_hint["category"],
                rarity=test_hint["rarity"]
            )
            session.add(lore_piece)
            await session.flush()  # Para obtener el ID
        
        # Verificar si el usuario ya tiene esta pista
        existing_user_hint = await session.execute(
            select(UserLorePiece).where(
                UserLorePiece.user_id == target_user_id,
                UserLorePiece.lore_piece_id == lore_piece.id
            )
        )
        
        if existing_user_hint.scalar_one_or_none():
            await message.answer(f"⚠️ Usuario ya posee la pista: {test_hint['title']}")
            return
        
        # Crear relación usuario-pista
        user_lore_piece = UserLorePiece(
            user_id=target_user_id,
            lore_piece_id=lore_piece.id,
            unlocked_at=datetime.now(),
            context={
                "source": "admin_test",
                "granted_by": user_id,
                "test_hint": True
            }
        )
        
        session.add(user_lore_piece)
        await session.commit()
        
        # Confirmar creación
        rarity_emoji = {
            "common": "⚪",
            "rare": "🔵", 
            "epic": "🟣",
            "legendary": "🟡"
        }
        
        emoji = rarity_emoji.get(test_hint["rarity"], "⚪")
        
        await message.answer(
            f"✅ **Pista de prueba creada**\n\n"
            f"{emoji} **{test_hint['title']}**\n"
            f"📂 Categoría: {test_hint['category']}\n"
            f"👤 Usuario: {target_user_id}\n"
            f"🎯 Código: `{test_hint['code_name']}`\n\n"
            f"*El usuario puede verificar su mochila con* 🎒 Mochila",
            parse_mode="Markdown"
        )

@router.message(Command("test_clear_hints"))  
async def cmd_clear_test_hints(message: Message):
    """Limpiar todas las pistas de prueba de un usuario"""
    user_id = message.from_user.id
    
    # Solo admins
    ADMIN_IDS = [1280444712]
    if user_id not in ADMIN_IDS:
        await message.answer("❌ Solo administradores")
        return
    
    args = message.text.split()
    target_user_id = int(args[1]) if len(args) > 1 else user_id
    
    session_factory = await get_session()
    async with session_factory() as session:
        # Eliminar pistas de prueba
        test_codes = [hint["code_name"] for hint in TEST_HINTS]
        
        result = await session.execute(
            select(UserLorePiece)
            .join(LorePiece)
            .where(
                UserLorePiece.user_id == target_user_id,
                LorePiece.code_name.in_(test_codes)
            )
        )
        
        user_hints = result.scalars().all()
        count = len(user_hints)
        
        for user_hint in user_hints:
            await session.delete(user_hint)
        
        await session.commit()
        
        await message.answer(f"🗑️ Eliminadas {count} pistas de prueba del usuario {target_user_id}")

@router.message(Command("test_all_hints"))
async def cmd_test_all_hints(message: Message):
    """Generar todas las pistas de prueba para un usuario"""
    user_id = message.from_user.id
    
    ADMIN_IDS = [1280444712]
    if user_id not in ADMIN_IDS:
        await message.answer("❌ Solo administradores")
        return
    
    args = message.text.split()
    target_user_id = int(args[1]) if len(args) > 1 else user_id
    
    session_factory = await get_session()
    async with session_factory() as session:
        created_count = 0
        
        for test_hint in TEST_HINTS:
            # Verificar/crear pista en BD
            existing_hint = await session.execute(
                select(LorePiece).where(LorePiece.code_name == test_hint["code_name"])
            )
            lore_piece = existing_hint.scalar_one_or_none()
            
            if not lore_piece:
                lore_piece = LorePiece(**test_hint)
                session.add(lore_piece)
                await session.flush()
            
            # Verificar si usuario ya la tiene
            existing_user_hint = await session.execute(
                select(UserLorePiece).where(
                    UserLorePiece.user_id == target_user_id,
                    UserLorePiece.lore_piece_id == lore_piece.id
                )
            )
            
            if not existing_user_hint.scalar_one_or_none():
                user_lore_piece = UserLorePiece(
                    user_id=target_user_id,
                    lore_piece_id=lore_piece.id,
                    unlocked_at=datetime.now(),
                    context={"source": "admin_test_all", "granted_by": user_id}
                )
                session.add(user_lore_piece)
                created_count += 1
        
        await session.commit()
        
        await message.answer(
            f"✅ **Pistas de prueba generadas**\n\n"
            f"📦 Total creadas: {created_count}\n" 
            f"👤 Usuario: {target_user_id}\n\n"
            f"*Usa* 🎒 Mochila *para verificar*"
        )
