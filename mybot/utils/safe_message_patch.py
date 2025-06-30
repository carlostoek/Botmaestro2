import inspect
import logging
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest

class SafeMessagePatch:
    _original_answer = None
    _patched = False

    @classmethod
    def apply_patch(cls):
        """Aplica parche global para manejar textos vacíos en message.answer()"""
        if cls._patched:
            return "✅ Parche ya aplicado anteriormente"

        cls._original_answer = Message.answer
        Message.answer = cls._safe_answer
        cls._patched = True

        logging.info("✅ Parche SafeMessage aplicado - textos vacíos serán manejados automáticamente")
        return "✅ Parche aplicado exitosamente"

    @classmethod
    async def _safe_answer(cls, self, text, **kwargs):
        """Método seguro que reemplaza message.answer()"""
        try:
            # Validar texto
            if not text or (isinstance(text, str) and text.strip() == ''):
                # Obtener información del caller
                frame = inspect.currentframe().f_back
                frame_info = inspect.getframeinfo(frame)
                caller_name = frame.f_code.co_name
                file_name = frame_info.filename.split('/')[-1]
                line_number = frame_info.lineno

                # Crear mensaje informativo
                safe_text = f"📝 Texto vacío detectado\n\n🔍 Origen: {caller_name}()\n📁 {file_name}:{line_number}"

                # Log del evento
                logging.warning(f"Texto vacío parcheado desde: {caller_name}() [{file_name}:{line_number}]")

                return await cls._original_answer(self, safe_text, **kwargs)

            # Si el texto es válido, usar método original
            return await cls._original_answer(self, text, **kwargs)

        except TelegramBadRequest as e:
            if "text must be non-empty" in str(e):
                # Fallback de emergencia
                emergency_text = "⚠️ Error: Mensaje sin contenido"
                logging.error(f"Error Telegram capturado y manejado: {e}")
                return await cls._original_answer(self, emergency_text, **kwargs)
            raise e

