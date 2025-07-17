STORY_GRAPH = {
    'start': {
        'text': 'Lucien te recibe con una inclinación de cabeza. "Bienvenido. La señora Diana te esperaba. Pero antes, dime, ¿quién eres en esta historia?"',
        'character': 'Lucien',
        'decisions': [
            {'text': 'Un alma curiosa', 'next': 'path_curious'},
            {'text': 'Un corazón apasionado', 'next': 'path_passionate'},
        ]
    },
    'path_curious': {
        'text': '"Curiosidad... una cualidad peligrosa y fascinante. Te guiaré por los secretos que esta mansión esconde."',
        'character': 'Lucien',
        'decisions': [
            {'text': 'Continuar...', 'next': 'start'} # Loop back for now
        ]
    },
    'path_passionate': {
        'text': '"Pasión. El motor de toda gran historia. Veo que la tuya será... intensa."',
        'character': 'Lucien',
        'decisions': [
            {'text': 'Continuar...', 'next': 'start'} # Loop back for now
        ]
    }
}