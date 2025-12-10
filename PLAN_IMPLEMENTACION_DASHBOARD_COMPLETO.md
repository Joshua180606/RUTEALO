# Plan de Implementación Integral - Dashboard RUTEALO
**Fecha:** 2025-12-10  
**Estado:** En Progreso

---

## 📋 Resumen Ejecutivo

El dashboard actual tiene una estructura base funcional pero requiere refinamientos UI/UX críticos y mejoras en la lógica de flujo de examen. Este documento establece un roadmap completo de implementación.

---

## 🎯 Objetivos Principales

1. **UI/UX Mejorada:** Paneles con altura fija, scrolling interno, mejor balance visual
2. **Flujo de Examen:** Botón "Iniciar ruta" dispara examen inicial si está pendiente
3. **Validación de Datos:** Manejo robusto de estados y errores en frontend
4. **Accesibilidad:** Indicadores visuales claros del progreso
5. **Responsividad:** Funciona bien en móvil, tablet, desktop

---

## 📑 Detalles de Implementación

### **FASE 1: Mejoras de Layout (Inmediato)**

#### 1.1 Panel de Subida + Materiales con Altura Fija
**Objetivo:** Hacer que el área de subida/materiales tenga una altura máxima consistente con scroll interno.

**Cambios:**
- Establecer `height: 500px` o `max-height: 500px` en el contenedor principal `.col-md-4` y `.col-md-8`
- Añadir `overflow-y: auto` al card-body para permitir scroll interno
- Aplicar `height: 100%` al card para ocupar todo el espacio disponible

**Archivos:** `src/templates/dashboard.html` (estilos CSS)

**Código a agregar:**
```css
.panel-materiales-container {
    height: 500px;
    overflow-y: auto;
}

.panel-subida-container {
    height: 500px;
    display: flex;
    flex-direction: column;
}

.panel-subida-container .card-body {
    flex: 1;
    overflow-y: auto;
}
```

---

### **FASE 2: Lógica de Examen Inicial (Crítica)**

#### 2.1 Auto-Activación de Examen al Pulsar "Iniciar Ruta"
**Objetivo:** Cuando el usuario pulsa "Iniciar ruta de aprendizaje", si el examen está pendiente, mostrar el examen directamente sin mostrar la ruta.

**Cambios en JS:**
- Modificar `cargarEstadoRuta()` para check `examen_pendiente` PRIMERO
- Si está pendiente, saltarse `renderRuta()` y llamar directamente a `cargarExamenInicial()`
- Mejorar `renderExamen()` para dar feedback visual (spinner, validación, resumen de respuestas)

**Flujo mejorado:**
```
btnIniciarRuta click
  → fetch /ruta/estado
    → if examen_pendiente: mostrar examen y cargarExamenInicial()
    → else: mostrar ruta/flashcards
```

**Código a modificar:** Función `cargarEstadoRuta()` en `src/templates/dashboard.html`

---

### **FASE 3: Mejoras UX del Examen**

#### 3.1 Indicador de Progreso
**Objetivo:** Mostrar "Pregunta X de Y" mientras se responde el examen.

**Cambios:**
- Agregar contador visual en `renderExamen()`
- Mostrar % completado con progress bar

#### 3.2 Validación de Respuestas Incompletas
**Objetivo:** Evitar que el usuario envíe un examen sin responder todas las preguntas.

**Cambios:**
- En evento submit del form, validar que TODAS las preguntas tengan respuesta
- Mostrar alert o mensaje de error si falta alguna

#### 3.3 Spinner y Feedback Durante Envío
**Objetivo:** Mostrar loading mientras se procesa el examen.

**Cambios:**
- Desactivar botón submit durante el envío
- Mostrar spinner
- Mensaje de confirmación al completar

---

### **FASE 4: Validación de Estados**

#### 4.1 Estados Posibles en Backend (ya implementados)
- `examen_generado`: true/false (¿se creó el examen?)
- `examen_pendiente`: true/false (¿está sin completar?)
- `perfil_zdp`: null/dict (¿hay evaluación ZDP?)
- `ruta`: null/dict (¿existe la ruta?)

#### 4.2 Manejo de Cada Estado en Frontend
```javascript
if (!examen_generado) {
  // Mostrar: "Sube material para generar el examen"
}
if (examen_pendiente) {
  // Mostrar: Examen inicial
}
if (!examen_pendiente && examen_generado) {
  // Mostrar: Ruta + Flashcards
}
```

---

### **FASE 5: Mejoras de Ruta Personalizada**

#### 5.1 Renderizado Mejorado de Flashcards
**Objetivo:** Mostrar flashcards con flip animation y estado "visto".

**Cambios:**
- Implementar flip card CSS animation
- Contador de flashcards por nivel
- Marcador visual para nivel completado vs. en progreso

#### 5.2 Mini-Exámenes por Nivel
**Objetivo:** Permitir responder mini-exámenes inline en la ruta.

**Cambios:**
- Agregar modal o collapsible para mostrar examen de cada nivel
- Submit y guardar respuestas en backend
- Actualizar estado de competencia

#### 5.3 Filtrado de Niveles Dominados
**Objetivo:** Ocultar automáticamente niveles ya dominados (competent=true).

**Cambios:**
- Filtro en `renderRuta()`: `if (comp && comp.competente) return;`
- Mostrar badge "✅ Dominado" en niveles no mostrados
- Opción de expandir si el usuario quiere revisarlos

---

### **FASE 6: Mejoras de Datos y Persistencia**

#### 6.1 Historial de Exámenes
**Objetivo:** Guardar historial de intentos y puntajes.

**Cambios:**
- En `/examen-inicial/responder`, guardar respuestas en nueva colección `historico_examenes`
- Mostrar últimos 3 intentos en dashboard con puntajes y fechas

#### 6.2 Progreso de Ruta
**Objetivo:** Mostrar % completado en cada nivel.

**Cambios:**
- Agregar contador flashcards vistos vs. totales
- Agregar contador exámenes realizados vs. totales
- Progress bar por nivel

#### 6.3 Sincronización en Tiempo Real
**Objetivo:** Actualizar estado cuando se completa examen sin recargar página.

**Cambios:**
- Usar `setInterval()` o WebSockets para polling de estado cada 5 segundos
- Actualizar progreso dinámicamente

---

### **FASE 7: Mejoras de Accesibilidad**

#### 7.1 Labels y ARIA
**Objetivo:** Mejorar accesibilidad para lectores de pantalla.

**Cambios:**
- Agregar `aria-label` a botones
- Agregar `aria-live="polite"` a áreas que se actualizan
- Asegurar contraste de colores

#### 7.2 Navegación por Teclado
**Objetivo:** Permitir navegación con Tab y Enter.

**Cambios:**
- Asegurar que todos los botones sean focusables
- Permitir Enter en radio buttons
- Agregar tecla Escape para cerrar modales

---

### **FASE 8: Manejo de Errores y Edge Cases**

#### 8.1 Errores de Fetch
**Objetivo:** Manejar fallos de red con reintentos y mensajes claros.

**Cambios:**
- Wrap fetch en try-catch mejorado
- Mostrar toasts de error/advertencia
- Opción de reintentar

#### 8.2 Estados Inconsistentes
**Objetivo:** Validar que los datos devueltos por API tengan estructura esperada.

**Cambios:**
- Validar JSON antes de usar
- Fallbacks para campos faltantes
- Logs de error en consola

#### 8.3 Timeout
**Objetivo:** Evitar que la UI se "cuelgue" esperando respuesta.

**Cambios:**
- Agregar timeout a fetch (AbortController)
- Mostrar mensaje después de N segundos
- Opción de cancelar/reintentar

---

### **FASE 9: Optimizaciones de Performance**

#### 9.1 Lazy Loading
**Objetivo:** No cargar examen/ruta hasta que el usuario lo solicite.

**Cambios:**
- Cargar en demanda (ya implementado con click)
- Cachear resultados para no refetch innecesario

#### 9.2 Debouncing
**Objetivo:** Evitar requests múltiples si el usuario hace click varias veces.

**Cambios:**
- Agregar flag `isLoading` para desactivar botón durante fetch
- Usar debounce en eventos de click

---

### **FASE 10: Mejoras Visuales**

#### 10.1 Temas y Colores
**Objetivo:** Mejorar paleta de colores y coherencia visual.

**Cambios:**
- Usar colores consistentes para niveles Bloom
- Agregar gradientes sutiles
- Iconos emoji más consistentes (o reemplazar por Font Awesome)

#### 10.2 Animaciones
**Objetivo:** Transiciones suaves entre estados.

**Cambios:**
- Fade-in/fade-out para examen y ruta
- Slide animación para niveles
- Skeleton loaders mientras se carga contenido

#### 10.3 Espaciado y Tipografía
**Objetivo:** Mejorar legibilidad.

**Cambios:**
- Ajustar font-size en diferentes secciones
- Mejorar line-height para mejor legibilidad
- Espaciado consistente

---

## 🔄 Priorización

### **CRÍTICOS (Implementar Ya)**
1. Altura fija + scroll en paneles de subida/materiales
2. Auto-trigger examen inicial al pulsar "Iniciar ruta"
3. Validación de respuestas incompletas
4. Manejo robusto de errores en fetch

### **IMPORTANTE (Próxima Iteración)**
5. Indicadores de progreso (Pregunta X de Y)
6. Filtrado de niveles dominados
7. Spinner/loading estados
8. Historial de exámenes

### **NICE-TO-HAVE (Futuro)**
9. Flip cards animation
10. Sincronización en tiempo real
11. Accesibilidad mejorada
12. Performance optimizations

---

## 📝 Checklist de Implementación

- [ ] Altura fija en paneles
- [ ] Auto-trigger examen
- [ ] Validación de respuestas
- [ ] Manejo de errores mejorado
- [ ] Indicadores de progreso
- [ ] Spinner/loading
- [ ] Pruebas manuales en navegador
- [ ] Pruebas en móvil (responsive)
- [ ] Validación de datos en backend
- [ ] Documentación actualizada

---

## 📚 Archivos Afectados

| Archivo | Cambios |
|---------|---------|
| `src/templates/dashboard.html` | Estilos CSS, lógica JS |
| `src/app.py` | Posibles nuevos endpoints (historial, etc.) |
| `src/web_utils.py` | Funciones helper si es necesario |

---

## 🚀 Próximos Pasos

1. Implementar FASE 1 (Altura fija)
2. Implementar FASE 2 (Auto-trigger examen)
3. Implementar FASE 3 (Indicadores UX)
4. Probar en navegador
5. Recopilar feedback
6. Iterar sobre FASES 4-10 según prioridad

