from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from services.narrative_loader import NarrativeLoader
from utils.admin_check import is_admin

router = Router()

@router.message(Command("load_narrative"))
async def load_narrative_command(message: Message, session: AsyncSession):
    """Carga fragmentos narrativos desde la carpeta 'narrative_fragments'"""
    # Solo permitir a administradores
    if not await is_admin(message.from_user.id):
        return await message.answer("❌ Solo los administradores pueden usar este comando.")
    
    loader = NarrativeLoader(session)
    try:
        await loader.load_fragments_from_directory("narrative_fragments")
        await message.answer("✅ Fragmentos narrativos cargados exitosamente!")
    except Exception as e:
        await message.answer(f"❌ Error cargando fragmentos: {str(e)}")

@router.message(Command("load_fragment"))
async def load_fragment_command(message: Message, session: AsyncSession, state: FSMContext):
    """Inicia el proceso para cargar un fragmento específico"""
    if not await is_admin(message.from_user.id):
        return await message.answer("❌ Solo los administradores pueden usar este comando.")
    
    await message.answer(
        "📤 Por favor, envíame el archivo JSON del fragmento narrativo.\n\n"
        "⚠️ Asegúrate de que el archivo tenga la estructura correcta."
    )
    await state.set_state("waiting_for_narrative_file")

@router.message(F.document, F.state == "waiting_for_narrative_file")
async def handle_narrative_file(message: Message, session: AsyncSession, state: FSMContext, bot: Bot):
    """Procesa un archivo JSON de fragmento narrativo"""
    if not message.document:
        return await message.answer("❌ No se detectó ningún documento. Intenta de nuevo.")
    
    if not message.document.file_name.endswith('.json'):
        return await message.answer("❌ El archivo debe ser un JSON (.json).")
    
    # Descargar el archivo
    file_id = message.document.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    
    # Crear directorio temporal si no existe
    os.makedirs("temp_narrative", exist_ok=True)
    temp_path = f"temp_narrative/{file_id}.json"
    
    await bot.download_file(file_path, temp_path)
    
    # Cargar el fragmento
    loader = NarrativeLoader(session)
    try:
        await loader.load_fragment_from_file(temp_path)
        await message.answer(f"✅ Fragmento cargado exitosamente!")
    except Exception as e:
        await message.answer(f"❌ Error cargando fragmento: {str(e)}")
    finally:
        # Limpiar estado y archivo temporal
        await state.clear()
        if os.path.exists(temp_path):
            os.remove(temp_path)
          
