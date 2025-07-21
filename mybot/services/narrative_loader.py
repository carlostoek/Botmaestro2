"""
Cargador de contenido narrativo desde archivos JSON.
Permite cargar y actualizar fragmentos narrativos fácilmente.
"""
import json
import os
import logging
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.narrative_models import StoryFragment, NarrativeChoice
from datetime import datetime

logger = logging.getLogger(__name__)

class NarrativeLoader:
    """Cargador de fragmentos narrativos desde archivos JSON."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def load_fragments_from_directory(self, directory_path: str = "mybot/narrative_fragments"):
        """Carga todos los fragmentos JSON de un directorio."""
        if not os.path.exists(directory_path):
            logger.warning(f"Directorio de narrativa no encontrado: {directory_path}")
            return
        
        loaded_count = 0
        for filename in os.listdir(directory_path):
            if filename.endswith('.json'):
                filepath = os.path.join(directory_path, filename)
                try:
                    await self.load_fragment_from_file(filepath)
                    loaded_count += 1
                except Exception as e:
                    logger.error(f"Error cargando {filepath}: {e}")
        
        logger.info(f"Cargados {loaded_count} fragmentos narrativos")
    
    async def load_fragment_from_file(self, filepath: str):
        """Carga un fragmento desde un archivo JSON."""
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                fragment_data = json.load(file)
                await self.upsert_fragment(fragment_data)
                logger.debug(f"Fragmento cargado: {fragment_data.get('fragment_id', 'unknown')}")
        except Exception as e:
            logger.error(f"Error cargando fragmento desde {filepath}: {e}")
            raise
    
    async def upsert_fragment(self, fragment_data: Dict[str, Any]):
        """Inserta o actualiza un fragmento narrativo."""
        fragment_id = fragment_data.get('fragment_id')
        if not fragment_id:
            logger.error("Fragmento sin fragment_id, saltando")
            return
        
        # Buscar fragmento existente
        stmt = select(StoryFragment).where(StoryFragment.key == fragment_id)
        result = await self.session.execute(stmt)
        fragment = result.scalar_one_or_none()
        
        if fragment:
            # Actualizar fragmento existente
            await self._update_fragment(fragment, fragment_data)
        else:
            # Crear nuevo fragmento
            fragment = await self._create_fragment(fragment_data)
        
        # Procesar decisiones
        await self._process_fragment_decisions(fragment, fragment_data.get('decisions', []))
    
    async def _create_fragment(self, data: Dict[str, Any]) -> StoryFragment:
        """Crea un nuevo fragmento narrativo."""
        fragment = StoryFragment(
            key=data['fragment_id'],
            text=data['content'],
            character=data.get('character', 'Lucien'),
            level=data.get('level', 1),
            min_besitos=data.get('required_besitos', 0),
            required_role=data.get('required_role'),
            reward_besitos=data.get('reward_besitos', 0),
            unlocks_achievement_id=data.get('unlocks_achievement_id')
        )
        
        self.session.add(fragment)
        await self.session.commit()
        await self.session.refresh(fragment)
        
        logger.info(f"Fragmento creado: {fragment.key}")
        return fragment
    
    async def _update_fragment(self, fragment: StoryFragment, data: Dict[str, Any]):
        """Actualiza un fragmento existente."""
        fragment.text = data['content']
        fragment.character = data.get('character', 'Lucien')
        fragment.level = data.get('level', 1)
        fragment.min_besitos = data.get('required_besitos', 0)
        fragment.required_role = data.get('required_role')
        fragment.reward_besitos = data.get('reward_besitos', 0)
        fragment.unlocks_achievement_id = data.get('unlocks_achievement_id')
        
        await self.session.commit()
        logger.info(f"Fragmento actualizado: {fragment.key}")
    
    async def _process_fragment_decisions(self, fragment: StoryFragment, decisions: List[Dict[str, Any]]):
        """Procesa las decisiones de un fragmento."""
        # Eliminar decisiones existentes
        stmt = select(NarrativeChoice).where(NarrativeChoice.source_fragment_id == fragment.id)
        result = await self.session.execute(stmt)
        existing_choices = result.scalars().all()
        
        for choice in existing_choices:
            await self.session.delete(choice)
        
        # Crear nuevas decisiones
        for decision in decisions:
            next_fragment_key = decision.get('next_fragment')
            if not next_fragment_key:
                continue
            
            # Buscar fragmento de destino
            dest_stmt = select(StoryFragment).where(StoryFragment.key == next_fragment_key)
            dest_result = await self.session.execute(dest_stmt)
            dest_fragment = dest_result.scalar_one_or_none()
            
            if not dest_fragment:
                logger.warning(f"Fragmento de destino no encontrado: {next_fragment_key}")
                continue
            
            choice = NarrativeChoice(
                source_fragment_id=fragment.id,
                destination_fragment_id=dest_fragment.id,
                text=decision['text']
            )
            self.session.add(choice)
        
        await self.session.commit()
    
    async def load_default_narrative(self):
        """Carga la narrativa por defecto si no existe contenido."""
        # Verificar si ya hay fragmentos
        stmt = select(StoryFragment)
        result = await self.session.execute(stmt)
        existing = result.scalars().first()
        
        if existing:
            logger.info("Ya existen fragmentos narrativos, saltando carga por defecto")
            return
        
        # Cargar narrativa básica
        default_fragments = [
            {
                "fragment_id": "START",
                "content": "🎩 **Lucien:** Bienvenido, viajero. Soy Lucien, el mayordomo de esta mansión. Diana te esperaba... ¿Estás listo para comenzar tu historia?",
                "character": "Lucien",
                "level": 1,
                "required_besitos": 0,
                "reward_besitos": 5,
                "decisions": [
                    {
                        "text": "Estoy listo para comenzar",
                        "next_fragment": "INTRO_1"
                    },
                    {
                        "text": "Necesito saber más primero",
                        "next_fragment": "INFO_1"
                    }
                ]
            },
            {
                "fragment_id": "INTRO_1",
                "content": "🎩 **Lucien:** Excelente. La primera regla de esta casa es simple: cada acción tiene consecuencias, cada decisión abre o cierra puertas. Tus 'besitos' son la moneda de este lugar.",
                "character": "Lucien",
                "level": 1,
                "required_besitos": 0,
                "reward_besitos": 10,
                "decisions": [
                    {
                        "text": "Entiendo. ¿Qué sigue?",
                        "next_fragment": "DIANA_HINT_1"
                    }
                ]
            },
            {
                "fragment_id": "INFO_1",
                "content": "🎩 **Lucien:** Sabio. La prudencia es una virtud aquí. Esta mansión guarda secretos, y Diana... bueno, ella es el mayor de todos. Pero no temas, yo seré tu guía.",
                "character": "Lucien",
                "level": 1,
                "required_besitos": 0,
                "reward_besitos": 5,
                "decisions": [
                    {
                        "text": "Ahora estoy listo",
                        "next_fragment": "INTRO_1"
                    }
                ]
            },
            {
                "fragment_id": "DIANA_HINT_1",
                "content": "🌸 **Diana:** *Una voz suave resuena en tu mente...* Así que has llegado hasta aquí. Lucien habla bien de ti. Pero las palabras son solo el comienzo... ¿Qué es lo que realmente buscas?",
                "character": "Diana",
                "level": 2,
                "required_besitos": 15,
                "reward_besitos": 15,
                "decisions": [
                    {
                        "text": "Te busco a ti",
                        "next_fragment": "DIANA_RESPONSE_1"
                    },
                    {
                        "text": "Busco respuestas",
                        "next_fragment": "DIANA_RESPONSE_2"
                    }
                ]
            },
            {
                "fragment_id": "DIANA_RESPONSE_1",
                "content": "🌸 **Diana:** *Sonríe con misterio...* Muchos me buscan, pocos me encuentran. Pero hay algo en ti... algo diferente. Sigue el camino que Lucien te muestre, y quizás... solo quizás, nos encontremos de verdad.",
                "character": "Diana",
                "level": 2,
                "required_besitos": 15,
                "reward_besitos": 20,
                "decisions": []
            },
            {
                "fragment_id": "DIANA_RESPONSE_2",
                "content": "🌸 **Diana:** Las respuestas... *ríe suavemente* Las respuestas son solo el principio. La verdad se construye, no se encuentra. Y requiere... sacrificios. ¿Estás dispuesto a pagar el precio?",
                "character": "Diana",
                "level": 2,
                "required_besitos": 15,
                "reward_besitos": 20,
                "decisions": []
            }
        ]
        
        for fragment_data in default_fragments:
            await self.upsert_fragment(fragment_data)
        
        logger.info("Narrativa por defecto cargada exitosamente")
