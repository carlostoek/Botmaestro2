"""
Handlers administrativos para gestión de narrativa.
Permite a los admins cargar, editar y gestionar contenido narrativo.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, Document
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession
import os
import json
import tempfile

from services.narrative_loader import NarrativeLoader
from utils.user_roles import is_admin
from utils.message_safety import safe_answer, safe_edit

router = Router()

class NarrativeAdminStates(StatesGroup):
    waiting_for_narrative_file = State()
    waiting_for_fragment_json = State()

@router.message(Command("load_narrative"))
async def load_narrative_command(message: Message, session: AsyncSession):
    """Carga fragmentos narrativos desde la carpeta narrative_fragments."""
    if not await is_admin(message.from_user.id, session):
        await safe_answer(message, "❌ Solo los administradores pueden usar este comando.")
        return
    
    try:
        loader = NarrativeLoader(session)
        
        # Intentar cargar desde directorio
        await loader.load_fragments_from_directory("narrative_fragments")
        
        # Si no hay archivos, cargar narrativa por defecto
        await loader.load_default_narrative()
        
        await safe_answer(message, "✅ **Narrativa Cargada**\n\nLos fragmentos narrativos han sido cargados exitosamente.")
        
    except Exception as e:
        await safe_answer(message, f"❌ **Error**: {str(e)}")

@router.message(Command("upload_narrative"))
async def upload_narrative_command(message: Message, session: AsyncSession, state: FSMContext):
    """Inicia el proceso para subir un archivo narrativo."""
    if not await is_admin(message.from_user.id, session):
        await safe_answer(message, "❌ Solo los administradores pueden usar este comando.")
        return
    
    await safe_answer(
        message,
        "📤 **Subir Narrativa**\n\n"
        "Envía un archivo JSON con el fragmento narrativo.\n\n"
        "**Formato esperado:**\n"
        "```json\n"
        "{\n"
        '  "fragment_id": "UNIQUE_ID",\n'
        '  "content": "Texto del fragmento",\n'
        '  "character": "Lucien",\n'
        '  "level": 1,\n'
        '  "required_besitos": 0,\n'
        '  "reward_besitos": 5,\n'
        '  "decisions": [\n'
        '    {\n'
        '      "text": "Opción 1",\n'
        '      "next_fragment": "NEXT_ID"\n'
        '    }\n'
        '  ]\n'
        "}\n"
        "```"
    )
    await state.set_state(NarrativeAdminStates.waiting_for_narrative_file)

@router.message(NarrativeAdminStates.waiting_for_narrative_file, F.document)
async def handle_narrative_file(message: Message, session: AsyncSession, state: FSMContext):
    """Procesa un archivo JSON de fragmento narrativo."""
    if not message.document:
        await safe_answer(message, "❌ No se detectó ningún documento.")
        return
    
    if not message.document.file_name.endswith('.json'):
        await safe_answer(message, "❌ El archivo debe ser un JSON (.json).")
        return
    
    try:
        # Descargar el archivo
        file = await message.bot.get_file(message.document.file_id)
        
        # Crear archivo temporal
        with tempfile.NamedTemporaryFile(mode='w+b', suffix='.json', delete=False) as temp_file:
            await message.bot.download_file(file.file_path, temp_file.name)
            temp_path = temp_file.name
        
        # Cargar el fragmento
        loader = NarrativeLoader(session)
        await loader.load_fragment_from_file(temp_path)
        
        await safe_answer(message, "✅ **Fragmento Cargado**\n\nEl fragmento narrativo se ha cargado exitosamente.")
        
    except json.JSONDecodeError as e:
        await safe_answer(message, f"❌ **Error de JSON**: {str(e)}")
    except Exception as e:
        await safe_answer(message, f"❌ **Error**: {str(e)}")
    finally:
        # Limpiar archivo temporal
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        await state.clear()

@router.message(Command("narrative_stats"))
async def narrative_admin_stats(message: Message, session: AsyncSession):
    """Muestra estadísticas del sistema narrativo."""
    if not await is_admin(message.from_user.id, session):
        await safe_answer(message, "❌ Solo los administradores pueden usar este comando.")
        return
    
    try:
        from sqlalchemy import select, func
        from database.narrative_models import StoryFragment, NarrativeChoice, UserNarrativeState
        
        # Contar fragmentos
        fragments_stmt = select(func.count()).select_from(StoryFragment)
        fragments_result = await session.execute(fragments_stmt)
        total_fragments = fragments_result.scalar() or 0
        
        # Contar decisiones
        choices_stmt = select(func.count()).select_from(NarrativeChoice)
        choices_result = await session.execute(choices_stmt)
        total_choices = choices_result.scalar() or 0
        
        # Contar usuarios con progreso narrativo
        users_stmt = select(func.count()).select_from(UserNarrativeState)
        users_result = await session.execute(users_stmt)
        active_users = users_result.scalar() or 0
        
        # Fragmentos por nivel
        level_stmt = select(StoryFragment.level, func.count()).select_from(StoryFragment).group_by(StoryFragment.level)
        level_result = await session.execute(level_stmt)
        level_distribution = dict(level_result.all())
        
        stats_text = f"""📊 **Estadísticas del Sistema Narrativo**

📚 **Contenido**:
• Fragmentos totales: {total_fragments}
• Decisiones totales: {total_choices}
• Usuarios activos: {active_users}

📈 **Distribución por Nivel**:"""
        
        for level in sorted(level_distribution.keys()):
            count = level_distribution[level]
            level_type = "Gratuito" if level <= 3 else "VIP"
            stats_text += f"\n• Nivel {level} ({level_type}): {count} fragmentos"
        
        await safe_answer(message, stats_text)
        
    except Exception as e:
        await safe_answer(message, f"❌ **Error**: {str(e)}")

@router.message(Command("reset_narrative"))
async def reset_user_narrative(message: Message, session: AsyncSession):
    """Reinicia la narrativa de un usuario (solo admins)."""
    if not await is_admin(message.from_user.id, session):
        await safe_answer(message, "❌ Solo los administradores pueden usar este comando.")
        return
    
    # Extraer user_id del comando
    command_parts = message.text.split()
    if len(command_parts) < 2:
        await safe_answer(
            message, 
            "❌ **Uso**: `/reset_narrative <user_id>`\n\n"
            "Ejemplo: `/reset_narrative 123456789`"
        )
        return
    
    try:
        target_user_id = int(command_parts[1])
        
        # Buscar y eliminar estado narrativo del usuario
        from database.narrative_models import UserNarrativeState
        stmt = select(UserNarrativeState).where(UserNarrativeState.user_id == target_user_id)
        result = await session.execute(stmt)
        user_state = result.scalar_one_or_none()
        
        if user_state:
            await session.delete(user_state)
            await session.commit()
            await safe_answer(message, f"✅ **Narrativa Reiniciada**\n\nLa historia del usuario {target_user_id} ha sido reiniciada.")
        else:
            await safe_answer(message, f"❌ El usuario {target_user_id} no tiene progreso narrativo.")
            
    except ValueError:
        await safe_answer(message, "❌ ID de usuario inválido.")
    except Exception as e:
        await safe_answer(message, f"❌ **Error**: {str(e)}")