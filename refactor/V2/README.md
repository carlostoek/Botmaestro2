# Diana Bot V2 🌸

Diana Bot es un bot de Telegram con funciones avanzadas de administración de canales, gamificación y narrativa profunda. Esta es la versión 2.0, una refactorización completa del bot original.

## 🚀 Características Principales

- **Sistema Emocional Avanzado**: Los personajes tienen estados emocionales dinámicos que evolucionan con las interacciones.
- **Narrativa Ramificada**: Experiencia narrativa inmersiva con decisiones que afectan el desarrollo de la historia.
- **Gamificación Completa**: Sistema de puntos, logros, misiones y recompensas para mantener a los usuarios comprometidos.
- **Gestión de Canales**: Herramientas avanzadas para administrar canales VIP y gratuitos.
- **Respuestas Personalizadas**: Contenido adaptado a las preferencias y comportamiento de cada usuario.
- **Minijuegos Interactivos**: Ruleta, trivia y otros minijuegos integrados en la experiencia.

## 🧠 Arquitectura

La V2 ha sido rediseñada siguiendo principios de Clean Architecture para mejorar:

- **Mantenibilidad**: Código organizado, bien documentado y fácil de modificar.
- **Testabilidad**: Componentes desacoplados que pueden probarse de forma aislada.
- **Extensibilidad**: Fácil adición de nuevas características sin modificar el código existente.
- **Rendimiento**: Optimizaciones en áreas críticas para mejor experiencia de usuario.

Para más detalles, consulta [ARCHITECTURE.md](ARCHITECTURE.md).

## 🛠️ Tecnologías

- **Python 3.10+**: Aprovechando las últimas características del lenguaje.
- **Aiogram 3.x**: Framework moderno y asíncrono para bots de Telegram.
- **SQLAlchemy 2.x**: ORM potente y flexible para interacción con bases de datos.
- **PostgreSQL**: Base de datos relacional robusta.
- **Pydantic**: Validación de datos y configuración basada en tipos.
- **Asyncio**: Programación asíncrona para máxima eficiencia.

## 📦 Instalación

### Requisitos Previos
- Python 3.10 o superior
- PostgreSQL
- Token de bot de Telegram (de BotFather)

### Pasos de Instalación

1. **Clonar el repositorio**
   ```bash
   git clone https://github.com/tu-usuario/diana-bot-v2.git
   cd diana-bot-v2
   ```

2. **Crear entorno virtual**
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env con tus configuraciones
   ```

5. **Ejecutar migraciones de base de datos**
   ```bash
   alembic upgrade head
   ```

6. **Iniciar el bot**
   ```bash
   python -m src.bot
   ```

## 👩‍💻 Desarrollo

### Estructura del Proyecto

```
telegram-bot/
├── src/                        # Código fuente
│   └── bot/                    # Paquete del bot
│       ├── config/             # Configuración
│       ├── core/               # Componentes centrales
│       ├── database/           # Modelos y conexión a base de datos
│       ├── handlers/           # Manejadores de mensajes
│       ├── keyboards/          # Definiciones de teclados
│       ├── middlewares/        # Middlewares
│       ├── services/           # Lógica de negocio
│       ├── utils/              # Utilidades
│       └── tasks/              # Tareas programadas
├── tests/                      # Tests
│   ├── unit/                   # Tests unitarios
│   └── integration/            # Tests de integración
└── scripts/                    # Scripts de utilidad
```

### Convenciones de Código

- Utilizamos [Black](https://github.com/psf/black) para formateo de código
- Seguimos [PEP 8](https://www.python.org/dev/peps/pep-0008/) para estilo de código
- Utilizamos type hints en todas las funciones
- Escribimos docstrings para todas las clases y funciones públicas

### Ejecución de Tests

```bash
# Ejecutar todos los tests
pytest

# Ejecutar tests específicos
pytest tests/unit/
pytest tests/integration/

# Ver cobertura de tests
pytest --cov=src
```

## 📋 Progreso de Refactorización

El proyecto está en desarrollo activo. Para ver el estado actual, consulta [PROGRESS.md](PROGRESS.md).

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor, consulta nuestras guías de contribución antes de empezar.

## 📄 Licencia

Este proyecto está bajo licencia privada. Todos los derechos reservados.

## 👥 Equipo

Diana Bot V2 está siendo desarrollado por un equipo de agentes especializados en diferentes aspectos del sistema. Para más detalles, consulta [AGENTS.md](AGENTS.md).

---

⭐ **Diana Bot V2** - Haciendo que la interacción con bots sea más humana y emocionante.