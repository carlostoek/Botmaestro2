"""Centralized text resources for the bot grouped by category."""

# ---------------------------------------------------------------------------
# Mensajes del Mayordomo del Diván
# ---------------------------------------------------------------------------
BUTLER_MESSAGES = {
    "vip_members_only": "Esta sección está disponible solo para miembros VIP.",
    "profile_not_registered": "Parece que aún no has comenzado tu recorrido. Usa /start para dar tu primer paso.",
    "back_to_main_menu": "Has regresado al centro del Diván. Elige por dónde seguir explorando.",
    "unrecognized_command_text": "Comando no reconocido. Aquí está el menú principal:",
    "confirm_purchase_message": "¿Estás segur@ de que quieres canjear {reward_name} por {reward_cost} puntos?",
    "purchase_cancelled_message": "Compra cancelada. Puedes seguir explorando otras recompensas.",
    "gain_points_instructions": "Puedes ganar puntos completando misiones y participando en las actividades del canal.",
    "enter_reward_name": "Ingresa el nombre de la recompensa:",
    "enter_reward_points": "¿Cuántos puntos se requieren?",
    "enter_reward_description": "Agrega una descripción (opcional):",
    "select_reward_type": "Selecciona el tipo de recompensa:",
    "reward_created": "✅ Recompensa creada.",
    "reward_deleted": "❌ Recompensa eliminada.",
    "reward_updated": "✅ Recompensa actualizada.",
    "invalid_number": "Ingresa un número válido.",
    "level_created": "✅ Nivel creado correctamente.",
    "level_updated": "✅ Nivel actualizado.",
    "level_deleted": "❌ Nivel eliminado.",
}

# ---------------------------------------------------------------------------
# Mensajes de la Señorita Kinky
# ---------------------------------------------------------------------------
KINKY_MESSAGES = {
    "start_welcome_new_user": (
        "🌙 Bienvenid@ a *El Diván de Diana*…\n\n"
        "Aquí cada gesto, cada decisión y cada paso que das, suma. Con cada interacción, te adentras más en *El Juego del Diván*.\n\n"
        "¿Estás list@ para descubrir lo que te espera? Elige por dónde empezar, yo me encargo de hacer que lo disfrutes."
    ),
    "start_welcome_returning_user": (
        "✨ Qué bueno tenerte de regreso.\n\n"
        "Tu lugar sigue aquí. Tus puntos también... y hay nuevas sorpresas esperándote.\n\n"
        "¿List@ para continuar *El Juego del Diván*?"
    ),
    "reward_claim_success": "🎉 ¡Recompensa reclamada!",
    "level_up_notification": "🎉 ¡Subiste a Nivel {level}: {level_name}! {reward}",
    "special_level_reward": "✨ Recompensa especial por alcanzar el nivel {level}! {reward}",
    "daily_gift_received": "🎁 Recibiste {points} puntos del regalo diario!",
    "PACK_INTEREST_REPLY": "💌 ¡Gracias! Recibí tu interés. Me pondré en contacto contigo muy pronto. O si no quieres esperar escríbeme directo a mi chat privado en ,,@DianaKinky ",
    "VIP_INTEREST_REPLY": (
        "💌 ¡Gracias! Recibí tu interés. Me pondré en contacto contigo muy pronto. "
        "O si no quieres esperar escríbeme directo a mi chat privado en ,,@DianaKinky "
    ),
    "vip_first_welcome": (
        "💖 Bienvenido al VIP, cariño. Gracias por acompañarme en este rincón tan exclusivo."\
        " Prepárate para disfrutar como nunca antes... ahora te dejo en manos del Mayordomo del Diván."
    ),
}

# ---------------------------------------------------------------------------
# Textos de menús y opciones generales
# ---------------------------------------------------------------------------
MENU_MESSAGES = {
    "profile_title": "🛋️ *Tu rincón en El Diván de Diana*",
    "profile_points": "📌 *Puntos acumulados:* `{user_points}`",
    "profile_level": "🎯 *Nivel actual:* `{user_level}`",
    "profile_points_to_next_level": "📶 *Para el siguiente nivel:* `{points_needed}` más (Nivel `{next_level}` a partir de `{next_level_threshold}`)",
    "profile_max_level": "🌟 Has llegado al nivel más alto... y se nota. 😉",
    "profile_achievements_title": "🏅 *Logros desbloqueados*",
    "profile_no_achievements": "Aún no hay logros. Pero te tengo fe.",
    "profile_active_missions_title": "📋 *Tus desafíos activos*",
    "profile_no_active_missions": "Por ahora no hay desafíos, pero eso puede cambiar pronto. Mantente cerca.",
    "missions_title": "🎯 *Desafíos disponibles*",
    "missions_no_active": "No hay desafíos por el momento. Aprovecha para tomar aliento.",
    "reward_shop_title": "🎁 *Recompensas del Diván*",
    "reward_shop_empty": "Por ahora no hay recompensas disponibles. Pero pronto sí. 😉",
    "ranking_title": "🏆 *Tabla de Posiciones*",
    "ranking_entry": "#{rank}. @{username} - Puntos: `{points}`, Nivel: `{level}`",
    "no_ranking_data": "Aún no hay datos en el ranking. ¡Sé el primero en aparecer!",
    "menu_missions_text": "Aquí están los desafíos que puedes emprender. ¡Cada uno te acerca más!",
    "menu_rewards_text": "¡Es hora de canjear tus puntos! Aquí tienes las recompensas disponibles:",
    "profile_achievements_button_text": "🏅 Mis Logros",
    "profile_active_missions_button_text": "🎯 Mis Desafíos",
    "back_to_profile_button_text": "← Volver a mi rincón",
    "view_all_missions_button_text": "Ver todos los desafíos",
    "back_to_missions_button_text": "← Volver a desafíos",
    "complete_mission_button_text": "✅ Completado",
    "confirm_purchase_button_text": "Canjear por `{cost}` puntos",
    "cancel_purchase_button_text": "❌ Cancelar",
    "back_to_rewards_button_text": "← Volver a recompensas",
    "prev_page_button_text": "← Anterior",
    "next_page_button_text": "Siguiente →",
    "back_to_main_menu_button_text": "← Volver al inicio",
    "FREE_MENU_TEXT": "✨ *Bienvenid@ a mi espacio gratuito*\n\nElige y descubre un poco de mi mundo...",
    "FREE_GIFT_TEXT": (
        "🎁 *Desbloquear regalo*\n"
        "Activa tu obsequio de bienvenida y descubre los primeros detalles de todo lo que tengo para ti."
    ),
    "PACKS_MENU_TEXT": (
        "🎀 *Paquetes especiales de Diana* 🎀\n\n"
        "¿Quieres una probadita de mis momentos más intensos?\n\n"
        "Estos son sets que puedes comprar directamente, sin suscripción. "
        "Cada uno incluye fotos y videos explícitos. 🥵\n\n"
        "🛍️ Elige tu favorito y presiona *“Me interesa”*. Yo me pondré en contacto contigo."
    ),
    "PACK_1_DETAILS": (
        "💫 *Encanto Inicial*\n"
        "Una primera mirada. Una chispa.\n"
        "Aquí comienza el juego entre tú y yo…\n\n"
        "Este set es tu puerta de entrada a mi mundo:\n"
        "📹 1 video íntimo donde mis dedos exploran lentamente mientras mis labios y mirada te envuelven.\n"
        "📸 10 fotos donde apenas cubro lo necesario… lencería suave, piel desnuda, miradas insinuantes.\n\n"
        "Perfecto si quieres conocerme de una forma dulce, coqueta y provocadora.\n\n"
        "*150 MXN (10 USD)*"
    ),
    "PACK_2_DETAILS": (
        "🔥 *Sensualidad Revelada*\n"
        "Te muestro más. Te invito a quedarte…\n\n"
        "Este set revela lo que solo pocos han visto:\n"
        "📹 2 videos donde me toco sin censura, jugando con mi cuerpo mientras mi rostro refleja cada sensación.\n"
        "📸 10 fotos tan provocadoras que te harán dudar si mirar una sola vez será suficiente.\n\n"
        "Es mi manera de decirte:\n"
        "“No es lo que ves... es cómo te lo muestro.”\n\n"
        "*200 MXN (14 USD)*"
    ),
    "PACK_3_DETAILS": (
        "💋 *Pasión Desbordante*\n"
        "Aquí ya no hay timidez. Solo deseo.\n\n"
        "Este set está hecho para quienes quieren ver *todo* lo que puedo provocar:\n"
        "📹 3 videos:\n"
        "1. En lencería de alto voltaje\n"
        "2. Vestida, pero seduciéndote con juegos visuales\n"
        "3. Jugando con un juguetito que me hace gemir suave… y fuerte.\n"
        "📸 15 fotos íntimas y provocativas, capturadas en el punto exacto entre arte y placer.\n\n"
        "Un set para perderte y volver a verme... muchas veces.\n\n"
        "*250 MXN (17 USD)*"
    ),
    "PACK_4_DETAILS": (
        "🔞 *Intimidad Explosiva*\n\n"
        "Esto no es un set. Es una confesión explícita…\n\n"
        "Mi lado más sucio, más real, más entregado:\n"
        "📹 5 videos:\n"
        "- Me masturbo hasta acabar... sin cortes.\n"
        "- Uso dildos, me abro, gimo, me muerdo los labios.\n"
        "- Me desvisto lentamente hasta estar completamente desnuda.\n"
        "- Juego con mis juguetes favoritos.\n"
        "- Y uno… donde estoy montando, moviéndome como si estuvieras debajo. Sin censura.\n\n"
        "📸 15 fotos extra, como regalo. Fotos que no circulan por ningún otro lado.\n\n"
        "Este es el set que convierte la fantasía en algo real.\n"
        "Lo más explícito. Lo más mío. Lo más tuyo.\n\n"
        "*300 MXN (20 USD)*"
    ),
    "FREE_VIP_EXPLORE_TEXT": (
        "🔐 *Bienvenido al Diván de Diana* 🔐\n\n"
        "¿Te atreves a entrar a mi universo sin censura?\n\n"
        "✨ Más de 2000 archivos privados\n"
        "🎬 Videos explícitos sin censura\n"
        "🎁 Descuentos en contenido personalizado\n"
        "👀 Acceso exclusivo a mis historias diarias\n\n"
        "📌 Precio: *$350 MXN / mes*"
    ),
    "FREE_CUSTOM_TEXT": (
        "💌 *Quiero contenido personalizado*\n"
        "Cuéntame tus fantasías y recibirás algo hecho solo para ti."
    ),
    "FREE_GAME_TEXT": (
        "🎮 *Modo gratuito del juego Kinky*\n"
        "Disfruta de un adelanto de la diversión. La versión completa te espera en el VIP."
    ),
    "FREE_FOLLOW_TEXT": (
        "🌐 *¿Dónde más seguirme?*\n"
        "Encuentra todos mis enlaces y redes para que no te pierdas nada."
    ),
}

# ---------------------------------------------------------------------------
# Mensajes de misiones y minijuegos
# ---------------------------------------------------------------------------
GAME_MESSAGES = {
    "mission_not_found": "Ese desafío no existe o ya expiró.",
    "mission_already_completed": "Ya lo completaste. Buen trabajo.",
    "mission_completed_success": "✅ ¡Desafío completado! Ganaste `{points_reward}` puntos.",
    "mission_completed_feedback": "🎉 ¡Misión '{mission_name}' completada! Ganaste `{points_reward}` puntos.",
    "mission_level_up_bonus": "🚀 Subiste de nivel. Ahora estás en el nivel `{user_level}`. Las cosas se pondrán más interesantes.",
    "mission_achievement_unlocked": "\n🏆 Logro desbloqueado: *{achievement_name}*",
    "mission_completion_failed": "❌ No pudimos registrar este desafío. Revisa si ya lo hiciste antes o si aún está activo.",
    "reward_not_found": "Esa recompensa ya no está aquí... o aún no está lista.",
    "reward_not_registered": "Tu perfil no está activo. Usa /start para comenzar *El Juego del Diván*.",
    "reward_not_enough_points": "Te faltan `{required_points}` puntos. Ahora tienes `{user_points}`. Pero sigue... estás cerca.",
    "reward_claim_failed": "No pudimos procesar tu solicitud.",
    "reward_already_claimed": "Esta recompensa ya fue reclamada.",
    "points_total_notification": "Tienes ahora {total_points} puntos acumulados.",
    "checkin_success": "✅ Check-in registrado. Ganaste {points} puntos.",
    "checkin_already_done": "Ya realizaste tu check-in. Vuelve mañana.",
    "daily_gift_already": "Ya reclamaste el regalo diario. Vuelve mañana.",
    "daily_gift_disabled": "Regalos diarios deshabilitados.",
    "minigames_disabled": "Minijuegos deshabilitados.",
    "dice_points": "Ganaste {points} puntos lanzando el dado.",
    "trivia_correct": "¡Correcto! +5 puntos",
    "trivia_wrong": "Respuesta incorrecta.",
    "challenge_completed": "🎯 ¡Desafío {challenge_type} completado! +{points} puntos",
    "reaction_registered": "👍 ¡Reacción registrada!",
    "reaction_registered_points": "👍 ¡Reacción registrada! Ganaste {points} puntos.",
    "reaction_already": "Ya reaccionaste a este mensaje.",
    "mission_details_text": (
        "🎯 *Desafío:* {mission_name}\n\n"
        "📖 *Descripción:* {mission_description}\n"
        "🎁 *Recompensa:* `{points_reward}` puntos\n"
        "⏱️ *Frecuencia:* `{mission_type}`"
    ),
    "reward_details_text": (
        "🎁 *Recompensa:* {reward_title}\n\n"
        "📌 *Descripción:* {reward_description}\n"
        "🔥 *Requiere:* `{required_points}` puntos"
    ),
    "reward_details_not_enough_points_alert": "💔 Te faltan puntos para esta recompensa. Necesitas `{required_points}`, tienes `{user_points}`. Sigue sumando, lo estás haciendo bien.",
    "user_no_badges": "Aún no has desbloqueado ninguna insignia. ¡Sigue participando!",
}

# ---------------------------------------------------------------------------
# Combinación en BOT_MESSAGES para compatibilidad
# ---------------------------------------------------------------------------
BOT_MESSAGES = {}
for _grp in (BUTLER_MESSAGES, KINKY_MESSAGES, MENU_MESSAGES, GAME_MESSAGES):
    BOT_MESSAGES.update(_grp)

# Textos descriptivos para las insignias disponibles
BADGE_TEXTS = {
    "first_message": {"name": "Primer Mensaje", "description": "Envía tu primer mensaje en el chat"},
    "conversador": {"name": "Conversador", "description": "Alcanza 100 mensajes enviados"},
    "invitador": {"name": "Invitador", "description": "Consigue 5 invitaciones exitosas"},
}

NIVEL_TEMPLATE = """
🎮 Tu nivel actual: {current_level}
✨ Puntos totales: {points}
📊 Progreso hacia el siguiente nivel: {percentage:.1%}
🎯 Te faltan {points_needed} puntos para alcanzar el nivel {next_level}.
"""
