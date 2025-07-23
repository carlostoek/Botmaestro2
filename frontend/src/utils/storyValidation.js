import { VALIDATION_MESSAGES } from './constants';

export const validateStoryFragment = (fragment, allFragments) => {
  const errors = [];
  const warnings = [];

  // Validar contenido
  if (!fragment.content || fragment.content.trim() === '') {
    errors.push(VALIDATION_MESSAGES.EMPTY_CONTENT);
  }

  // Validar ID
  if (!fragment.fragment_id || fragment.fragment_id.trim() === '') {
    errors.push(VALIDATION_MESSAGES.EMPTY_ID);
  }

  // Validar ID único
  const duplicateIds = allFragments.filter(f => 
    f.fragment_id === fragment.fragment_id && f !== fragment
  );
  if (duplicateIds.length > 0) {
    errors.push(VALIDATION_MESSAGES.DUPLICATE_ID);
  }

  // Validar decisiones
  fragment.decisions.forEach((decision, index) => {
    if (decision.next_fragment && decision.next_fragment.trim() !== '') {
      const targetExists = allFragments.some(f => f.fragment_id === decision.next_fragment);
      if (!targetExists) {
        errors.push(`Decisión ${index + 1}: ${VALIDATION_MESSAGES.INVALID_NEXT_FRAGMENT} (${decision.next_fragment})`);
      }
    }
  });

  return { errors, warnings };
};

export const validateStoryFlow = (fragments) => {
  const errors = [];
  const warnings = [];
  const fragmentIds = new Set(fragments.map(f => f.fragment_id));
  
  // Validar cada fragmento individualmente
  fragments.forEach(fragment => {
    const { errors: fragmentErrors, warnings: fragmentWarnings } = validateStoryFragment(fragment, fragments);
    errors.push(...fragmentErrors.map(err => `${fragment.fragment_id}: ${err}`));
    warnings.push(...fragmentWarnings.map(warn => `${fragment.fragment_id}: ${warn}`));
  });

  // Validar conexiones rotas
  fragments.forEach(fragment => {
    fragment.decisions.forEach((decision, decisionIndex) => {
      if (decision.next_fragment && !fragmentIds.has(decision.next_fragment)) {
        errors.push(`${fragment.fragment_id} (Decisión ${decisionIndex + 1}): ${VALIDATION_MESSAGES.BROKEN_CONNECTION} → ${decision.next_fragment}`);
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
      warnings.push(`${fragment.fragment_id}: ${VALIDATION_MESSAGES.ORPHANED_FRAGMENT}`);
    }
  });

  // Detectar referencias circulares
  const detectCircularReferences = (startId, visited = new Set(), path = []) => {
    if (visited.has(startId)) {
      const circleStart = path.indexOf(startId);
      if (circleStart !== -1) {
        const circle = path.slice(circleStart).join(' → ') + ' → ' + startId;
        errors.push(`${VALIDATION_MESSAGES.CIRCULAR_REFERENCE}: ${circle}`);
      }
      return;
    }

    visited.add(startId);
    path.push(startId);

    const fragment = fragments.find(f => f.fragment_id === startId);
    if (fragment) {
      fragment.decisions.forEach(decision => {
        if (decision.next_fragment) {
          detectCircularReferences(decision.next_fragment, new Set(visited), [...path]);
        }
      });
    }
  };

  fragments.forEach(fragment => {
    detectCircularReferences(fragment.fragment_id);
  });

  return {
    isValid: errors.length === 0,
    errors,
    warnings,
    stats: {
      totalFragments: fragments.length,
      brokenConnections: errors.filter(e => e.includes(VALIDATION_MESSAGES.BROKEN_CONNECTION)).length,
      orphanedFragments: warnings.filter(w => w.includes(VALIDATION_MESSAGES.ORPHANED_FRAGMENT)).length,
      circularReferences: errors.filter(e => e.includes(VALIDATION_MESSAGES.CIRCULAR_REFERENCE)).length
    }
  };
};

export const getFragmentReachability = (fragments) => {
  const reachable = new Set();
  const visited = new Set();
  
  const dfs = (fragmentId) => {
    if (visited.has(fragmentId)) return;
    visited.add(fragmentId);
    reachable.add(fragmentId);
    
    const fragment = fragments.find(f => f.fragment_id === fragmentId);
    if (fragment) {
      fragment.decisions.forEach(decision => {
        if (decision.next_fragment) {
          dfs(decision.next_fragment);
        }
      });
    }
  };
  
  // Comenzar desde el fragmento de inicio
  const startFragment = fragments.find(f => f.fragment_id === 'start') || fragments[0];
  if (startFragment) {
    dfs(startFragment.fragment_id);
  }
  
  return {
    reachableFragments: Array.from(reachable),
    unreachableFragments: fragments.filter(f => !reachable.has(f.fragment_id)).map(f => f.fragment_id)
  };
};

export const analyzeStoryFlow = (fragments) => {
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
    fragmentsByRole: fragments.reduce((acc, f) => {
      acc[f.required_role] = (acc[f.required_role] || 0) + 1;
      return acc;
    }, {}),
    rewardDistribution: {
      min: Math.min(...fragments.map(f => f.reward_besitos)),
      max: Math.max(...fragments.map(f => f.reward_besitos)),
      avg: fragments.reduce((acc, f) => acc + f.reward_besitos, 0) / fragments.length || 0,
      total: fragments.reduce((acc, f) => acc + f.reward_besitos, 0)
    },
    requirementDistribution: {
      min: Math.min(...fragments.map(f => f.required_besitos)),
      max: Math.max(...fragments.map(f => f.required_besitos)),
      avg: fragments.reduce((acc, f) => acc + f.required_besitos, 0) / fragments.length || 0,
      total: fragments.reduce((acc, f) => acc + f.required_besitos, 0)
    }
  };
  
  // Análisis de conectividad
  const reachabilityAnalysis = getFragmentReachability(fragments);
  analysis.reachability = reachabilityAnalysis;
  
  // Análisis de caminos
  const pathAnalysis = analyzeStoryPaths(fragments);
  analysis.paths = pathAnalysis;
  
  return analysis;
};

export const analyzeStoryPaths = (fragments) => {
  const paths = [];
  const visited = new Set();
  
  const findPaths = (fragmentId, currentPath = []) => {
    if (visited.has(fragmentId) || currentPath.includes(fragmentId)) {
      return; // Evitar ciclos infinitos
    }
    
    const fragment = fragments.find(f => f.fragment_id === fragmentId);
    if (!fragment) return;
    
    const newPath = [...currentPath, fragmentId];
    
    if (fragment.decisions.length === 0) {
      // Es un final
      paths.push(newPath);
      return;
    }
    
    fragment.decisions.forEach(decision => {
      if (decision.next_fragment) {
        findPaths(decision.next_fragment, newPath);
      }
    });
  };
  
  const startFragment = fragments.find(f => f.fragment_id === 'start') || fragments[0];
  if (startFragment) {
    findPaths(startFragment.fragment_id);
  }
  
  return {
    totalPaths: paths.length,
    averagePathLength: paths.reduce((acc, path) => acc + path.length, 0) / paths.length || 0,
    longestPath: paths.reduce((longest, current) => 
      current.length > longest.length ? current : longest, []),
    shortestPath: paths.reduce((shortest, current) => 
      current.length < shortest.length ? current : shortest, paths[0] || [])
  };
};