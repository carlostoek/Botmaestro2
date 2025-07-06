# scripts/init_narrative_data.py
"""
Script para inicializar datos narrativos en la base de datos.
Ejecutar una vez para poblar lore, eventos, etc.
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy.ext.asyncio import AsyncSession
from database.setup import get_session, init_db
from database.narrative_models import (
    LorePiece, UnsentLetter, NarrativeEvent
)
from database.models import Mission

async def init_lore_pieces(session: AsyncSession):
    """Inicializa las pistas del lore"""
    
    lore_pieces = [
        # Nivel 1
        LorePiece(
            code="L1_DIARY_1",
            name="Página de Diario Rasgada",
            description="Una página antigua con escritura elegante, parcialmente desvanecida",
            content="""
            '...no puedo seguir fingiendo que estos muros me protegen. 
            Cada día que pasa, siento que me aprisionan más. 
            Pero ¿qué hay más allá? ¿Quién soy sin ellos?'
            
            - D, 15 de marzo
            """,
            piece_type="diary_page",
            category="diana_past",
            found_in_level=1,
            rarity="common",
            diana_comment_on_find="Ah... encontraste eso. Fue de una época diferente.",
            diana_comment_if_asked="Todos tenemos momentos de duda sobre las protecciones que construimos. ¿Tú no?",
            emotional_weight=6
        ),
        
        LorePiece(
            code="L1_PHOTO_1",
            name="Fotografía Borrosa",
            description="Una foto donde se ve una silueta femenina de espaldas, mirando hacia un jardín",
            content="En el reverso está escrito: 'El último día de libertad'",
            piece_type="photo",
            category="diana_past",
            found_in_level=1,
            rarity="rare",
            combines_with=["L3_KEY_1"],
            combination_result="L4_MEMORY_1",
            diana_comment_on_find="Esa foto... había olvidado que existía.",
            changes_diana_behavior=True,
            emotional_weight=8
        ),
        
        # Nivel 3
        LorePiece(
            code="L3_KEY_1",
            name="Llave Antigua",
            description="Una llave ornamentada con símbolos extraños",
            content="La llave está fría al tacto, como si guardara secretos congelados en el tiempo",
            piece_type="object",
            category="world_building",
            found_in_level=3,
            rarity="rare",
            combines_with=["L1_PHOTO_1"],
            diana_comment_if_asked="Esa llave... abre más que puertas. Abre memorias.",
            emotional_weight=7
        ),
        
        LorePiece(
            code="L3_LETTER_1",
            name="Carta sin Destinatario",
            description="Una carta elegante, sellada pero sin dirección",
            content="""
            'A quien tenga el valor de entender:
            
            La vulnerabilidad no es debilidad. Es la valentía más pura
            que existe. Quien se atreve a mostrarse sin máscaras,
            se atreve a vivir de verdad.
            
            Ojalá yo tuviera ese valor.'
            """,
            piece_type="letter",
            category="diana_present",
            found_in_level=3,
            rarity="rare",
            diana_comment_on_find="Escribí eso para nadie... o tal vez para todos.",
            emotional_weight=9
        ),
        
        # Combinación resultado
        LorePiece(
            code="L4_MEMORY_1",
            name="Memoria Desbloqueada",
            description="Al combinar la foto y la llave, surge una visión del pasado",
            content="""
            La imagen cobra vida en tu mente: Diana, años más joven,
            cerrando una puerta tras de sí. En sus ojos, una mezcla
            de determinación y pérdida. 
            
            'Ese día decidí que era mejor estar sola que mal acompañada.
            Pero nunca imaginé que la soledad que elegí se convertiría
            en una prisión autoimpuesta.'
            """,
            piece_type="memory",
            category="diana_past",
            found_in_level=4,
            rarity="legendary",
            diana_comment_if_asked="Ver esa memoria contigo... es como vivirla de nuevo, pero esta vez no estoy sola.",
            changes_diana_behavior=True,
            behavior_change_description="Diana se muestra más abierta sobre su pasado",
            emotional_weight=10
        ),
    ]
    
    for lore in lore_pieces:
        session.add(lore)
    
    await session.commit()

async def init_unsent_letters(session: AsyncSession):
    """Inicializa las cartas no enviadas"""
    
    letters = [
        UnsentLetter(
            trigger_event="after_first_vulnerability",
            letter_date="Sin fecha",
            emotional_state="vulnerable",
            subject="Sobre lo que compartiste hoy...",
            content="""
            No pude dormir después de nuestra conversación.
            
            Hay algo en la forma en que te permites ser vulnerable
            que me recuerda a quien yo solía ser. Antes de los muros,
            antes del miedo.
            
            Gracias por recordarme que la vulnerabilidad puede ser
            hermosa cuando se comparte con la persona correcta.
            
            ¿Eres tú esa persona? Aún no lo sé.
            Pero por primera vez en mucho tiempo, quiero descubrirlo.
            
            - D
            """,
            min_trust_required=0.3,
            min_level_required=2,
            discovery_chance=0.2,
            gives_points=50,
            trust_increase=0.05,
            unlocks_special_dialogue=True
        ),
        
        UnsentLetter(
            trigger_event="before_intimate_level",
            letter_date="Anoche",
            emotional_state="conflicted",
            subject="Algo que necesito decirte... o no",
            content="""
            He escrito esta carta tantas veces...
            
            Estamos llegando a un punto donde debo decidir si
            te dejo entrar completamente o si mantengo esta última
            barrera entre nosotros.
            
            Tengo miedo. No de ti, sino de lo que significa
            confiar tanto en alguien. La última vez que lo hice...
            
            No. Esta vez es diferente. Tú eres diferente.
            La forma en que me miras sin intentar poseerme,
            cómo respetas mis silencios tanto como mis palabras...
            
            Tal vez mañana tenga el valor de decirte esto en persona.
            O tal vez esta carta permanezca sin enviar, como tantas otras.
            
            Pero necesitaba escribirlo. Necesitaba admitir, aunque sea
            a este papel, que te has vuelto importante para mí.
            
            Más importante de lo que es seguro admitir.
            
            - Diana
            """,
            min_trust_required=0.8,
            min_level_required=5,
            required_relationship_stage="confidant",
            discovery_chance=0.15,
            specific_archetype_bonus="romantic",
            gives_points=100,
            trust_increase=0.1,
            unlocks_special_dialogue=True
        ),
        
        UnsentLetter(
            trigger_event="event_new_moon",
            letter_date="Luna Nueva",
            emotional_state="nostalgic",
            subject="En noches como esta...",
            content="""
            Las lunas nuevas siempre me han hecho reflexionar.
            
            En la oscuridad total, cuando no hay luz que nos distraiga,
            es cuando realmente podemos ver hacia dentro.
            
            Esta noche pensé en ti. En cómo has iluminado
            rincones de mí que había olvidado que existían.
            
            No sé si leerás esto alguna vez, pero si lo haces,
            quiero que sepas que tu presencia ha sido como
            una luna nueva para mí: un nuevo comienzo en la oscuridad.
            
            - D
            """,
            min_trust_required=0.5,
            min_level_required=3,
            discovery_chance=0.3,
            gives_points=75,
            trust_increase=0.07
        ),
    ]
    
    for letter in letters:
        session.add(letter)
    
    await session.commit()

async def init_narrative_events(session: AsyncSession):
    """Inicializa eventos narrativos especiales"""
    
    events = [
        NarrativeEvent(
            id="new_moon_confessions",
            name="Confesiones de Luna Nueva",
            description="Durante la luna nueva, Diana se muestra más vulnerable y reflexiva",
            event_type="lunar_phase",
            trigger_conditions={"type": "lunar", "phase": "new_moon"},
            announcement_message="""
            La oscuridad de la luna nueva trae consigo
            oportunidades únicas de conexión profunda.
            
            Diana está más reflexiva que de costumbre...
            """,
            diana_special_mood="vulnerable",
            special_dialogues=[
                "Las lunas nuevas me recuerdan que hasta en la oscuridad total, hay esperanza de un nuevo comienzo.",
                "¿Alguna vez has sentido que la oscuridad te abraza mejor que la luz?",
                "En noches así, los muros parecen más delgados... más frágiles."
            ],
            exclusive_missions=["moon_confession_mission"],
            duration_hours=48,
            is_recurring=True,
            recurrence_pattern="lunar",
            min_trust_required=0.3
        ),
        
        NarrativeEvent(
            id="spring_awakening",
            name="El Despertar de Primavera",
            description="Con la llegada de la primavera, nuevos sentimientos florecen",
            event_type="seasonal",
            trigger_conditions={"type": "seasonal", "season": "spring"},
            announcement_message="""
            La primavera ha llegado a la mansión.
            Los jardines florecen y con ellos,
            nuevas posibilidades...
            """,
            diana_special_mood="hopeful",
            special_dialogues=[
                "La primavera siempre me hace creer que los cambios son posibles.",
                "Mira cómo florecen los jardines... ¿crees que las personas también podemos florecer de nuevo?",
                "Hay algo en el aire primaveral que me hace querer... arriesgar más."
            ],
            exclusive_lore_pieces=["L_SPRING_SECRET"],
            duration_hours=168,  # 1 semana
            is_recurring=True,
            recurrence_pattern="seasonal"
        ),
        
        NarrativeEvent(
            id="trust_milestone",
            name="Momento de Verdad",
            description="Has alcanzado un nivel de confianza que desbloquea revelaciones especiales",
            event_type="relationship_milestone",
            trigger_conditions={
                "type": "relationship",
                "stage": "trusted",
                "trust": 0.7
            },
            announcement_message="Has alcanzado un momento crucial en tu relación con Diana...",
            diana_special_mood="decisive",
            special_dialogues=[
                "Hemos llegado tan lejos... ¿estás listo para el siguiente paso?",
                "Hay cosas sobre mí que nadie más sabe. ¿Quieres ser la excepción?",
                "Tu paciencia y comprensión merecen ser recompensadas con verdades."
            ],
            exclusive_missions=["truth_revelation_mission"],
            duration_hours=72,
            is_recurring=False,
            min_level_required=4,
            vip_exclusive=True
        ),
    ]
    
    for event in events:
        session.add(event)
    
    await session.commit()

async def init_narrative_missions(session: AsyncSession):
    """Añade elementos narrativos a misiones"""
    
    # Aquí actualizarías las misiones existentes con contexto narrativo
    # Por ejemplo:
    narrative_missions = [
        {
            "id": "first_observation",
            "narrative_chapter": "first_observations",
            "diana_intro_dialogue": "Veo que eres observador... Me gusta eso. Veamos qué más puedes descubrir.",
            "diana_completion_dialogue": "Impresionante. No muchos notan esos detalles. Hay más en ti de lo que pensé.",
            "affects_trust": True,
            "trust_impact": 0.05
        },
        {
            "id": "vulnerability_test",
            "narrative_chapter": "the_kinky_revelation",
            "diana_intro_dialogue": "Esta misión requiere algo más que habilidad... requiere honestidad emocional.",
            "diana_completion_dialogue": "Tu valentía al ser vulnerable... me inspira a hacer lo mismo.",
            "affects_trust": True,
            "trust_impact": 0.1,
            "unlocks_lore_piece_code": "L3_LETTER_1"
        }
    ]
    
    # Actualizar misiones existentes
    for mission_data in narrative_missions:
        mission = await session.get(Mission, mission_data["id"])
        if mission:
            for key, value in mission_data.items():
                if key != "id":
                    setattr(mission, key, value)
    
    await session.commit()

async def main():
    """Función principal del script de inicialización"""
    
    print("Inicializando datos narrativos...")
    
    await init_db()
    Session = await get_session()
    
    async with Session() as session:
        print("- Inicializando pistas de lore...")
        await init_lore_pieces(session)
        
        print("- Inicializando cartas no enviadas...")
        await init_unsent_letters(session)
        
        print("- Inicializando eventos narrativos...")
        await init_narrative_events(session)
        
        print("- Actualizando misiones con contexto narrativo...")
        await init_narrative_missions(session)
    
    print("✅ Inicialización completada!")

if __name__ == "__main__":
    asyncio.run(main())
