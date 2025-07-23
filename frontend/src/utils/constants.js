export const CHARACTERS = {
  LUCIEN: 'Lucien',
  DIANA: 'Diana'
};

export const ROLES = {
  NORMAL: 'normal',
  VIP: 'vip',
  PREMIUM: 'premium'
};

export const VALIDATION_MESSAGES = {
  EMPTY_CONTENT: 'El contenido no puede estar vacío',
  EMPTY_ID: 'El ID del fragmento no puede estar vacío',
  DUPLICATE_ID: 'Ya existe un fragmento con este ID',
  INVALID_NEXT_FRAGMENT: 'El fragmento de destino no existe',
  BROKEN_CONNECTION: 'Conexión rota detectada',
  ORPHANED_FRAGMENT: 'Fragmento sin referencias entrantes',
  CIRCULAR_REFERENCE: 'Referencia circular detectada'
};

export const DEFAULT_FRAGMENT = {
  fragment_id: '',
  content: '',
  character: CHARACTERS.LUCIEN,
  level: 1,
  required_besitos: 0,
  required_role: ROLES.NORMAL,
  reward_besitos: 0,
  decisions: [],
  position: { x: 100, y: 100 }
};

export const CHARACTER_COLORS = {
  [CHARACTERS.LUCIEN]: {
    bg: 'bg-blue-100',
    border: 'border-blue-300',
    text: 'text-blue-600',
    badge: 'bg-blue-500'
  },
  [CHARACTERS.DIANA]: {
    bg: 'bg-pink-100',
    border: 'border-pink-300',
    text: 'text-pink-600',
    badge: 'bg-pink-500'
  }
};

export const ROLE_COLORS = {
  [ROLES.NORMAL]: 'bg-gray-500',
  [ROLES.VIP]: 'bg-yellow-500',
  [ROLES.PREMIUM]: 'bg-purple-500'
};

export const CANVAS_SETTINGS = {
  GRID_SIZE: 20,
  MIN_ZOOM: 0.5,
  MAX_ZOOM: 2,
  ZOOM_STEP: 0.1,
  NODE_WIDTH: 250,
  NODE_HEIGHT: 150
};