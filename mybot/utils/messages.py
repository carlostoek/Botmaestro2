# utils/messages.py
"""Centralized bot texts organized by speaker and context."""

# Mensajes de la Señorita Kinky
KINKY_MESSAGES = {
    "start_welcome_new_user": (
        "🌙 Hola, alma curiosa... Bienvenid@ a *El Diván de Diana*. "
        "Cada caricia y cada decisión te acercan más a nuestro juego secreto."
    ),
    "start_welcome_returning_user": (
        "✨ Me alegra tenerte de vuelta. Tus deseos y puntos te estaban esperando."
    ),
    "vip_special_welcome": (
        "Hola, mi Kinky. Qué emoción que estés aquí, donde todo lo especial sucede. "
        "Prepárate, porque este será nuestro rincón secreto. Desde ahora te dejo a cargo de mi querido Mayordomo del Diván, él cuidará de ti y te llevará de la mano. "
        "Pero no te preocupes… seguiré muy, muy cerca."
    ),
}

# Mensajes del Mayordomo del Diván
BUTLER_MESSAGES = {
    "vip_members_only": "Esta sección está reservada para nuestros distinguidos miembros VIP.",
    "profile_not_registered": "Aún no he registrado su presencia. Use /start para comenzar su travesía.",
    "profile_title": "🛋️ *Su rincón en El Diván de Diana*",
    "profile_points": "📌 *Puntos acumulados:* `{user_points}`",
    "profile_level": "🎯 *Nivel actual:* `{user_level}`",
    "profile_points_to_next_level": "📶 *Para el siguiente nivel:* `{points_needed}` más (Nivel `{next_level}` desde `{next_level_threshold}`)",
    "profile_max_level": "🌟 Ha alcanzado el nivel más alto. Mis respetos.",
    "profile_achievements_title": "🏅 *Logros obtenidos*",
    "profile_no_achievements": "Aún no cuenta con logros. Confío en que pronto los tendrá.",
    "profile_active_missions_title": "📋 *Sus desafíos activos*",
    "profile_no_active_missions": "Por el momento no hay desafíos disponibles. Esté atento.",
    "back_to_main_menu": "Ha regresado al centro del Diván. Indique cómo desea continuar.",
    "vip_welcome_link": (
        "Es un placer darle la bienvenida a nuestro selecto círculo. "
        "Su suscripción estará activa por {duration} días, hasta {expires_at}.\n\n"
        "Este es su acceso exclusivo: {invite_link}\n"
        "Tenga presente que el enlace caduca en 24 horas."
    ),
    "vip_welcome_no_link": (
        "Es un placer darle la bienvenida a nuestro selecto círculo. "
        "Su suscripción estará activa por {duration} días, hasta {expires_at}.\n\n"
        "Use /vip_menu para descubrir todas sus ventajas."
    ),
}

# Textos de menús y opciones generales
MENU_TEXTS = {
    "admin_main": "🛠️ **Panel de Administración**\n\nBienvenido al centro de control del bot. Desde aquí puede gestionar todos los aspectos del sistema.",
    "vip_main": "✨ **Bienvenido al Diván de Diana**\n\nSu suscripción VIP le otorga acceso completo a todas las funciones. Disfrute de la experiencia premium.",
    "free_main": "🌟 **Bienvenido a los Kinkys**\n\nExplore nuestro contenido gratuito y descubra todo lo que tenemos para usted. ¿Listo para una experiencia única?",
    "menu_missions_text": "Aquí se muestran los desafíos disponibles. Cada uno lo acerca más a nuevas recompensas.",
    "menu_rewards_text": "Es momento de canjear sus puntos. Estas son las recompensas disponibles:",
    "unrecognized_command_text": "Comando no reconocido. Este es el menú principal:",
    "free_welcome": "Bienvenido a los kinkys",
    "free_info_text": "Información del canal gratuito.",
    "free_game_title": "Mini Juego Kinky (versión gratuita)",
    "admin_welcome_prefix": "👑 **¡Bienvenido, Administrador!**\n\n",
}

# Mensajes de misiones y minijuegos
MISSION_MESSAGES = {
    "missions_title": "🎯 *Desafíos disponibles*",
    "missions_no_active": "No hay desafíos por ahora. Aproveche para descansar.",
    "mission_not_found": "Ese desafío no existe o ha expirado.",
    "mission_already_completed": "Ese desafío ya fue completado. Excelente trabajo.",
    "mission_completed_success": "✅ Desafío completado. Ha ganado `{points_reward}` puntos.",
    "mission_completed_feedback": "🎉 Misión '{mission_name}' completada. Ha ganado `{points_reward}` puntos.",
    "mission_level_up_bonus": "🚀 ¡Ha subido al nivel `{user_level}`! Todo se vuelve más interesante.",
    "mission_achievement_unlocked": "\n🏆 Logro desbloqueado: *{achievement_name}*",
    "mission_completion_failed": "❌ No fue posible registrar este desafío. Verifique si ya lo completó o si sigue activo.",
    "reward_shop_title": "🎁 *Recompensas del Diván*",
    "reward_shop_empty": "Por ahora no hay recompensas disponibles, pero pronto las habrá.",
    "reward_not_found": "Esa recompensa ya no se encuentra disponible.",
    "reward_not_registered": "Su perfil aún no está activo. Use /start para comenzar El Juego del Diván.",
    "reward_not_enough_points": "Necesita `{required_points}` puntos y posee `{user_points}`. Continúe acumulando para obtenerla.",
    "reward_claim_success": "🎉 Recompensa reclamada con éxito.",
    "reward_claim_failed": "No fue posible procesar su solicitud.",
    "reward_already_claimed": "Esta recompensa ya ha sido reclamada.",
    "level_up_notification": "🎉 ¡Subió a Nivel {level}: {level_name}! {reward}",
    "special_level_reward": "✨ Recompensa especial por alcanzar el nivel {level}! {reward}",
    "ranking_title": "🏆 *Tabla de Posiciones*",
    "ranking_entry": "#{rank}. @{username} - Puntos: `{points}`, Nivel: `{level}`",
    "no_ranking_data": "Aún no hay datos en el ranking. Sea el primero en aparecer.",
    "weekly_ranking_title": "🏆 Ranking Semanal de Reacciones",
    "weekly_ranking_entry": "#{rank}. {username} - Reacciones: {count}",
    "weekly_no_data": "Aún no hay reacciones registradas esta semana.",
    "confirm_purchase_message": "¿Confirma que desea canjear {reward_name} por {reward_cost} puntos?",
    "purchase_cancelled_message": "Compra cancelada. Puede seguir explorando otras recompensas.",
    "gain_points_instructions": "Puede ganar puntos completando misiones y participando en las actividades del canal.",
    "points_total_notification": "Ahora cuenta con {total_points} puntos acumulados.",
    "checkin_success": "✅ Check-in registrado. Ha ganado {points} puntos.",
    "checkin_already_done": "Ya registró su check-in. Vuelva mañana.",
    "daily_gift_received": "🎁 Ha recibido {points} puntos del regalo diario!",
    "daily_gift_already": "Ya reclamó el regalo diario. Vuelva mañana.",
    "daily_gift_disabled": "Regalos diarios deshabilitados.",
    "minigames_disabled": "Minijuegos deshabilitados.",
    "dice_points": "Ha ganado {points} puntos lanzando el dado.",
    "roulette_no_free": "Ya utilizó su tiro gratis. Puede comprar giros extra.",
    "roulette_result": "Resultado {score}, ha ganado {points} puntos.",
    "roulette_bought": "Tiro extra comprado.",
    "roulette_buy_fail": "No posee puntos suficientes.",
    "trivia_correct": "¡Correcto! +5 puntos",
    "trivia_wrong": "Respuesta incorrecta.",
    "reto_start": "Reaccione a {target} publicaciones en {seconds} segundos.",
    "reto_success": "¡Reto completado!",
    "reto_failed": "No completó el reto y perdió puntos.",
    "challenge_completed": "🎯 Desafío {challenge_type} completado. +{points} puntos",
    "reaction_registered": "👍 Reacción registrada.",
    "reaction_thanks": "¡Gracias por reaccionar!",
    "enter_reward_name": "Ingrese el nombre de la recompensa:",
    "enter_reward_points": "¿Cuántos puntos se requieren?",
    "enter_reward_description": "Agregue una descripción (opcional):",
    "select_reward_type": "Seleccione el tipo de recompensa:",
    "reward_created": "✅ Recompensa creada.",
    "reward_deleted": "❌ Recompensa eliminada.",
    "reward_updated": "✅ Recompensa actualizada.",
    "invalid_number": "Ingrese un número válido.",
    "user_no_badges": "Aún no ha desbloqueado ninguna insignia. Continúe participando.",
    "level_created": "✅ Nivel creado correctamente.",
    "level_updated": "✅ Nivel actualizado.",
    "level_deleted": "❌ Nivel eliminado.",
    "auto_mission_reaction_name": "Reaccionar a la publicación",
    "auto_mission_reaction_desc": "Pulse cualquier reacción para completar la misión.",
}

# Unión de todos los mensajes para compatibilidad con el código existente
BOT_MESSAGES = {**KINKY_MESSAGES, **BUTLER_MESSAGES, **MENU_TEXTS, **MISSION_MESSAGES}

# Textos descriptivos de insignias
BADGE_TEXTS = {
    "first_message": {
        "name": "Primer Mensaje",
        "description": "Envíe su primer mensaje en el chat",
    },
    "conversador": {
        "name": "Conversador",
        "description": "Alcance 100 mensajes enviados",
    },
    "invitador": {
        "name": "Invitador",
        "description": "Consiga 5 invitaciones exitosas",
    },
}

# Plantilla de mensaje para mostrar el nivel del usuario
NIVEL_TEMPLATE = """
🎮 Su nivel actual: {current_level}
✨ Puntos totales: {points}
📊 Progreso hacia el siguiente nivel: {percentage:.1%}
🎯 Le faltan {points_needed} puntos para alcanzar el nivel {next_level}.
"""
