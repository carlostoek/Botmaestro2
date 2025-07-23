import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Separator } from './ui/separator';
import { 
  Play, 
  RotateCcw, 
  Heart, 
  Crown, 
  User,
  ArrowLeft,
  BookOpen
} from 'lucide-react';

const StoryPreview = ({ fragments }) => {
  const [currentFragment, setCurrentFragment] = useState(null);
  const [storyHistory, setStoryHistory] = useState([]);
  const [userState, setUserState] = useState({
    besitos: 100,
    role: 'normal',
    level: 1
  });

  useEffect(() => {
    // Inicializar con el primer fragmento o uno de inicio
    const startFragment = fragments.find(f => f.fragment_id === 'start') || fragments[0];
    if (startFragment) {
      setCurrentFragment(startFragment);
      setStoryHistory([startFragment]);
    }
  }, [fragments]);

  const handleDecisionClick = (decision) => {
    const nextFragment = fragments.find(f => f.fragment_id === decision.next_fragment);
    if (nextFragment) {
      // Verificar requisitos
      if (nextFragment.required_besitos > userState.besitos) {
        alert(`Necesitas ${nextFragment.required_besitos} besitos para acceder a este fragmento`);
        return;
      }
      
      if (nextFragment.required_role === 'vip' && userState.role === 'normal') {
        alert('Necesitas ser VIP para acceder a este fragmento');
        return;
      }
      
      if (nextFragment.required_role === 'premium' && userState.role !== 'premium') {
        alert('Necesitas ser Premium para acceder a este fragmento');
        return;
      }
      
      // Actualizar estado del usuario
      setUserState(prev => ({
        ...prev,
        besitos: prev.besitos - nextFragment.required_besitos + nextFragment.reward_besitos
      }));
      
      // Cambiar al siguiente fragmento
      setCurrentFragment(nextFragment);
      setStoryHistory(prev => [...prev, nextFragment]);
    }
  };

  const handleRestart = () => {
    const startFragment = fragments.find(f => f.fragment_id === 'start') || fragments[0];
    setCurrentFragment(startFragment);
    setStoryHistory([startFragment]);
    setUserState({
      besitos: 100,
      role: 'normal',
      level: 1
    });
  };

  const handleGoBack = () => {
    if (storyHistory.length > 1) {
      const newHistory = storyHistory.slice(0, -1);
      setStoryHistory(newHistory);
      setCurrentFragment(newHistory[newHistory.length - 1]);
    }
  };

  const getCharacterColor = (character) => {
    return character === 'Lucien' ? 'text-blue-600' : 'text-pink-600';
  };

  const getCharacterBgColor = (character) => {
    return character === 'Lucien' ? 'bg-blue-50 border-blue-200' : 'bg-pink-50 border-pink-200';
  };

  const getRoleBadge = (role) => {
    const roleColors = {
      normal: 'bg-gray-500',
      vip: 'bg-yellow-500',
      premium: 'bg-purple-500'
    };
    return roleColors[role] || 'bg-gray-500';
  };

  if (!currentFragment) {
    return (
      <div className="h-full flex items-center justify-center bg-gray-50">
        <div className="text-center text-gray-500">
          <BookOpen className="h-12 w-12 mx-auto mb-4 opacity-50" />
          <p className="text-lg font-medium">No hay fragmentos para previsualizar</p>
          <p className="text-sm">Agrega algunos fragmentos para comenzar</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-4xl mx-auto h-full flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <h2 className="text-2xl font-bold text-gray-800 flex items-center gap-2">
              <Play className="h-6 w-6" />
              Previsualización de Historia
            </h2>
            <Badge variant="outline" className="text-sm">
              Fragmento {storyHistory.length} de {fragments.length}
            </Badge>
          </div>
          
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              onClick={handleGoBack}
              disabled={storyHistory.length <= 1}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Anterior
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRestart}
              className="flex items-center gap-2"
            >
              <RotateCcw className="h-4 w-4" />
              Reiniciar
            </Button>
          </div>
        </div>

        {/* User State */}
        <Card className="mb-6 bg-white shadow-sm">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-6">
                <div className="flex items-center gap-2">
                  <Heart className="h-5 w-5 text-red-500" />
                  <span className="font-medium">{userState.besitos}</span>
                  <span className="text-sm text-gray-500">besitos</span>
                </div>
                <div className="flex items-center gap-2">
                  <User className="h-5 w-5 text-gray-500" />
                  <Badge className={`${getRoleBadge(userState.role)} text-white`}>
                    {userState.role.toUpperCase()}
                  </Badge>
                </div>
              </div>
              
              <div className="flex items-center gap-2">
                <span className="text-sm text-gray-500">Cambiar rol:</span>
                <Select value={userState.role} onValueChange={(value) => setUserState(prev => ({ ...prev, role: value }))}>
                  <SelectTrigger className="w-32">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="normal">Normal</SelectItem>
                    <SelectItem value="vip">VIP</SelectItem>
                    <SelectItem value="premium">Premium</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Story Content */}
        <div className="flex-1 flex gap-6">
          {/* Main Story */}
          <div className="flex-1">
            <Card className={`h-full ${getCharacterBgColor(currentFragment.character)}`}>
              <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                  <CardTitle className={`text-xl ${getCharacterColor(currentFragment.character)}`}>
                    {currentFragment.character}
                  </CardTitle>
                  <div className="flex items-center gap-2">
                    <Badge variant="outline" className="text-xs">
                      Nivel {currentFragment.level}
                    </Badge>
                    <Badge variant="outline" className="text-xs">
                      {currentFragment.fragment_id}
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              
              <CardContent className="flex-1 flex flex-col justify-between">
                <div className="space-y-4">
                  <p className="text-gray-700 leading-relaxed text-lg">
                    {currentFragment.content}
                  </p>
                  
                  {/* Requirements */}
                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    {currentFragment.required_besitos > 0 && (
                      <div className="flex items-center gap-1">
                        <Heart className="h-4 w-4" />
                        Costo: {currentFragment.required_besitos}
                      </div>
                    )}
                    {currentFragment.reward_besitos > 0 && (
                      <div className="flex items-center gap-1 text-green-600">
                        <Heart className="h-4 w-4" />
                        Recompensa: +{currentFragment.reward_besitos}
                      </div>
                    )}
                    {currentFragment.required_role !== 'normal' && (
                      <div className="flex items-center gap-1">
                        <Crown className="h-4 w-4" />
                        Requiere: {currentFragment.required_role.toUpperCase()}
                      </div>
                    )}
                  </div>
                </div>
                
                {/* Decisions */}
                {currentFragment.decisions.length > 0 && (
                  <div className="space-y-3 mt-6">
                    <Separator />
                    <div className="space-y-2">
                      {currentFragment.decisions.map((decision, index) => {
                        const nextFragment = fragments.find(f => f.fragment_id === decision.next_fragment);
                        const canAccess = nextFragment && 
                          nextFragment.required_besitos <= userState.besitos &&
                          (nextFragment.required_role === 'normal' || 
                           (nextFragment.required_role === 'vip' && userState.role !== 'normal') ||
                           (nextFragment.required_role === 'premium' && userState.role === 'premium'));
                        
                        return (
                          <Button
                            key={index}
                            variant="outline"
                            className={`w-full justify-start text-left h-auto p-4 ${
                              canAccess ? 'hover:bg-blue-50' : 'opacity-50 cursor-not-allowed'
                            }`}
                            onClick={() => handleDecisionClick(decision)}
                            disabled={!canAccess}
                          >
                            <div className="flex-1">
                              <div className="font-medium">{decision.text}</div>
                              {nextFragment && (
                                <div className="text-xs text-gray-500 mt-1">
                                  → {nextFragment.fragment_id}
                                  {nextFragment.required_besitos > 0 && ` (${nextFragment.required_besitos} besitos)`}
                                  {nextFragment.required_role !== 'normal' && ` (${nextFragment.required_role.toUpperCase()})`}
                                </div>
                              )}
                            </div>
                          </Button>
                        );
                      })}
                    </div>
                  </div>
                )}
                
                {currentFragment.decisions.length === 0 && (
                  <div className="text-center py-6 text-gray-500">
                    <p className="text-sm">Fin de esta rama de la historia</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
          
          {/* History Sidebar */}
          <div className="w-64">
            <Card className="h-full">
              <CardHeader className="pb-4">
                <CardTitle className="text-lg">Historial</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {storyHistory.map((fragment, index) => (
                  <div
                    key={index}
                    className={`p-2 rounded-md text-sm ${
                      index === storyHistory.length - 1
                        ? 'bg-blue-100 border border-blue-200'
                        : 'bg-gray-50'
                    }`}
                  >
                    <div className="font-medium">{fragment.fragment_id}</div>
                    <div className="text-xs text-gray-500">{fragment.character}</div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default StoryPreview;