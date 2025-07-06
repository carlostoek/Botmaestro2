# services/narrative/memory_system.py
"""
Sistema de memorias compartidas y callbacks narrativos.
Gestiona las referencias a momentos pasados y su impacto en la narrativa.
"""

from typing import List, Optional, Dict
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, or_, func

from database.narrative_models import (
    DialogueMemory, NarrativeState, UserArchetype
)
from database.models import User

class MemoryCallbackSystem:
    """Gestiona las memorias y sus referencias en conversaciones futuras"""
    
    def __init__(self):
        self.memory_weights = {
            "vulnerability": 1.0,
            "understanding": 0.8,
            "conflict": 0.6,
            "breakthrough": 1.2,
            "boundary_respect": 0.9,
            "shared_secret": 1.1,
        }
        
        self.callback_cooldown = timedelta(hours=12)  # Tiempo mÃ­nimo entre referencias
    
    async def find_relevant_memory(
        self,
        session: AsyncSession,
        user_id: int,
        current_context: Dict,
        memory_type: Optional[str] = None
    ) -> Optional[DialogueMemory]:
        """Encuentra una memoria relevante para el contexto actual"""
        
        # Query base
        query = select(DialogueMemory).filter(
            and_(
                DialogueMemory.user_id == user_id,
                DialogueMemory.can_be_referenced == True,
                DialogueMemory.times_referenced < 5  # LÃ­mite de referencias
            )
        )
        
        # Filtrar por tipo si se especifica
        if memory_type:
            query = query.filter(DialogueMemory.memory_type == memory_type)
        
        # Evitar memorias referenciadas recientemente
        cooldown_time = datetime.utcnow() - self.callback_cooldown
        query = query.filter(
            or_(
                DialogueMemory.last_referenced == None,
                DialogueMemory.last_referenced < cooldown_time
            )
        )
        
        result = await session.execute(query)
        memories = result.scalars().all()
        
        if not memories:
            return None
        
        # Calcular relevancia de cada memoria
        scored_memories = []
        for memory in memories:
            score = self._calculate_memory_relevance(memory, current_context)
            scored_memories.append((score, memory))
        
        # Ordenar por relevancia y seleccionar la mejor
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        
        if scored_memories and scored_memories[0][0] > 0.5:  # Umbral de relevancia
            return scored_memories[0][1]
        
        return None
    
    def _calculate_memory_relevance(
        self,
        memory: DialogueMemory,
        current_context: Dict
    ) -> float:
        """Calcula quÃ© tan relevante es una memoria para el contexto actual"""
        
        relevance = 0.0
        
        # Peso base por tipo de memoria
        relevance += self.memory_weights.get(memory.memory_type, 0.5)
        
        # Bonus por memorias breakthrough
        if memory.is_breakthrough_moment:
            relevance += 0.3
        
        # Ajustar por contexto emocional similar
        if current_context.get("emotional_tone") == memory.emotional_context:
            relevance += 0.4
        
        # Penalizar memorias muy referenciadas
        relevance -= (memory.times_referenced * 0.2)
        
        # Bonus por tiempo transcurrido (memorias mÃ¡s antiguas pueden ser nostÃ¡lgicas)
        days_ago = (datetime.utcnow() - memory.created_at).days
        if days_ago > 7:
            relevance += 0.2
        
        return max(0.0, min(1.0, relevance))  # Clamp entre 0 y 1
    
    async def create_memory(
        self,
        session: AsyncSession,
        user_id: int,
        memory_type: str,
        user_message: str,
        diana_response: str,
        context: Dict,
        emotional_impact: Dict
    ) -> DialogueMemory:
        """Crea una nueva memoria significativa"""
        
        memory = DialogueMemory(
            user_id=user_id,
            memory_type=memory_type,
            chapter=context.get("chapter", "unknown"),
            emotional_context=context.get("emotional_tone", "neutral"),
            trigger_context=context.get("trigger", "conversation"),
            user_message=user_message[:1000],  # Limitar longitud
            diana_response=diana_response[:1000],
            trust_impact=emotional_impact.get("trust", 0.0),
            vulnerability_impact=emotional_impact.get("vulnerability", 0.0),
            relationship_impact=emotional_impact.get("relationship", 0.0),
            is_breakthrough_moment=emotional_impact.get("is_breakthrough", False),
            unlocked_new_responses=context.get("unlocked_responses", [])
        )
        
        session.add(memory)
        await session.commit()
        
        return memory
    
    async def reference_memory(
        self,
        session: AsyncSession,
        memory: DialogueMemory
    ) -> str:
        """Genera una referencia a una memoria y actualiza su uso"""
        
        # Actualizar contadores
        memory.times_referenced += 1
        memory.last_referenced = datetime.utcnow()
        await session.commit()
        
        # Generar referencia contextual
        return self._generate_memory_reference(memory)
    
    def _generate_memory_reference(self, memory: DialogueMemory) -> str:
        """Genera el texto de referencia para una memoria"""
        
        references = {
            "vulnerability": {
                "first_time": [
                    f"Recuerdo cuando me confiaste que {self._extract_key_phrase(memory.user_message)}...",
                    f"AÃºn pienso en lo que compartiste sobre {self._extract_topic(memory.user_message)}...",
                ],
                "repeated": [
                    "Como aquella vez que fuiste tan honesto conmigo...",
                    "Me recuerda a esa conversaciÃ³n donde bajaste la guardia...",
                ],
            },
            "understanding": {
                "first_time": [
                    f"Como cuando entendiste que {self._extract_key_phrase(memory.diana_response)}...",
                    "Ese momento cuando simplemente... supiste lo que necesitaba escuchar...",
                ],
                "repeated": [
                    "Igual que aquella vez que no necesitÃ© explicar todo...",
                    "Como cuando demostraste esa comprensiÃ³n Ãºnica...",
                ],
            },
            "boundary_respect": {
                "first_time": [
                    "Cuando respetaste mi necesidad de espacio sin alejarte...",
                    f"Recuerdo cÃ³mo entendiste que {self._extract_boundary(memory)}...",
                ],
                "repeated": [
                    "Como siempre has sabido respetar mis lÃ­mites...",
                    "Tu forma de estar cerca sin invadir...",
                ],
            },
            "breakthrough": {
                "first_time": [
                    "Ese momento que cambiÃ³ algo entre nosotros...",
                    f"Cuando {self._extract_breakthrough_moment(memory)}...",
                ],
                "repeated": [
                    "Aquel punto de inflexiÃ³n en nuestra relaciÃ³n...",
                    "Ese instante que lo cambiÃ³ todo...",
                ],
            },
        }
        
        memory_refs = references.get(memory.memory_type, {})
        
        if memory.times_referenced == 0:
            options = memory_refs.get("first_time", ["Recuerdo ese momento especial..."])
        else:
            options = memory_refs.get("repeated", ["Como aquella vez..."])
        
        return random.choice(options)
    
    def _extract_key_phrase(self, text: str) -> str:
        """Extrae una frase clave del texto"""
        # Simplificado - en producciÃ³n usarÃ­a NLP
        words = text.split()[:10]
        return " ".join(words).lower().rstrip(".,!?") + "..."
    
    def _extract_topic(self, text: str) -> str:
        """Extrae el tema principal del texto"""
        # Buscar palabras clave comunes
        topics = {
            "miedo": ["miedo", "temo", "asusta", "temor"],
            "amor": ["amor", "quiero", "siento", "corazÃ³n"],
            "pasado": ["pasado", "antes", "recuerdo", "historia"],
            "futuro": ["futuro", "serÃ¡", "espero", "algÃºn dÃ­a"],
            "soledad": ["solo", "soledad", "aislado", "vacÃ­o"],
        }
        
        text_lower = text.lower()
        for topic, keywords in topics.items():
            if any(keyword in text_lower for keyword in keywords):
                return topic
        
        return "eso"
    
    def _extract_boundary(self, memory: DialogueMemory) -> str:
        """Extrae informaciÃ³n sobre el lÃ­mite respetado"""
        if "espacio" in memory.user_message.lower():
            return "necesitaba espacio para procesar"
        elif "tiempo" in memory.user_message.lower():
            return "necesitaba tiempo"
        else:
            return "tenÃ­a mis razones para mantener distancia"
    
    def _extract_breakthrough_moment(self, memory: DialogueMemory) -> str:
        """Extrae la esencia del momento breakthrough"""
        if memory.vulnerability_impact > 0.5:
            return "ambos nos permitimos ser vulnerables"
        elif memory.trust_impact > 0.5:
            return "la confianza se volviÃ³ mutua"
        else:
            return "algo cambiÃ³ entre nosotros"

    async def get_shared_memories_summary(
        self,
        session: AsyncSession,
        user_id: int
    ) -> Dict:
        """Obtiene un resumen de las memorias compartidas"""
        
        result = await session.execute(
            select(
                DialogueMemory.memory_type,
                func.count(DialogueMemory.id).label('count'),
                func.avg(DialogueMemory.trust_impact).label('avg_trust_impact')
            )
            .filter(DialogueMemory.user_id == user_id)
            .group_by(DialogueMemory.memory_type)
        )
        
        summary = {
            "total_memories": 0,
            "by_type": {},
            "breakthrough_moments": 0,
            "average_trust_impact": 0.0,
            "most_impactful": None,
        }
        
        for row in result:
            summary["total_memories"] += row.count
            summary["by_type"][row.memory_type] = {
                "count": row.count,
                "avg_trust_impact": float(row.avg_trust_impact or 0)
            }
        
        # Contar breakthrough moments
        breakthrough_result = await session.execute(
            select(func.count(DialogueMemory.id))
            .filter(
                DialogueMemory.user_id == user_id,
                DialogueMemory.is_breakthrough_moment == True
            )
        )
        summary["breakthrough_moments"] = breakthrough_result.scalar() or 0
        
        # Encontrar la memoria mÃ¡s impactante
        most_impactful_result = await session.execute(
            select(DialogueMemory)
            .filter(DialogueMemory.user_id == user_id)
            .order_by(
                (DialogueMemory.trust_impact + 
                 DialogueMemory.vulnerability_impact + 
                 DialogueMemory.relationship_impact).desc()
            )
            .limit(1)
        )
        
        most_impactful = most_impactful_result.scalar_one_or_none()
        if most_impactful:
            summary["most_impactful"] = {
                "type": most_impactful.memory_type,
                "created_at": most_impactful.created_at.isoformat(),
                "total_impact": float(
                    most_impactful.trust_impact + 
                    most_impactful.vulnerability_impact + 
                    most_impactful.relationship_impact
                )
            }
        
        return summary
