import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  RefreshCw,
  BarChart3,
  Network,
  Eye
} from 'lucide-react';

const FlowValidator = ({ fragments, validationResults, onValidate }) => {
  const [isValidating, setIsValidating] = useState(false);
  const [flowAnalysis, setFlowAnalysis] = useState(null);

  useEffect(() => {
    analyzeFlow();
  }, [fragments]);

  const analyzeFlow = () => {
    const analysis = {
      totalFragments: fragments.length,
      charactersUsed: [...new Set(fragments.map(f => f.character))],
      avgDecisionsPerFragment: fragments.reduce((acc, f) => acc + f.decisions.length, 0) / fragments.length || 0,
      fragmentsByLevel: fragments.reduce((acc, f) => {
        acc[f.level] = (acc[f.level] || 0) + 1;
        return acc;
      }, {}),
      fragmentsByCharacter: fragments.reduce((acc, f) => {
        acc[f.character] = (acc[f.character] || 0) + 1;
        return acc;
      }, {}),
      rewardDistribution: {
        min: Math.min(...fragments.map(f => f.reward_besitos)),
        max: Math.max(...fragments.map(f => f.reward_besitos)),
        avg: fragments.reduce((acc, f) => acc + f.reward_besitos, 0) / fragments.length || 0
      }
    };
    
    setFlowAnalysis(analysis);
  };

  const handleValidate = async () => {
    setIsValidating(true);
    // Simular proceso de validación
    await new Promise(resolve => setTimeout(resolve, 1000));
    onValidate();
    setIsValidating(false);
  };

  const getValidationIcon = (isValid) => {
    if (isValid) return <CheckCircle className="h-5 w-5 text-green-500" />;
    return <XCircle className="h-5 w-5 text-red-500" />;
  };

  const getValidationColor = (isValid) => {
    return isValid ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50';
  };

  const renderConnectionMap = () => {
    const connections = new Map();
    fragments.forEach(fragment => {
      connections.set(fragment.fragment_id, {
        ...fragment,
        connections: fragment.decisions.map(d => d.next_fragment).filter(Boolean)
      });
    });

    return (
      <div className="space-y-2">
        {Array.from(connections.entries()).map(([id, data]) => (
          <div key={id} className="flex items-center gap-2 text-sm">
            <Badge variant="outline" className="text-xs">
              {id}
            </Badge>
            <span className="text-gray-400">→</span>
            <div className="flex gap-1">
              {data.connections.length > 0 ? (
                data.connections.map((conn, idx) => (
                  <Badge key={idx} variant="secondary" className="text-xs">
                    {conn}
                  </Badge>
                ))
              ) : (
                <span className="text-gray-400 text-xs">sin conexiones</span>
              )}
            </div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="h-full bg-gray-50 p-6 overflow-y-auto">
      <div className="max-w-4xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Network className="h-6 w-6 text-blue-600" />
            <h2 className="text-2xl font-bold text-gray-800">Validador de Flujo</h2>
          </div>
          <Button
            onClick={handleValidate}
            disabled={isValidating}
            className="flex items-center gap-2"
          >
            <RefreshCw className={`h-4 w-4 ${isValidating ? 'animate-spin' : ''}`} />
            {isValidating ? 'Validando...' : 'Validar Flujo'}
          </Button>
        </div>

        {/* Validation Results */}
        {validationResults && (
          <Card className={`${getValidationColor(validationResults.isValid)}`}>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                {getValidationIcon(validationResults.isValid)}
                Resultados de Validación
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {/* Summary */}
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-blue-600">
                      {validationResults.stats.totalFragments}
                    </div>
                    <div className="text-sm text-gray-600">Fragmentos</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-red-600">
                      {validationResults.stats.brokenConnections}
                    </div>
                    <div className="text-sm text-gray-600">Conexiones Rotas</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-yellow-600">
                      {validationResults.stats.orphanedFragments}
                    </div>
                    <div className="text-sm text-gray-600">Fragmentos Huérfanos</div>
                  </div>
                </div>

                {/* Errors */}
                {validationResults.errors.length > 0 && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-red-700">
                      <XCircle className="h-4 w-4" />
                      <span className="font-medium">Errores ({validationResults.errors.length})</span>
                    </div>
                    <ul className="space-y-1">
                      {validationResults.errors.map((error, index) => (
                        <li key={index} className="text-sm text-red-600 bg-red-50 p-2 rounded">
                          {error}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Warnings */}
                {validationResults.warnings.length > 0 && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-yellow-700">
                      <AlertTriangle className="h-4 w-4" />
                      <span className="font-medium">Advertencias ({validationResults.warnings.length})</span>
                    </div>
                    <ul className="space-y-1">
                      {validationResults.warnings.map((warning, index) => (
                        <li key={index} className="text-sm text-yellow-600 bg-yellow-50 p-2 rounded">
                          {warning}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Success */}
                {validationResults.isValid && (
                  <div className="flex items-center gap-2 text-green-700 bg-green-50 p-3 rounded">
                    <CheckCircle className="h-4 w-4" />
                    <span className="font-medium">¡El flujo de la historia es válido!</span>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Flow Analysis */}
        {flowAnalysis && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Statistics */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <BarChart3 className="h-5 w-5" />
                  Estadísticas
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <div className="text-gray-600">Total Fragmentos</div>
                    <div className="text-lg font-semibold">{flowAnalysis.totalFragments}</div>
                  </div>
                  <div>
                    <div className="text-gray-600">Personajes</div>
                    <div className="text-lg font-semibold">{flowAnalysis.charactersUsed.length}</div>
                  </div>
                  <div>
                    <div className="text-gray-600">Decisiones Promedio</div>
                    <div className="text-lg font-semibold">{flowAnalysis.avgDecisionsPerFragment.toFixed(1)}</div>
                  </div>
                  <div>
                    <div className="text-gray-600">Recompensa Promedio</div>
                    <div className="text-lg font-semibold">{flowAnalysis.rewardDistribution.avg.toFixed(1)}</div>
                  </div>
                </div>

                {/* Character Distribution */}
                <div className="space-y-2">
                  <div className="text-sm font-medium text-gray-700">Distribución por Personaje</div>
                  {Object.entries(flowAnalysis.fragmentsByCharacter).map(([character, count]) => (
                    <div key={character} className="flex items-center justify-between text-sm">
                      <span className={character === 'Lucien' ? 'text-blue-600' : 'text-pink-600'}>
                        {character}
                      </span>
                      <Badge variant="outline">{count}</Badge>
                    </div>
                  ))}
                </div>

                {/* Level Distribution */}
                <div className="space-y-2">
                  <div className="text-sm font-medium text-gray-700">Distribución por Nivel</div>
                  {Object.entries(flowAnalysis.fragmentsByLevel).map(([level, count]) => (
                    <div key={level} className="flex items-center justify-between text-sm">
                      <span>Nivel {level}</span>
                      <Badge variant="outline">{count}</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Connection Map */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Network className="h-5 w-5" />
                  Mapa de Conexiones
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="max-h-96 overflow-y-auto">
                  {fragments.length > 0 ? renderConnectionMap() : (
                    <div className="text-center py-8 text-gray-500">
                      <Network className="h-8 w-8 mx-auto mb-2 opacity-50" />
                      <p className="text-sm">No hay fragmentos para analizar</p>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Acciones Rápidas</CardTitle>
          </CardHeader>
          <CardContent className="flex gap-3">
            <Button variant="outline" size="sm" onClick={handleValidate}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Revalidar
            </Button>
            <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
              <Eye className="h-4 w-4 mr-2" />
              Vista Previa
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default FlowValidator;