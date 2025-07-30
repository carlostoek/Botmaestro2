# Arquitectura del Bot Diana V2

Este documento describe la arquitectura implementada en la refactorización del bot Diana V2, junto con las decisiones técnicas tomadas.

## Visión General

Diana Bot V2 sigue una arquitectura en capas inspirada en los principios de Clean Architecture, enfocada en la separación de responsabilidades, la testabilidad, y la mantenibilidad del código.

## Capas de la Arquitectura

### 1. Capa de Presentación (Handlers y Keyboards)

**Responsabilidad**: Manejar interacciones directas con el usuario a través de Telegram.

**Componentes**:
- **Handlers**: Procesan comandos, mensajes y callbacks del usuario.
- **Keyboards**: Definen interfaces de usuario interactivas.

**Características**:
- Separación por dominio (usuarios, administradores, VIP)
- Manejo de estados para flujos de conversación complejos
- Respuestas formateadas según el contexto

### 2. Capa de Aplicación (Servicios)

**Responsabilidad**: Implementar la lógica de negocio y coordinar flujos entre componentes.

**Componentes**:
- **UserService**: Gestión de usuarios y perfiles.
- **EmotionalService**: Sistema emocional y relaciones con personajes.
- **NarrativeService**: Sistema narrativo con fragmentos de historia y opciones.
- **GamificationService**: Sistema de puntos, logros y misiones.

**Características**:
- Métodos enfocados en casos de uso
- Independiente de la fuente de datos
- Coordinación entre diferentes dominios

### 3. Capa de Dominio (Modelos y Lógica de Negocio)

**Responsabilidad**: Definir las entidades principales y la lógica de dominio.

**Componentes**:
- **Modelos de Dominio**: Definen entidades y relaciones del sistema.
- **Reglas de Negocio**: Implementan la lógica específica del dominio.

**Características**:
- Enfoque en las reglas y comportamientos del dominio
- Independiente de la tecnología de persistencia
- Define interfaces para servicios externos

### 4. Capa de Infraestructura (Base de Datos y Frameworks)

**Responsabilidad**: Proporcionar implementaciones técnicas para persistencia y servicios externos.

**Componentes**:
- **Database**: Implementación de acceso a datos con SQLAlchemy.
- **Middlewares**: Componentes que interceptan mensajes para procesamiento común.
- **External Services**: Integración con servicios externos.

**Características**:
- Conectores específicos para tecnologías
- Implementación de interfaces definidas en el dominio
- Manejo de detalles técnicos específicos

## Flujo de Datos

1. **Usuario envía un mensaje a Diana Bot**
2. **Telegram reenvía el mensaje a nuestro servidor**
3. **Middlewares procesan el mensaje**:
   - DatabaseMiddleware: Proporciona una sesión de base de datos
   - UserMiddleware: Asegura que el usuario existe
   - ThrottlingMiddleware: Limita la frecuencia de mensajes
   - EmotionalMiddleware: Procesa el impacto emocional
   - PointsMiddleware: Otorga puntos por interacción
4. **El Handler apropiado procesa el mensaje**
5. **El Service implementa la lógica de negocio**
6. **Se realizan operaciones en la base de datos**
7. **Se devuelve la respuesta al usuario**

## Patrones de Diseño Utilizados

### 1. Dependency Injection
Los servicios y dependencias se inyectan en handlers y middlewares, facilitando pruebas y desacoplamiento.

```python
async def handle_start(message: Message, session: AsyncSession, user_service: UserService):
    user = await user_service.get_user(session, message.from_user.id)
    # ...
```

### 2. Repository Pattern
Abstrae el acceso a datos a través de clases repository especializadas.

```python
class BaseService(Generic[T]):
    async def get_by_id(self, session: AsyncSession, id: Any) -> Optional[T]:
        return await session.get(self.model_class, id)
```

### 3. Factory Method
Utilizado para crear objetos complejos como teclados y componentes UI.

```python
class KeyboardFactory:
    def create_main_menu(self, user: User) -> InlineKeyboardMarkup:
        # ...
```

### 4. Middleware Pipeline
Procesamiento secuencial de solicitudes a través de una serie de middlewares.

```python
def setup_middlewares(dp: Dispatcher) -> None:
    dp.update.middleware(DatabaseMiddleware())
    dp.update.middleware(UserMiddleware())
    # ...
```

### 5. Service Layer
Encapsula la lógica de negocio en servicios especializados.

```python
class EmotionalService:
    async def process_message(self, session, user_id, character_name, message_text):
        # Implementación de lógica de negocio
```

## Estructuración del Código

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

## Características Técnicas Clave

### 1. Programación Asíncrona
Todo el código está escrito utilizando `async/await` para manejar operaciones de E/S sin bloquear el hilo principal.

```python
async def get_current_fragment(self, session: AsyncSession, user_id: int) -> Dict[str, Any]:
    state = await self.state_service.get_by_user(session, user_id)
    # ...
```

### 2. Tipado Estático
Uso extensivo de type hints para mejorar la seguridad del código y facilitar el desarrollo.

```python
def calculate_level(self, points: float) -> Dict[str, Any]:
    # ...
```

### 3. Manejo de Errores Centralizado
Sistema de manejo de errores centralizado para capturar y procesar excepciones.

```python
class ErrorHandler:
    async def handle_error(self, event: ErrorEvent):
        # ...
```

### 4. Configuración por Variables de Entorno
Configuración flexible basada en variables de entorno con valores predeterminados sensatos.

```python
class Settings(BaseSettings):
    BOT_TOKEN: str
    DATABASE_URL: PostgresDsn
    # ...
```

### 5. Logging Estructurado
Sistema de logging estructurado para facilitar el monitoreo y la depuración.

```python
logger = structlog.get_logger()
logger.info("Iniciando bot", version="2.0.0")
```

## Decisiones Técnicas

### 1. SQLAlchemy vs. ORM Simple
Se eligió SQLAlchemy por su flexibilidad, soporte para migraciones, y potentes características de consulta.

### 2. Aiogram 3.x vs. python-telegram-bot
Se eligió Aiogram 3.x por su diseño totalmente asíncrono, su API limpia, y su excelente soporte para FSM.

### 3. Estructura Modular vs. Monolítica
Se adoptó una estructura modular para facilitar la colaboración entre agentes especializados.

### 4. Patrón Repositorio vs. Acceso Directo a BD
Se implementó el patrón repositorio para abstraer el acceso a datos y facilitar pruebas.

### 5. Middleware vs. Lógica en Handlers
Se utilizaron middlewares para separar preocupaciones transversales como autenticación y throttling.

## Consideraciones de Escalabilidad

- **Conexiones de Base de Datos**: Configuradas con pool de conexiones para optimizar recursos.
- **Throttling**: Implementado para prevenir abusos y sobrecarga del sistema.
- **Manejo de Carga**: Diseñado para escalar horizontalmente si es necesario.
- **Background Tasks**: Separadas de la lógica principal para mejorar la responsividad.

## Aspectos de Seguridad

- **Validación de Entrada**: Validación estricta de todos los datos de entrada.
- **Manejo Seguro de Sesiones**: Sesiones de base de datos aisladas y con rollback automático.
- **Protección contra Abusos**: Rate limiting y monitoreo de comportamientos sospechosos.
- **Transacciones Seguras**: Operaciones críticas envueltas en transacciones.

## Próximas Mejoras Arquitectónicas

1. **Caché Distribuida**: Implementación de Redis para caché de datos frecuentes.
2. **Event Sourcing**: Para operaciones críticas que requieren auditabilidad.
3. **API REST**: Para posibles integraciones externas con panel de administración.
4. **Métricas y Monitoreo**: Sistema completo de telemetría con Prometheus.
5. **Contenerización**: Docker para simplificar despliegue y desarrollo.