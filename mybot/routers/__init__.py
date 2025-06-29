# No coloques mybot como módulo, es la raíz del proyecto
# Cuando se ejecuta ``bot.py`` directamente, los imports relativos fallan
# porque ``mybot`` no se trata como un paquete. Usamos una importación
# absoluta para asegurar compatibilidad sin importar cómo se ejecute el
# proyecto.
from trivia_router import router as trivia_router
