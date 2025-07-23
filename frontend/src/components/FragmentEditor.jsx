import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Plus, Trash2, Save, AlertCircle } from 'lucide-react';
import { toast } from '../hooks/use-toast';

const FragmentEditor = ({ fragment, onUpdateFragment, onDeleteFragment, fragments }) => {
  const [editedFragment, setEditedFragment] = useState(fragment);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    setEditedFragment(fragment);
    setHasChanges(false);
  }, [fragment]);

  const handleFieldChange = (field, value) => {
    setEditedFragment(prev => ({
      ...prev,
      [field]: value
    }));
    setHasChanges(true);
  };

  const handleDecisionChange = (index, field, value) => {
    setEditedFragment(prev => ({
      ...prev,
      decisions: prev.decisions.map((decision, i) => 
        i === index ? { ...decision, [field]: value } : decision
      )
    }));
    setHasChanges(true);
  };

  const handleAddDecision = () => {
    setEditedFragment(prev => ({
      ...prev,
      decisions: [...prev.decisions, { text: '', next_fragment: '' }]
    }));
    setHasChanges(true);
  };

  const handleRemoveDecision = (index) => {
    setEditedFragment(prev => ({
      ...prev,
      decisions: prev.decisions.filter((_, i) => i !== index)
    }));
    setHasChanges(true);
  };

  const handleSave = () => {
    onUpdateFragment(editedFragment);
    setHasChanges(false);
    toast({
      title: "Fragmento guardado",
      description: "Los cambios han sido guardados exitosamente"
    });
  };

  const handleDelete = () => {
    onDeleteFragment(fragment.fragment_id);
    toast({
      title: "Fragmento eliminado",
      description: "El fragmento ha sido eliminado correctamente"
    });
  };

  const getAvailableFragments = () => {
    return fragments.filter(f => f.fragment_id !== fragment.fragment_id);
  };

  const validateFragment = () => {
    const errors = [];
    
    if (!editedFragment.content.trim()) {
      errors.push("El contenido no puede estar vacío");
    }
    
    if (!editedFragment.fragment_id.trim()) {
      errors.push("El ID del fragmento no puede estar vacío");
    }
    
    // Validar que los next_fragment existan
    editedFragment.decisions.forEach((decision, index) => {
      if (decision.next_fragment && !fragments.find(f => f.fragment_id === decision.next_fragment)) {
        errors.push(`Decisión ${index + 1}: El fragmento "${decision.next_fragment}" no existe`);
      }
    });
    
    return errors;
  };

  const validationErrors = validateFragment();

  return (
    <div className="h-full overflow-y-auto">
      <Card className="m-4 mb-0">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg flex items-center justify-between">
            Editor de Fragmento
            <Badge variant="outline" className="text-xs">
              {fragment.fragment_id}
            </Badge>
          </CardTitle>
        </CardHeader>
        
        <CardContent className="space-y-4">
          {/* Validation Errors */}
          {validationErrors.length > 0 && (
            <div className="bg-red-50 border border-red-200 rounded-md p-3">
              <div className="flex items-center gap-2 text-red-700 mb-2">
                <AlertCircle className="h-4 w-4" />
                <span className="text-sm font-medium">Errores de validación:</span>
              </div>
              <ul className="text-sm text-red-600 space-y-1">
                {validationErrors.map((error, index) => (
                  <li key={index}>• {error}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Fragment ID */}
          <div className="space-y-2">
            <Label htmlFor="fragment_id">ID del Fragmento</Label>
            <Input
              id="fragment_id"
              value={editedFragment.fragment_id}
              onChange={(e) => handleFieldChange('fragment_id', e.target.value)}
              className="font-mono text-sm"
            />
          </div>

          {/* Content */}
          <div className="space-y-2">
            <Label htmlFor="content">Contenido</Label>
            <Textarea
              id="content"
              value={editedFragment.content}
              onChange={(e) => handleFieldChange('content', e.target.value)}
              rows={4}
              className="resize-none"
            />
          </div>

          {/* Character */}
          <div className="space-y-2">
            <Label htmlFor="character">Personaje</Label>
            <Select 
              value={editedFragment.character} 
              onValueChange={(value) => handleFieldChange('character', value)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Selecciona un personaje" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="Lucien">Lucien</SelectItem>
                <SelectItem value="Diana">Diana</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Level and Requirements */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="level">Nivel</Label>
              <Input
                id="level"
                type="number"
                value={editedFragment.level}
                onChange={(e) => handleFieldChange('level', parseInt(e.target.value) || 0)}
                min="1"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="required_besitos">Besitos Requeridos</Label>
              <Input
                id="required_besitos"
                type="number"
                value={editedFragment.required_besitos}
                onChange={(e) => handleFieldChange('required_besitos', parseInt(e.target.value) || 0)}
                min="0"
              />
            </div>
          </div>

          {/* Role and Reward */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="required_role">Rol Requerido</Label>
              <Select 
                value={editedFragment.required_role} 
                onValueChange={(value) => handleFieldChange('required_role', value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Selecciona un rol" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="normal">Normal</SelectItem>
                  <SelectItem value="vip">VIP</SelectItem>
                  <SelectItem value="premium">Premium</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label htmlFor="reward_besitos">Recompensa Besitos</Label>
              <Input
                id="reward_besitos"
                type="number"
                value={editedFragment.reward_besitos}
                onChange={(e) => handleFieldChange('reward_besitos', parseInt(e.target.value) || 0)}
                min="0"
              />
            </div>
          </div>

          <Separator />

          {/* Decisions */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label className="text-base font-medium">Decisiones</Label>
              <Button
                variant="outline"
                size="sm"
                onClick={handleAddDecision}
                className="flex items-center gap-2"
              >
                <Plus className="h-4 w-4" />
                Agregar
              </Button>
            </div>

            {editedFragment.decisions.map((decision, index) => (
              <Card key={index} className="p-3 bg-gray-50">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <Label className="text-sm font-medium">Decisión {index + 1}</Label>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveDecision(index)}
                      className="h-6 w-6 p-0 hover:bg-red-100 hover:text-red-600"
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor={`decision-text-${index}`}>Texto</Label>
                    <Input
                      id={`decision-text-${index}`}
                      value={decision.text}
                      onChange={(e) => handleDecisionChange(index, 'text', e.target.value)}
                      placeholder="Texto de la decisión"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor={`decision-next-${index}`}>Siguiente Fragmento</Label>
                    <Select 
                      value={decision.next_fragment} 
                      onValueChange={(value) => handleDecisionChange(index, 'next_fragment', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="Selecciona fragmento destino" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="">Sin conexión</SelectItem>
                        {getAvailableFragments().map(f => (
                          <SelectItem key={f.fragment_id} value={f.fragment_id}>
                            {f.fragment_id}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </Card>
            ))}

            {editedFragment.decisions.length === 0 && (
              <div className="text-center py-6 text-gray-500">
                <p className="text-sm">No hay decisiones configuradas</p>
                <p className="text-xs">Haz clic en "Agregar" para crear una nueva decisión</p>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex gap-2 pt-4">
            <Button
              onClick={handleSave}
              disabled={!hasChanges || validationErrors.length > 0}
              className="flex-1 flex items-center gap-2"
            >
              <Save className="h-4 w-4" />
              Guardar
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              className="flex items-center gap-2"
            >
              <Trash2 className="h-4 w-4" />
              Eliminar
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default FragmentEditor;