# No coloques mybot como módulo, es la raíz del proyecto
# Importamos el router de trivia usando una ruta absoluta para evitar
# problemas de importación cuando "routers" es tratado como un módulo de
# primer nivel.
from trivia_router import router as trivia_router
