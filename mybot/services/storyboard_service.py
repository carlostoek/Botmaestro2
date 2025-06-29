class StoryboardService:
    def __init__(self, db):
        self.db = db  # Conexión o interfaz a la base de datos

    # ... otros métodos de storyboard (por ejemplo, obtener escena por nombre, etc.)

    async def get_scene_by_id(self, scene_id: str):
        """Obtiene los datos completos de una escena por su ID."""
        query = "SELECT * FROM storyboard WHERE scene_id = %s"
        result = await self.db.fetch_one(query, (scene_id,))
        return result  # Se asume que `result` es un objeto con atributos de la escena o None

    async def get_conditions_by_type(self, trigger_type: str):
        """Obtiene todas las condiciones definidas para un tipo de disparador dado."""
        query = "SELECT trigger_type, trigger_value, scene_id FROM storyboard_conditions WHERE trigger_type = %s"
        return await self.db.fetch_all(query, (trigger_type,))

    async def get_condition(self, trigger_type: str, trigger_value: str):
        """Obtiene una condición específica (única) por tipo y valor de disparador."""
        query = """
            SELECT trigger_type, trigger_value, scene_id 
            FROM storyboard_conditions 
            WHERE trigger_type = %s AND trigger_value = %s
            LIMIT 1
        """
        return await self.db.fetch_one(query, (trigger_type, trigger_value))

    async def get_available_scenes(self, user_id: int, current_progress: int):
        """
        Obtiene las próximas escenas no vistas por el usuario, ordenadas por posición.
        `current_progress` típicamente es la posición de orden de la última escena vista.
        Retorna hasta 5 escenas siguientes que el usuario no haya visto.
        """
        query = """
            SELECT s.* 
            FROM storyboard s
            LEFT JOIN user_story_progress usp 
              ON usp.scene_id = s.scene_id AND usp.user_id = %s
            WHERE usp.scene_id IS NULL 
              AND s.order_position > %s
            ORDER BY s.order_position
            LIMIT 5
        """
        return await self.db.fetch_all(query, (user_id, current_progress))

    async def user_has_seen_scene(self, user_id: int, scene_id: str) -> bool:
        """Verifica si existe registro de que el usuario ya vio la escena dada."""
        query = "SELECT 1 FROM user_story_progress WHERE user_id = %s AND scene_id = %s"
        result = await self.db.fetch_one(query, (user_id, scene_id))
        return result is not None

    async def mark_scene_seen(self, user_id: int, scene_id: str):
        """Inserta un registro indicando que el usuario vio cierta escena (evita duplicados)."""
        query = """
            INSERT INTO user_story_progress (user_id, scene_id, seen_at)
            VALUES (%s, %s, NOW())
            ON CONFLICT (user_id, scene_id) DO NOTHING
        """
        await self.db.execute(query, (user_id, scene_id))

    async def get_user_max_order(self, user_id: int) -> int:
        """
        Obtiene el mayor order_position de las escenas que el usuario ya vio.
        Si no ha visto ninguna, devuelve 0.
        """
        query = """
            SELECT COALESCE(MAX(s.order_position), 0) AS max_order
            FROM storyboard s
            JOIN user_story_progress usp ON s.scene_id = usp.scene_id
            WHERE usp.user_id = %s
        """
        result = await self.db.fetch_one(query, (user_id,))
        if result:
            return result.max_order  # asumir que fetch_one devuelve un objeto con atributo max_order
        return 0
