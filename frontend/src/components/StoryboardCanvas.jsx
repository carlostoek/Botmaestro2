import React, { useState, useRef, useCallback, useEffect } from 'react';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Trash2, Edit, Users, Star, Gift } from 'lucide-react';

const StoryboardCanvas = ({ 
  fragments, 
  selectedFragment, 
  onSelectFragment, 
  onUpdateFragment, 
  onDeleteFragment 
}) => {
  const canvasRef = useRef(null);
  const [draggedFragment, setDraggedFragment] = useState(null);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [connections, setConnections] = useState([]);
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });

  // Calcular conexiones entre fragmentos
  useEffect(() => {
    const newConnections = [];
    fragments.forEach(fragment => {
      fragment.decisions.forEach(decision => {
        if (decision.next_fragment) {
          const targetFragment = fragments.find(f => f.fragment_id === decision.next_fragment);
          if (targetFragment) {
            newConnections.push({
              from: fragment.fragment_id,
              to: decision.next_fragment,
              fromPos: fragment.position || { x: 100, y: 100 },
              toPos: targetFragment.position || { x: 300, y: 100 },
              label: decision.text
            });
          }
        }
      });
    });
    setConnections(newConnections);
  }, [fragments]);

  const handleMouseDown = useCallback((e, fragment) => {
    if (e.button === 0) { // Solo botón izquierdo
      const rect = canvasRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      setDraggedFragment(fragment);
      setDragOffset({
        x: x - (fragment.position?.x || 100),
        y: y - (fragment.position?.y || 100)
      });
    }
  }, []);

  const handleMouseMove = useCallback((e) => {
    if (draggedFragment) {
      const rect = canvasRef.current.getBoundingClientRect();
      const x = e.clientX - rect.left - dragOffset.x;
      const y = e.clientY - rect.top - dragOffset.y;
      
      const updatedFragment = {
        ...draggedFragment,
        position: { x, y }
      };
      
      onUpdateFragment(updatedFragment);
    }
  }, [draggedFragment, dragOffset, onUpdateFragment]);

  const handleMouseUp = useCallback(() => {
    setDraggedFragment(null);
    setDragOffset({ x: 0, y: 0 });
  }, []);

  const handleFragmentClick = useCallback((fragment) => {
    onSelectFragment(fragment);
  }, [onSelectFragment]);

  const getCharacterColor = (character) => {
    return character === 'Lucien' ? 'bg-blue-100 border-blue-300' : 'bg-pink-100 border-pink-300';
  };

  const getCharacterBadgeColor = (character) => {
    return character === 'Lucien' ? 'bg-blue-500' : 'bg-pink-500';
  };

  const renderConnection = (connection, index) => {
    const { fromPos, toPos, label } = connection;
    const startX = fromPos.x + 150; // Centro del nodo origen
    const startY = fromPos.y + 50;
    const endX = toPos.x;
    const endY = toPos.y + 50;
    
    // Crear una curva suave
    const controlX1 = startX + (endX - startX) * 0.3;
    const controlY1 = startY;
    const controlX2 = startX + (endX - startX) * 0.7;
    const controlY2 = endY;
    
    const pathData = `M ${startX} ${startY} C ${controlX1} ${controlY1}, ${controlX2} ${controlY2}, ${endX} ${endY}`;
    
    return (
      <g key={index}>
        <path
          d={pathData}
          stroke="#6366f1"
          strokeWidth="2"
          fill="none"
          strokeDasharray="5,5"
          className="opacity-70"
        />
        <circle
          cx={endX}
          cy={endY}
          r="4"
          fill="#6366f1"
        />
        {label && (
          <text
            x={startX + (endX - startX) * 0.5}
            y={startY + (endY - startY) * 0.5 - 10}
            textAnchor="middle"
            fontSize="12"
            fill="#6366f1"
            className="pointer-events-none select-none bg-white p-1 rounded"
          >
            {label.length > 20 ? label.substring(0, 20) + '...' : label}
          </text>
        )}
      </g>
    );
  };

  const renderFragment = (fragment) => {
    const position = fragment.position || { x: 100, y: 100 };
    const isSelected = selectedFragment?.fragment_id === fragment.fragment_id;
    
    return (
      <div
        key={fragment.fragment_id}
        className={`absolute cursor-move transition-all duration-200 ${
          isSelected ? 'ring-2 ring-blue-500 ring-offset-2' : ''
        }`}
        style={{
          left: position.x,
          top: position.y,
          transform: `scale(${zoom})`,
          transformOrigin: 'top left'
        }}
        onMouseDown={(e) => handleMouseDown(e, fragment)}
        onClick={() => handleFragmentClick(fragment)}
      >
        <Card className={`w-64 shadow-lg hover:shadow-xl transition-shadow ${getCharacterColor(fragment.character)}`}>
          <CardContent className="p-4">
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
              <Badge 
                className={`${getCharacterBadgeColor(fragment.character)} text-white text-xs`}
              >
                {fragment.character}
              </Badge>
              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteFragment(fragment.fragment_id);
                  }}
                  className="h-6 w-6 p-0 hover:bg-red-100 hover:text-red-600"
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>
            </div>

            {/* Content */}
            <div className="space-y-2 mb-3">
              <div className="text-sm font-medium text-gray-700">
                {fragment.fragment_id}
              </div>
              <div className="text-xs text-gray-600 line-clamp-2">
                {fragment.content}
              </div>
            </div>

            {/* Stats */}
            <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
              <div className="flex items-center gap-1">
                <Star className="h-3 w-3" />
                Lv. {fragment.level}
              </div>
              <div className="flex items-center gap-1">
                <Gift className="h-3 w-3" />
                {fragment.reward_besitos}
              </div>
            </div>

            {/* Decisions */}
            {fragment.decisions.length > 0 && (
              <div className="space-y-1">
                <div className="text-xs font-medium text-gray-700">
                  Decisiones:
                </div>
                {fragment.decisions.map((decision, index) => (
                  <div key={index} className="text-xs text-gray-600 bg-white bg-opacity-50 p-1 rounded">
                    {decision.text}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    );
  };

  return (
    <div 
      ref={canvasRef}
      className="w-full h-full bg-gray-50 relative overflow-hidden cursor-grab active:cursor-grabbing"
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
    >
      {/* Grid Background */}
      <div className="absolute inset-0 opacity-20">
        <svg width="100%" height="100%" className="pointer-events-none">
          <defs>
            <pattern id="grid" width="20" height="20" patternUnits="userSpaceOnUse">
              <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#e5e7eb" strokeWidth="1"/>
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      </div>

      {/* Connections */}
      <svg className="absolute inset-0 pointer-events-none" style={{ zIndex: 1 }}>
        {connections.map(renderConnection)}
      </svg>

      {/* Fragments */}
      <div className="relative" style={{ zIndex: 2 }}>
        {fragments.map(renderFragment)}
      </div>

      {/* Zoom Controls */}
      <div className="absolute bottom-4 right-4 flex flex-col gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setZoom(Math.min(zoom + 0.1, 2))}
          className="bg-white shadow-md"
        >
          +
        </Button>
        <div className="text-xs text-center bg-white px-2 py-1 rounded shadow-md">
          {Math.round(zoom * 100)}%
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setZoom(Math.max(zoom - 0.1, 0.5))}
          className="bg-white shadow-md"
        >
          -
        </Button>
      </div>

      {/* Instructions */}
      {fragments.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center text-gray-500">
            <Users className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <p className="text-lg font-medium">Tu storyboard está vacío</p>
            <p className="text-sm">Haz clic en "Nuevo Fragmento" para comenzar</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default StoryboardCanvas;