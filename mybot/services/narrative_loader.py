import json
import os
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from database.models.narrative import NarrativeFragment
from sqlalchemy import select

logger = logging.getLogger(__name__)

class NarrativeLoader:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def load_fragments_from_directory(self, directory_path: str):
        """Carga todos los fragmentos JSON de un directorio a la base de datos"""
        for filename in os.listdir(directory_path):
            if filename.endswith('.json'):
                filepath = os.path.join(directory_path, filename)
                await self.load_fragment_from_file(filepath)
    
    async def load_fragment_from_file(self, filepath: str):
        """Carga un fragmento desde un archivo JSON"""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                fragment_data = json.load(file)
                await self.upsert_fragment(fragment_data)
                logger.info(f"Fragmento cargado: {fragment_data['fragment_id']}")
        except Exception as e:
            logger.error(f"Error cargando fragmento desde {filepath}: {str(e)}")
    
    async def upsert_fragment(self, fragment_data: dict):
        """Inserta o actualiza un fragmento narrativo en la base de datos"""
        # Verificar si el fragmento ya existe
        result = await self.session.execute(
            select(NarrativeFragment).filter_by(fragment_id=fragment_data['fragment_id'])
        )
        fragment = result.scalars().first()
        
        if fragment:
            # Actualizar el fragmento existente
            fragment.content = fragment_data['content']
            fragment.level = fragment_data.get('level', 1)
            fragment.required_besitos = fragment_data.get('required_besitos', 0)
            fragment.required_item_id = fragment_data.get('required_item_id')
            fragment.unlock_conditions = fragment_data.get('unlock_conditions')
            fragment.decisions = fragment_data['decisions']
        else:
            # Crear un nuevo fragmento
            fragment = NarrativeFragment(
                fragment_id=fragment_data['fragment_id'],
                content=fragment_data['content'],
                level=fragment_data.get('level', 1),
                required_besitos=fragment_data.get('required_besitos', 0),
                required_item_id=fragment_data.get('required_item_id'),
                unlock_conditions=fragment_data.get('unlock_conditions'),
                decisions=fragment_data['decisions']
            )
            self.session.add(fragment)
        
        await self.session.commit()
      
