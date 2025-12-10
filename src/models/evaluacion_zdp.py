"""
Sistema de Evaluación y Scoring basado en la Zona de Desarrollo Próximo (ZDP).

La ZDP de Vygotsky define que el aprendizaje óptimo ocurre en la brecha entre:
- Lo que el estudiante puede hacer solo (Nivel Actual)
- Lo que puede hacer con ayuda (Zona Próxima)

Este módulo:
1. Evalúa respuestas de exámenes
2. Calcula puntajes por nivel Bloom
3. Identifica brechas de conocimiento
4. Recomienda temas a omitir/enfatizar
5. Actualiza el perfil del estudiante
"""

import os
import json
import datetime
import google.generativeai as genai

# Configuración centralizada en src.config
from src.config import (
    DB_NAME,
    get_genai_model,
)
from src.database import get_database
from src.utils import retry
import logging

logger = logging.getLogger(__name__)

# Modelo Gemini (configuración centralizada)
model = get_genai_model()

# Jerarquía de Bloom (del más simple al más complejo)
JERARQUIA_BLOOM = ["Recordar", "Comprender", "Aplicar", "Analizar", "Evaluar", "Crear"]

# Umbral de competencia (% de aciertos)
UMBRAL_COMPETENCIA = 70  # Si el estudiante acierta >= 70%, se considera competente


class EvaluadorZDP:
    """Clase para evaluar exámenes y calcular scoring basado en ZDP."""

    def __init__(self):
        """Inicializa la conexión a la BD."""
        try:
            self.db = get_database(DB_NAME)
        except Exception as e:
            logger.error(f"❌ Error conectando a BD: {e}")
            self.db = None

    def evaluar_examen(self, usuario, respuestas_estudiante, examen_original):
        """
        Evalúa un examen respondido por el estudiante.

        Args:
            usuario (str): ID del estudiante
            respuestas_estudiante (list): [
                {"pregunta_id": 1, "respuesta": "a", "tiempo_seg": 45},
                ...
            ]
            examen_original (dict): El examen original con respuestas correctas

        Returns:
            dict: Resultado de evaluación con puntuaciones por nivel Bloom
        """
        if not self.db:
            return {"error": "No hay conexión a BD"}

        resultado = {
            "usuario": usuario,
            "fecha_evaluacion": datetime.datetime.utcnow(),
            "respuestas_procesadas": [],
            "resumen_por_nivel": {},
            "puntaje_total": 0,
            "nivel_actual": None,
            "zona_proxima": [],
            "recomendaciones": [],
        }

        # 1. Procesar cada respuesta
        preguntas_examen = examen_original.get("EXAMENES", {}).get("EXAMEN_INICIAL", [])
        preguntas_dict = {p["id"]: p for p in preguntas_examen}

        aciertos_por_nivel = {}
        total_por_nivel = {}

        for respuesta_est in respuestas_estudiante:
            pregunta_id = respuesta_est.get("pregunta_id")
            respuesta_est_val = respuesta_est.get("respuesta", "").lower().strip()
            tiempo_seg = respuesta_est.get("tiempo_seg", 0)

            if pregunta_id not in preguntas_dict:
                continue

            pregunta = preguntas_dict[pregunta_id]
            respuesta_correcta = pregunta.get("respuesta_correcta", "").lower().strip()
            nivel_bloom = pregunta.get("nivel_bloom_evaluado", "Recordar")

            # Inicializar contadores por nivel si no existen
            if nivel_bloom not in aciertos_por_nivel:
                aciertos_por_nivel[nivel_bloom] = 0
                total_por_nivel[nivel_bloom] = 0

            total_por_nivel[nivel_bloom] += 1
            es_correcto = respuesta_est_val == respuesta_correcta

            if es_correcto:
                aciertos_por_nivel[nivel_bloom] += 1

            # Guardar respuesta procesada
            resultado["respuestas_procesadas"].append(
                {
                    "pregunta_id": pregunta_id,
                    "pregunta": pregunta.get("pregunta"),
                    "nivel_bloom": nivel_bloom,
                    "respuesta_estudiante": respuesta_est_val,
                    "respuesta_correcta": respuesta_correcta,
                    "es_correcto": es_correcto,
                    "tiempo_segundos": tiempo_seg,
                }
            )

        # 2. Calcular porcentajes por nivel y puntaje total
        puntaje_total = 0
        niveles_completados = []
        brechas_identificadas = []

        for nivel in JERARQUIA_BLOOM:
            if nivel in total_por_nivel and total_por_nivel[nivel] > 0:
                aciertos = aciertos_por_nivel.get(nivel, 0)
                total = total_por_nivel[nivel]
                porcentaje = (aciertos / total) * 100

                resultado["resumen_por_nivel"][nivel] = {
                    "aciertos": aciertos,
                    "total": total,
                    "porcentaje": round(porcentaje, 2),
                    "competente": porcentaje >= UMBRAL_COMPETENCIA,
                }

                # Sumar puntaje total (ponderado por dificultad)
                peso = (JERARQUIA_BLOOM.index(nivel) + 1) / len(JERARQUIA_BLOOM)
                puntaje_total += porcentaje * peso

                if porcentaje >= UMBRAL_COMPETENCIA:
                    niveles_completados.append(nivel)
                else:
                    brechas_identificadas.append(nivel)

        resultado["puntaje_total"] = round(puntaje_total, 2)

        # 3. Identificar Nivel Actual y Zona Próxima (ZDP)
        if niveles_completados:
            idx_ultimo = JERARQUIA_BLOOM.index(niveles_completados[-1])
            resultado["nivel_actual"] = niveles_completados[-1]
            # Zona próxima: próximos 1-2 niveles después del actual
            resultado["zona_proxima"] = JERARQUIA_BLOOM[idx_ultimo + 1 : idx_ultimo + 3]
        else:
            resultado["nivel_actual"] = JERARQUIA_BLOOM[0]
            resultado["zona_proxima"] = JERARQUIA_BLOOM[:2]

        # 4. Generar recomendaciones
        resultado["recomendaciones"] = self._generar_recomendaciones(
            niveles_completados, brechas_identificadas, resultado["zona_proxima"]
        )

        # 5. Guardar en BD
        self._guardar_resultado_evaluacion(usuario, resultado)

        return resultado

    def _generar_recomendaciones(self, competentes, brechas, zona_proxima):
        """Genera recomendaciones pedagógicas basadas en ZDP."""
        recomendaciones = []

        if competentes:
            recomendaciones.append(
                {
                    "tipo": "fortalezas",
                    "mensaje": f"El estudiante domina los siguientes niveles: {', '.join(competentes)}",
                    "accion": "Omitir o acelerar estos temas en la ruta",
                }
            )

        if brechas:
            recomendaciones.append(
                {
                    "tipo": "brechas",
                    "mensaje": f"Necesita refuerzo en: {', '.join(brechas)}",
                    "accion": "Enfatizar estos niveles con ejercicios prácticos y tutorización",
                }
            )

        if zona_proxima:
            recomendaciones.append(
                {
                    "tipo": "zona_proxima",
                    "mensaje": f"Próximos objetivos de aprendizaje (ZDP): {', '.join(zona_proxima)}",
                    "accion": "Trabajar estos niveles con apoyo estructurado",
                }
            )

        return recomendaciones

    def _guardar_resultado_evaluacion(self, usuario, resultado):
        """Guarda el resultado de evaluación en MongoDB."""
        if not self.db:
            return

        try:
            # Guardar en colección de evaluaciones
            col_evaluaciones = self.db.get_collection("evaluaciones_estudiante")
            col_evaluaciones.insert_one(resultado)

            # Actualizar perfil del estudiante
            col_perfil = self.db.get_collection("usuario_perfil")
            col_perfil.update_one(
                {"usuario": usuario},
                {
                    "$set": {
                        "nivel_actual": resultado["nivel_actual"],
                        "zona_proxima": resultado["zona_proxima"],
                        "puntaje_ultimo_examen": resultado["puntaje_total"],
                        "competencias": resultado["resumen_por_nivel"],
                        "ultima_evaluacion": resultado["fecha_evaluacion"],
                    }
                },
                upsert=True,
            )
            logger.info(f"✅ Evaluación guardada para {usuario}")
        except Exception as e:
            logger.error(f"❌ Error guardando evaluación: {e}")

    def obtener_evaluacion_estudiante(self, usuario):
        """Obtiene la evaluación más reciente de un estudiante."""
        if not self.db:
            return None

        try:
            col_evaluaciones = self.db.get_collection("evaluaciones_estudiante")
            resultado = col_evaluaciones.find_one({"usuario": usuario}, sort=[("fecha_evaluacion", -1)])
            return resultado
        except Exception as e:
            logger.error(f"❌ Error obteniendo evaluación: {e}")
            return None

    def obtener_perfil_zdp_simple(self, usuario):
        """Obtiene perfil ZDP resumido para generador de rutas.
        
        Returns:
            dict: {
                "niveles_competentes": [...],
                "zona_proxima": [...],
                "brechas": [...],
                "nivel_actual": str
            } o None si no hay evaluación
        """
        try:
            evaluacion = self.obtener_evaluacion_estudiante(usuario)
            
            if not evaluacion:
                logger.info(f"No hay evaluación previa para {usuario}, generando ruta completa")
                return None
            
            # Extraer niveles competentes del resumen
            competentes = [
                nivel for nivel, datos in evaluacion.get("resumen_por_nivel", {}).items()
                if datos.get("competente", False)
            ]
            
            # Calcular brechas (niveles NO competentes)
            brechas = [
                nivel for nivel in JERARQUIA_BLOOM 
                if nivel not in competentes
            ]
            
            perfil = {
                "niveles_competentes": competentes,
                "zona_proxima": evaluacion.get("zona_proxima", []),
                "nivel_actual": evaluacion.get("nivel_actual"),
                "brechas": brechas,
                "puntaje_total": evaluacion.get("puntaje_total", 0)
            }
            
            logger.info(f"✅ Perfil ZDP para {usuario}: Competentes={competentes}, Zona={perfil['zona_proxima']}")
            return perfil
            
        except Exception as e:
            logger.warning(f"⚠️ Error obteniendo perfil ZDP simple: {e}")
            return None

    @retry(max_attempts=3, delay=2.0, backoff=2.0, exceptions=(Exception,))
    def generar_ruta_personalizada(self, usuario, material_disponible):
        """
        Genera una ruta de aprendizaje personalizada según la evaluación ZDP.
        Se reintenta automáticamente si falla.

        Args:
            usuario (str): ID del estudiante
            material_disponible (str): Contenido educativo disponible

        Returns:
            dict: Ruta personalizada omitiendo niveles ya dominados
        """
        evaluacion = self.obtener_evaluacion_estudiante(usuario)

        if not evaluacion:
            return {"error": "No hay evaluación disponible para este estudiante"}

        nivel_actual = evaluacion.get("nivel_actual")
        zona_proxima = evaluacion.get("zona_proxima", [])
        competentes = [n for n, d in evaluacion.get("resumen_por_nivel", {}).items() if d.get("competente")]

        # Niveles a trabajar: zona próxima + brechas si las hay
        niveles_a_trabajar = zona_proxima + [n for n in JERARQUIA_BLOOM if n not in competentes]

        prompt = f"""
        Eres un diseñador de rutas educativas experto en la Teoría de Vygotsky sobre Zona de Desarrollo Próximo.

        El estudiante {usuario}:
        - NIVEL ACTUAL: {nivel_actual}
        - ZONA PRÓXIMA (objetivo): {', '.join(zona_proxima)}
        - YA DOMINA: {', '.join(competentes)}
        - NIVELES A TRABAJAR: {', '.join(niveles_a_trabajar)}

        Basado en este perfil y el contenido educativo disponible, genera una ruta de aprendizaje PERSONALIZADA que:
        1. OMITA por completo los temas donde ya es competente
        2. ENFATICE los temas en su zona próxima
        3. Incluya ejercicios prácticos con apoyo (tutorización)
        4. Sea pragmática y directa

        CONTENIDO DISPONIBLE (resumido):
        {material_disponible[:10000]}

        FORMATO JSON:
        {{
            "ruta_personalizada": {{
                "niveles_trabajar": [lista de niveles],
                "niveles_omitir": {competentes},
                "bloques": [
                    {{
                        "nivel": "nivel_bloom",
                        "duracion_min": 45,
                        "actividades": ["actividad1", "actividad2"],
                        "apoyo_requerido": "tipo de tutorización"
                    }}
                ],
                "observaciones": "recomendaciones pedagógicas"
            }}
        }}
        """

        try:
            respuesta = model.generate_content(prompt)
            import re

            texto_limpio = re.sub(r"```json|```", "", respuesta.text).strip()
            datos = json.loads(texto_limpio)
            return datos.get("ruta_personalizada", {})
        except Exception as e:
            logger.error(f"❌ Error generando ruta personalizada: {e}")
            return {"error": str(e)}


# --- FUNCIONES DE UTILIDAD ---


def evaluar_examen_simple(usuario, respuestas, examen):
    """
    Función simplificada para evaluar un examen con validaciones.
    
    Args:
        usuario (str): ID del estudiante
        respuestas (list): Lista de respuestas del estudiante
        examen (dict): Examen original con respuestas correctas
    
    Returns:
        dict: Resultado de evaluación o dict con error
    """
    from src.utils import validate_exam_responses, validate_exam_structure
    
    # Validar estructura de respuestas del estudiante
    is_valid, error_msg = validate_exam_responses(respuestas)
    if not is_valid:
        logger.warning(f"Invalid exam responses for {usuario}: {error_msg}")
        return {"error": f"Respuestas inválidas: {error_msg}", "status": 400}

    # Validar estructura del examen original
    is_valid, error_msg = validate_exam_structure(examen)
    if not is_valid:
        logger.error(f"Invalid exam structure for {usuario}: {error_msg}")
        return {"error": f"Estructura de examen inválida: {error_msg}", "status": 400}

    # Validar que el usuario existe
    if not usuario or not isinstance(usuario, str):
        logger.warning(f"Invalid usuario parameter: {usuario}")
        return {"error": "Usuario inválido", "status": 400}

    try:
        evaluador = EvaluadorZDP()
        resultado = evaluador.evaluar_examen(usuario, respuestas, examen)
        logger.info(f"Exam processed successfully for {usuario}")
        return resultado
    except Exception as e:
        logger.error(f"Error procesando examen para {usuario}: {str(e)}")
        return {"error": f"Error procesando examen: {str(e)}", "status": 500}


def obtener_perfil_zdp(usuario):
    """
    Obtiene el perfil ZDP actual del estudiante.
    
    Args:
        usuario (str): ID del estudiante
    
    Returns:
        dict: Perfil ZDP completo o dict indicando sin evaluación
    """
    evaluador = EvaluadorZDP()
    evaluacion = evaluador.obtener_evaluacion_estudiante(usuario)
    if evaluacion:
        return {
            "usuario": usuario,
            "nivel_actual": evaluacion.get("nivel_actual"),
            "zona_proxima": evaluacion.get("zona_proxima"),
            "puntaje": evaluacion.get("puntaje_total"),
            "competencias": evaluacion.get("resumen_por_nivel"),
            "recomendaciones": evaluacion.get("recomendaciones"),
        }
    return {
        "usuario": usuario,
        "estado": "Sin evaluación realizada",
        "mensaje": "El estudiante aún no ha completado un examen diagnóstico",
    }
