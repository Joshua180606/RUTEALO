"""
Funciones especializadas para generación de flashcards y tests con teoría pedagógica
Autor: Sistema RUTEALO - Fase 2
Fecha: 2024-12-10

OBJETIVO: Crear funciones dedicadas que usen marcos pedagógicos (CSV) para generar:
- Flashcards con conceptos teóricos explícitos
- Tests con feedback diferenciado según estrategia ZDP
"""

import json
import re
import logging
from src.config import get_genai_model
from src.utils import retry

logger = logging.getLogger(__name__)
model = get_genai_model()


@retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(Exception,))
def generar_flashcards_con_teoria(nivel_bloom, textos_nivel, estrategia="estandar", marcos=None):
    """Genera flashcards especializadas usando marcos pedagógicos.
    
    Args:
        nivel_bloom (str): Nivel cognitivo de Bloom
        textos_nivel (list): Contenido del estudiante para este nivel
        estrategia (str): 'scaffolding', 'refuerzo' o 'estandar'
        marcos (dict): Marcos pedagógicos {bloom, zdp, flow} o None
    
    Returns:
        list: Flashcards con estructura [{"id": int, "frente": str, "reverso": str, "visto": bool}]
    """
    if not textos_nivel:
        return []
    
    # Determinar cantidad según estrategia
    num_flashcards = {
        "scaffolding": 5,
        "refuerzo": 7,
        "estandar": 3
    }.get(estrategia, 3)
    
    # Construir contexto pedagógico desde CSV
    contexto_pedagogico = _construir_contexto_pedagogico(nivel_bloom, marcos)
    
    # Instrucciones específicas por estrategia
    instrucciones_estrategia = _obtener_instrucciones_flashcards(estrategia)
    
    texto_combinado = "\n".join(textos_nivel)[:8000]
    
    prompt = f"""
    Eres un experto en diseño instruccional con especialización en Taxonomía de Bloom.
    
    NIVEL COGNITIVO: {nivel_bloom}
    ESTRATEGIA: {estrategia.upper()}
    
    {contexto_pedagogico}
    
    {instrucciones_estrategia}
    
    CONTENIDO DEL ESTUDIANTE:
    {texto_combinado}
    
    TAREAS:
    1. Genera {num_flashcards} FLASHCARDS para nivel {nivel_bloom}
    2. Cada flashcard debe tener:
       - FRENTE: Pregunta/concepto clave que active procesos cognitivos de {nivel_bloom}
       - REVERSO: Respuesta completa CON TEORÍA EXPLÍCITA del material
    
    3. Distribuye tipos de flashcards:
       - Definiciones: "¿Qué es X según el material?"
       - Relaciones: "¿Cómo se relaciona X con Y?"
       - Procedimientos: "¿Cuál es el paso siguiente después de X?"
       - Ejemplos: "Provee un ejemplo de X del material"
    
    FORMATO JSON OBLIGATORIO:
    {{
        "FLASHCARDS": [
            {{
                "id": 1,
                "frente": "Pregunta activadora del nivel {nivel_bloom}",
                "reverso": "Respuesta completa con teoría extraída del material. Debe incluir definiciones, ejemplos y contexto.",
                "visto": false
            }}
        ]
    }}
    
    CRÍTICO: El reverso debe contener TEORÍA EXPLÍCITA, no solo respuestas cortas.
    """
    
    try:
        res = model.generate_content(prompt)
        text_clean = re.sub(r"```json|```", "", res.text).strip()
        data = json.loads(text_clean)
        
        flashcards = data.get("FLASHCARDS", [])
        logger.info(f"✅ Generadas {len(flashcards)} flashcards para {nivel_bloom} ({estrategia})")
        return flashcards
        
    except Exception as e:
        logger.error(f"❌ Error generando flashcards para {nivel_bloom}: {e}")
        return []


@retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(Exception,))
def generar_tests_con_teoria(nivel_bloom, textos_nivel, estrategia="estandar", marcos=None):
    """Genera tests con feedback diferenciado usando marcos pedagógicos.
    
    Args:
        nivel_bloom (str): Nivel cognitivo de Bloom
        textos_nivel (list): Contenido del estudiante para este nivel
        estrategia (str): 'scaffolding', 'refuerzo' o 'estandar'
        marcos (dict): Marcos pedagógicos {bloom, zdp, flow} o None
    
    Returns:
        list: Tests con estructura [{"id": int, "pregunta": str, "opciones": list, 
                                     "respuesta_correcta": str, "feedback": dict, "realizado": bool}]
    """
    if not textos_nivel:
        return []
    
    # Determinar cantidad según estrategia
    num_preguntas = {
        "scaffolding": 4,
        "refuerzo": 5,
        "estandar": 3
    }.get(estrategia, 3)
    
    # Construir contexto pedagógico
    contexto_pedagogico = _construir_contexto_pedagogico(nivel_bloom, marcos)
    
    # Instrucciones específicas por estrategia
    instrucciones_estrategia = _obtener_instrucciones_tests(estrategia)
    
    texto_combinado = "\n".join(textos_nivel)[:8000]
    
    prompt = f"""
    Eres un experto en evaluación formativa con especialización en feedback pedagógico.
    
    NIVEL COGNITIVO: {nivel_bloom}
    ESTRATEGIA: {estrategia.upper()}
    
    {contexto_pedagogico}
    
    {instrucciones_estrategia}
    
    CONTENIDO DEL ESTUDIANTE:
    {texto_combinado}
    
    TAREAS:
    1. Genera {num_preguntas} PREGUNTAS para nivel {nivel_bloom}
    2. Cada pregunta debe tener:
       - Enunciado claro que evalúe procesos cognitivos de {nivel_bloom}
       - 4 opciones (a, b, c, d) con distractores plausibles
       - 1 respuesta correcta
       - FEEDBACK DIFERENCIADO para cada opción (correcto/incorrecto)
    
    3. El feedback debe incluir:
       - Para correcta: Refuerzo positivo + explicación breve
       - Para incorrectas: Pista de por qué es incorrecta + dirección hacia concepto correcto
    
    FORMATO JSON OBLIGATORIO:
    {{
        "EXAMENES": [
            {{
                "id": 1,
                "pregunta": "Pregunta que evalúa {nivel_bloom} basada en el material",
                "opciones": [
                    "a) Opción correcta",
                    "b) Distractor plausible relacionado",
                    "c) Otro distractor",
                    "d) Tercer distractor"
                ],
                "respuesta_correcta": "a",
                "feedback": {{
                    "a": "¡Correcto! Esta es la respuesta porque... [explicación con teoría]",
                    "b": "Incorrecto. Esta opción confunde X con Y. Revisa el concepto de... [pista]",
                    "c": "Incorrecto. Aunque esto es cierto para Z, la pregunta se refiere a... [pista]",
                    "d": "Incorrecto. Esta afirmación contradice el principio de... [pista]"
                }},
                "realizado": false
            }}
        ]
    }}
    
    CRÍTICO: El feedback debe ser PEDAGÓGICO, no solo "correcto/incorrecto".
    """
    
    try:
        res = model.generate_content(prompt)
        text_clean = re.sub(r"```json|```", "", res.text).strip()
        data = json.loads(text_clean)
        
        tests = data.get("EXAMENES", [])
        logger.info(f"✅ Generadas {len(tests)} preguntas para {nivel_bloom} ({estrategia})")
        return tests
        
    except Exception as e:
        logger.error(f"❌ Error generando tests para {nivel_bloom}: {e}")
        return []


def _construir_contexto_pedagogico(nivel_bloom, marcos):
    """Construye contexto pedagógico desde marcos CSV.
    
    Args:
        nivel_bloom (str): Nivel cognitivo
        marcos (dict): {bloom: DataFrame, zdp: DataFrame, flow: DataFrame} o None
    
    Returns:
        str: Contexto pedagógico formateado
    """
    if not marcos:
        return ""
    
    contexto = ""
    
    # Marco Bloom: Procesos cognitivos
    if marcos.get("bloom") is not None:
        fila_bloom = marcos["bloom"][marcos["bloom"]["cat_bloom"] == nivel_bloom]
        if not fila_bloom.empty:
            desc = fila_bloom.iloc[0].get("proc_desc", "")
            subprocesos = fila_bloom.iloc[0].get("subprocesos", "")
            tipos_conocimiento = fila_bloom.iloc[0].get("tipos_conocimiento", "")
            
            contexto += f"\n📚 TAXONOMÍA DE BLOOM - {nivel_bloom}:\n"
            if desc and desc != "nan":
                contexto += f"  • Descripción: {desc}\n"
            if subprocesos and subprocesos != "nan":
                contexto += f"  • Subprocesos: {subprocesos}\n"
            if tipos_conocimiento and tipos_conocimiento != "nan":
                contexto += f"  • Tipos de conocimiento: {tipos_conocimiento}\n"
    
    # Marco ZDP: Principios de aprendizaje
    if marcos.get("zdp") is not None:
        filas_zdp = marcos["zdp"][marcos["zdp"]["cat_bloom_sugerida"] == nivel_bloom]
        if not filas_zdp.empty:
            principios = filas_zdp["principio_zdp"].tolist()
            contexto += f"\n🎯 ZONA DE DESARROLLO PRÓXIMO - Principios aplicables:\n"
            for i, principio in enumerate(principios[:3], 1):
                if principio and principio != "nan":
                    contexto += f"  {i}. {principio}\n"
    
    # Marco Flow: Dimensiones de motivación
    if marcos.get("flow") is not None:
        filas_flow = marcos["flow"][marcos["flow"]["cat_bloom"] == nivel_bloom]
        if not filas_flow.empty:
            dimensiones = filas_flow["dimension"].tolist()
            definiciones = filas_flow["txt_definicion"].tolist()
            contexto += f"\n⚡ TEORÍA DEL FLOW - Dimensiones motivacionales:\n"
            for dim, defi in zip(dimensiones[:2], definiciones[:2]):
                if dim and dim != "nan":
                    contexto += f"  • {dim}"
                    if defi and defi != "nan":
                        contexto += f": {defi[:100]}...\n"
                    else:
                        contexto += "\n"
    
    return contexto


def _obtener_instrucciones_flashcards(estrategia):
    """Retorna instrucciones específicas para flashcards según estrategia.
    
    Args:
        estrategia (str): 'scaffolding', 'refuerzo' o 'estandar'
    
    Returns:
        str: Instrucciones formateadas
    """
    if estrategia == "scaffolding":
        return """
        🎯 ESTRATEGIA SCAFFOLDING (Zona de Desarrollo Próximo):
        - Las flashcards deben incluir PISTAS PROGRESIVAS en el reverso
        - Estructura del reverso: Definición → Ejemplo → Aplicación
        - Usa lenguaje que invite a la reflexión: "Considera...", "Observa que..."
        - Incluye conexiones con conocimientos previos
        - Fomenta el pensamiento metacognitivo
        """
    elif estrategia == "refuerzo":
        return """
        💪 ESTRATEGIA REFUERZO (Brecha detectada):
        - Las flashcards deben enfatizar REPETICIÓN ESPACIADA de conceptos
        - Estructura del reverso: Definición precisa → Múltiples ejemplos → Contraejemplos
        - Usa lenguaje claro y directo
        - Incluye mnemotécnicos o reglas simples
        - Provee casos de uso prácticos
        """
    else:
        return """
        📝 ESTRATEGIA ESTÁNDAR:
        - Balance entre teoría y práctica
        - Estructura del reverso: Definición → Ejemplo representativo
        - Lenguaje neutro y académico
        - Conceptos claros sin ambigüedad
        """


def _obtener_instrucciones_tests(estrategia):
    """Retorna instrucciones específicas para tests según estrategia.
    
    Args:
        estrategia (str): 'scaffolding', 'refuerzo' o 'estandar'
    
    Returns:
        str: Instrucciones formateadas
    """
    if estrategia == "scaffolding":
        return """
        🎯 ESTRATEGIA SCAFFOLDING (Zona de Desarrollo Próximo):
        - El feedback debe incluir PISTAS GRADUALES sin revelar la respuesta completa
        - Para incorrectas: "Estás cerca, pero considera..."
        - Usa preguntas de seguimiento en el feedback
        - Refuerza el proceso de razonamiento, no solo el resultado
        - Conecta errores con conceptos relacionados
        """
    elif estrategia == "refuerzo":
        return """
        💪 ESTRATEGIA REFUERZO (Brecha detectada):
        - El feedback debe ser EXPLÍCITO Y DETALLADO
        - Para incorrectas: Explica exactamente por qué es incorrecta + concepto correcto completo
        - Incluye referencias a material específico: "Revisa la sección donde se define..."
        - Provee ejemplos adicionales en el feedback
        - Enfatiza la práctica: "Intenta resolver casos similares..."
        """
    else:
        return """
        📝 ESTRATEGIA ESTÁNDAR:
        - Feedback balanceado: explicación + pista
        - Para correctas: Refuerzo breve
        - Para incorrectas: Dirección hacia concepto correcto
        - Lenguaje neutral y formativo
        """
