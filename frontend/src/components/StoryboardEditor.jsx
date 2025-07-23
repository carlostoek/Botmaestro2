import React, { useState, useRef, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Textarea } from './ui/textarea';
import { Badge } from './ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { toast } from '../hooks/use-toast';
import { 
  Download, 
  Upload, 
  Play, 
  Save, 
  Plus, 
  Trash2, 
  AlertCircle, 
  CheckCircle,
  Eye,
  FileText,
  Workflow
} from 'lucide-react';
import StoryboardCanvas from './StoryboardCanvas';
import FragmentEditor from './FragmentEditor';
import StoryPreview from './StoryPreview';
import FlowValidator from './FlowValidator';
import { mockStoryData } from '../data/mockData';

const StoryboardEditor = () => {
  const [storyData, setStoryData] = useState(mockStoryData);
  const [selectedFragment, setSelectedFragment] = useState(null);
  const [activeTab, setActiveTab] = useState('editor');
  const [validationResults, setValidationResults] = useState(null);
  const [previewMode, setPreviewMode] = useState(false);
  const fileInputRef = useRef(null);

  const handleAddFragment = useCallback(() => {
    const newFragment = {
      fragment_id: `fragment_${Date.now()}`,
      content: 'Nuevo fragmento de historia',
      character: 'Lucien',
      level: 1,
      required_besitos: 0,
      required_role: 'normal',
      reward_besitos: 0,
      decisions: [],
      position: { x: 100, y: 100 }
    };
    
    setStoryData(prev => ({
      ...prev,
      fragments: [...prev.fragments, newFragment]
    }));
    
    toast({
      title: "Fragmento agregado",
      description: "Nuevo fragmento creado exitosamente"
    });
  }, []);

  const handleDeleteFragment = useCallback((fragmentId) => {
    setStoryData(prev => ({
      ...prev,
      fragments: prev.fragments.filter(f => f.fragment_id !== fragmentId)
    }));
    
    if (selectedFragment?.fragment_id === fragmentId) {
      setSelectedFragment(null);
    }
    
    toast({
      title: "Fragmento eliminado",
      description: "El fragmento ha sido eliminado correctamente"
    });
  }, [selectedFragment]);

  const handleUpdateFragment = useCallback((updatedFragment) => {
    setStoryData(prev => ({
      ...prev,
      fragments: prev.fragments.map(f => 
        f.fragment_id === updatedFragment.fragment_id ? updatedFragment : f
      )
    }));
  }, []);

  const handleValidateFlow = useCallback(() => {
    const results = validateStoryFlow(storyData.fragments);
    setValidationResults(results);
    
    if (results.isValid) {
      toast({
        title: "Validación exitosa",
        description: "El flujo de la historia es válido"
      });
    } else {
      toast({
        title: "Errores encontrados",
        description: `${results.errors.length} errores en el flujo`,
        variant: "destructive"
      });
    }
  }, [storyData]);

  const handleExportJSON = useCallback(() => {
    const dataStr = JSON.stringify(storyData, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = 'storyboard.json';
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
    
    toast({
      title: "Archivo exportado",
      description: "El storyboard ha sido exportado exitosamente"
    });
  }, [storyData]);

  const handleImportJSON = useCallback((event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        try {
          const imported = JSON.parse(e.target.result);
          setStoryData(imported);
          toast({
            title: "Archivo importado",
            description: "El storyboard ha sido importado exitosamente"
          });
        } catch (error) {
          toast({
            title: "Error de importación",
            description: "El archivo no tiene un formato JSON válido",
            variant: "destructive"
          });
        }
      };
      reader.readAsText(file);
    }
  }, []);

  const validateStoryFlow = (fragments) => {
    const errors = [];
    const warnings = [];
    const fragmentIds = new Set(fragments.map(f => f.fragment_id));
    
    // Validar conexiones rotas
    fragments.forEach(fragment => {
      fragment.decisions.forEach(decision => {
        if (decision.next_fragment && !fragmentIds.has(decision.next_fragment)) {
          errors.push(`Fragmento ${fragment.fragment_id}: Decisión "${decision.text}" apunta a un fragmento inexistente: ${decision.next_fragment}`);
        }
      });
    });
    
    // Validar fragmentos huérfanos
    const referencedFragments = new Set();
    fragments.forEach(fragment => {
      fragment.decisions.forEach(decision => {
        if (decision.next_fragment) {
          referencedFragments.add(decision.next_fragment);
        }
      });
    });
    
    fragments.forEach(fragment => {
      if (!referencedFragments.has(fragment.fragment_id) && fragment.fragment_id !== 'start') {
        warnings.push(`Fragmento ${fragment.fragment_id} no tiene referencias entrantes`);
      }
    });
    
    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      stats: {
        totalFragments: fragments.length,
        brokenConnections: errors.length,
        orphanedFragments: warnings.length
      }
    };
  };

  return (
    <div className="h-screen bg-gradient-to-br from-slate-50 to-slate-100 flex flex-col">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-slate-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Workflow className="h-8 w-8 text-blue-600" />
              <h1 className="text-2xl font-bold text-slate-800">Storyboard Editor</h1>
            </div>
            <Badge variant="outline" className="text-sm">
              {storyData.fragments.length} fragmentos
            </Badge>
          </div>
          
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => fileInputRef.current?.click()}
              className="flex items-center gap-2"
            >
              <Upload className="h-4 w-4" />
              Importar
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleExportJSON}
              className="flex items-center gap-2"
            >
              <Download className="h-4 w-4" />
              Exportar
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleValidateFlow}
              className="flex items-center gap-2"
            >
              <CheckCircle className="h-4 w-4" />
              Validar
            </Button>
            
            <Button
              variant="default"
              size="sm"
              onClick={handleAddFragment}
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700"
            >
              <Plus className="h-4 w-4" />
              Nuevo Fragmento
            </Button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex">
        {/* Canvas Area */}
        <div className="flex-1 relative">
          <Tabs value={activeTab} onValueChange={setActiveTab} className="h-full">
            <TabsList className="absolute top-4 left-4 z-10 bg-white shadow-md">
              <TabsTrigger value="editor" className="flex items-center gap-2">
                <Workflow className="h-4 w-4" />
                Editor
              </TabsTrigger>
              <TabsTrigger value="preview" className="flex items-center gap-2">
                <Eye className="h-4 w-4" />
                Previsualización
              </TabsTrigger>
              <TabsTrigger value="validation" className="flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Validación
              </TabsTrigger>
            </TabsList>

            <TabsContent value="editor" className="h-full m-0">
              <StoryboardCanvas 
                fragments={storyData.fragments}
                selectedFragment={selectedFragment}
                onSelectFragment={setSelectedFragment}
                onUpdateFragment={handleUpdateFragment}
                onDeleteFragment={handleDeleteFragment}
              />
            </TabsContent>

            <TabsContent value="preview" className="h-full m-0">
              <StoryPreview fragments={storyData.fragments} />
            </TabsContent>

            <TabsContent value="validation" className="h-full m-0">
              <FlowValidator 
                fragments={storyData.fragments}
                validationResults={validationResults}
                onValidate={handleValidateFlow}
              />
            </TabsContent>
          </Tabs>
        </div>

        {/* Right Panel */}
        {selectedFragment && (
          <div className="w-80 bg-white shadow-lg border-l border-slate-200 overflow-y-auto">
            <FragmentEditor
              fragment={selectedFragment}
              onUpdateFragment={handleUpdateFragment}
              onDeleteFragment={handleDeleteFragment}
              fragments={storyData.fragments}
            />
          </div>
        )}
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".json"
        onChange={handleImportJSON}
        className="hidden"
      />
    </div>
  );
};

export default StoryboardEditor;