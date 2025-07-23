export const mockStoryData = {
  title: "Mi Historia Interactiva",
  description: "Una historia épica con Lucien y Diana",
  fragments: [
    {
      fragment_id: "start",
      content: "Lucien se despierta en una habitación desconocida. La luz de la mañana se filtra a través de las cortinas, creando sombras misteriosas en las paredes. Sus ojos se adaptan lentamente a la claridad mientras trata de recordar cómo llegó hasta aquí.",
      character: "Lucien",
      level: 1,
      required_besitos: 0,
      required_role: "normal",
      reward_besitos: 10,
      decisions: [
        {
          text: "Explorar la habitación en busca de pistas",
          next_fragment: "explore_room"
        },
        {
          text: "Salir inmediatamente de la habitación",
          next_fragment: "exit_room"
        }
      ],
      position: { x: 100, y: 100 }
    },
    {
      fragment_id: "explore_room",
      content: "Lucien examina cuidadosamente la habitación. Encuentra una carta sobre la mesa de noche con su nombre escrito en elegante caligrafía. Al abrirla, descubre un mensaje enigmático que menciona un encuentro al atardecer.",
      character: "Lucien",
      level: 1,
      required_besitos: 0,
      required_role: "normal",
      reward_besitos: 15,
      decisions: [
        {
          text: "Leer la carta completa",
          next_fragment: "read_letter"
        },
        {
          text: "Buscar más pistas en la habitación",
          next_fragment: "search_more"
        }
      ],
      position: { x: 400, y: 50 }
    },
    {
      fragment_id: "exit_room",
      content: "Lucien sale apresuradamente de la habitación y se encuentra en un largo pasillo lleno de puertas. El sonido de sus pasos resuena en el silencio. Al final del pasillo, una figura familiar lo espera: Diana.",
      character: "Diana",
      level: 1,
      required_besitos: 5,
      required_role: "normal",
      reward_besitos: 20,
      decisions: [
        {
          text: "Acercarse a Diana con cautela",
          next_fragment: "approach_diana"
        },
        {
          text: "Llamar a Diana desde la distancia",
          next_fragment: "call_diana"
        }
      ],
      position: { x: 400, y: 200 }
    },
    {
      fragment_id: "read_letter",
      content: "La carta revela detalles sobre un tesoro oculto y un mapa que conduce a él. Lucien se da cuenta de que esta no es una situación ordinaria, sino el comienzo de una aventura que podría cambiar su vida para siempre.",
      character: "Lucien",
      level: 2,
      required_besitos: 10,
      required_role: "normal",
      reward_besitos: 25,
      decisions: [
        {
          text: "Seguir las instrucciones del mapa",
          next_fragment: "follow_map"
        },
        {
          text: "Buscar ayuda para descifrar el mapa",
          next_fragment: "seek_help"
        }
      ],
      position: { x: 700, y: 50 }
    },
    {
      fragment_id: "search_more",
      content: "Lucien continúa su búsqueda y encuentra un compartimento secreto en el escritorio. Dentro hay un medallón dorado con una inscripción en un idioma que no reconoce. El medallón emite un brillo suave y cálido.",
      character: "Lucien",
      level: 2,
      required_besitos: 15,
      required_role: "vip",
      reward_besitos: 30,
      decisions: [
        {
          text: "Ponerse el medallón",
          next_fragment: "wear_medallion"
        },
        {
          text: "Estudiar la inscripción más detenidamente",
          next_fragment: "study_inscription"
        }
      ],
      position: { x: 700, y: 150 }
    },
    {
      fragment_id: "approach_diana",
      content: "Diana sonríe al ver a Lucien acercarse. Sus ojos brillan con una mezcla de alivio y preocupación. 'Finalmente despertaste', dice con voz suave. 'Tenemos que hablar sobre lo que pasó anoche y lo que está por venir.'",
      character: "Diana",
      level: 2,
      required_besitos: 20,
      required_role: "normal",
      reward_besitos: 35,
      decisions: [
        {
          text: "Preguntar sobre los eventos de anoche",
          next_fragment: "ask_about_night"
        },
        {
          text: "Preguntar sobre el futuro",
          next_fragment: "ask_about_future"
        }
      ],
      position: { x: 700, y: 250 }
    },
    {
      fragment_id: "call_diana",
      content: "Diana se voltea al escuchar su nombre. Su expresión se ilumina con una sonrisa genuina. 'Lucien, qué bueno que estés bien. Ven aquí, necesito mostrarte algo importante que encontré mientras esperaba a que despertaras.'",
      character: "Diana",
      level: 2,
      required_besitos: 10,
      required_role: "normal",
      reward_besitos: 25,
      decisions: [
        {
          text: "Acercarse para ver lo que encontró",
          next_fragment: "see_discovery"
        },
        {
          text: "Preguntar cómo llegó hasta aquí",
          next_fragment: "ask_how_here"
        }
      ],
      position: { x: 700, y: 350 }
    },
    {
      fragment_id: "follow_map",
      content: "Lucien sigue las indicaciones del mapa y llega a un jardín secreto escondido detrás de la mansión. En el centro del jardín hay una fuente antigua con grabados que parecen coincidir con los símbolos del mapa.",
      character: "Lucien",
      level: 3,
      required_besitos: 25,
      required_role: "vip",
      reward_besitos: 40,
      decisions: [
        {
          text: "Examinar los grabados de la fuente",
          next_fragment: "examine_fountain"
        },
        {
          text: "Buscar el tesoro en los alrededores",
          next_fragment: "search_treasure"
        }
      ],
      position: { x: 1000, y: 100 }
    },
    {
      fragment_id: "seek_help",
      content: "Lucien decide buscar a Diana para que lo ayude a descifrar el mapa. La encuentra en la biblioteca, rodeada de libros antiguos. Cuando le muestra el mapa, Diana sonríe con conocimiento, como si hubiera estado esperando este momento.",
      character: "Diana",
      level: 3,
      required_besitos: 30,
      required_role: "premium",
      reward_besitos: 50,
      decisions: [
        {
          text: "Preguntarle qué sabe sobre el mapa",
          next_fragment: "diana_knowledge"
        },
        {
          text: "Trabajar juntos para resolverlo",
          next_fragment: "work_together"
        }
      ],
      position: { x: 1000, y: 200 }
    },
    {
      fragment_id: "wear_medallion",
      content: "Al ponerse el medallón, Lucien siente una energía extraña corriendo por su cuerpo. Visiones de lugares lejanos y eventos del pasado llenan su mente. Comprende que el medallón es una llave hacia un destino mucho más grande.",
      character: "Lucien",
      level: 4,
      required_besitos: 40,
      required_role: "premium",
      reward_besitos: 60,
      decisions: [
        {
          text: "Abrazar el poder del medallón",
          next_fragment: "embrace_power"
        },
        {
          text: "Resistir las visiones",
          next_fragment: "resist_visions"
        }
      ],
      position: { x: 1000, y: 300 }
    },
    {
      fragment_id: "study_inscription",
      content: "Lucien estudia cuidadosamente los símbolos en el medallón. Gradualmente, comienza a entender que es un texto en un idioma ancestral que habla de un guardián elegido. Las palabras parecen resonar con algo profundo en su alma.",
      character: "Lucien",
      level: 3,
      required_besitos: 35,
      required_role: "vip",
      reward_besitos: 45,
      decisions: [
        {
          text: "Intentar traducir completamente la inscripción",
          next_fragment: "translate_inscription"
        },
        {
          text: "Buscar referencias en la biblioteca",
          next_fragment: "library_research"
        }
      ],
      position: { x: 1000, y: 400 }
    }
  ]
};

export const mockCharacters = [
  {
    id: 'lucien',
    name: 'Lucien',
    description: 'Un joven aventurero con un pasado misterioso',
    color: 'blue'
  },
  {
    id: 'diana',
    name: 'Diana',
    description: 'Una sabia conocedora de antiguos secretos',
    color: 'pink'
  }
];

export const mockRoles = [
  { id: 'normal', name: 'Normal', description: 'Acceso básico a la historia' },
  { id: 'vip', name: 'VIP', description: 'Acceso a contenido premium' },
  { id: 'premium', name: 'Premium', description: 'Acceso completo a toda la historia' }
];

export const mockLevels = [
  { level: 1, name: 'Principiante', description: 'Introducción a la historia' },
  { level: 2, name: 'Aventurero', description: 'Profundizando en la trama' },
  { level: 3, name: 'Explorador', description: 'Descubriendo secretos' },
  { level: 4, name: 'Maestro', description: 'Dominando el destino' },
  { level: 5, name: 'Leyenda', description: 'Alcanzando la maestría' }
];