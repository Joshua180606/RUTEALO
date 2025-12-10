"""
Chatbot tutor inteligente con contexto de ruta y soporte multilingüe.

Utiliza Google Gemini para generar respuestas pedagógicas basadas en:
- Material de la ruta del estudiante
- Flashcards y exámenes generados
- Historial conversacional
- Idioma seleccionado (Español, Inglés, Quechua)
"""

import google.generativeai as genai
from src.config import GOOGLE_API_KEY_CHATBOT
from src.database import get_database
import logging

logger = logging.getLogger(__name__)

# Configurar Gemini con clave especializada para chatbot
genai.configure(api_key=GOOGLE_API_KEY_CHATBOT)
model = genai.GenerativeModel('gemini-1.5-pro')


class TutorVirtual:
    """Tutor virtual inteligente con contexto de ruta del estudiante"""
    
    def __init__(self, ruta_id, usuario, idioma='es'):
        """
        Inicializa el tutor con contexto de una ruta específica.
        
        Args:
            ruta_id (str): ID de la ruta de aprendizaje
            usuario (str): Usuario propietario
            idioma (str): Código de idioma ('es', 'en', 'qu')
        """
        self.ruta_id = ruta_id
        self.usuario = usuario
        self.idioma = idioma
        self.db = get_database()
        self.contexto_ruta = self._cargar_contexto()
    
    def _cargar_contexto(self):
        """Carga material de la ruta desde MongoDB"""
        try:
            # Buscar ruta por ID (string o ObjectId)
            from bson import ObjectId
            try:
                ruta = self.db.rutas_aprendizaje.find_one({"_id": ObjectId(self.ruta_id)})
            except:
                # Si falla, intentar como string
                ruta = self.db.rutas_aprendizaje.find_one({"_id": self.ruta_id})
            
            if not ruta:
                logger.warning(f"No se encontró ruta con ID: {self.ruta_id}")
                return None
            
            # Extraer conceptos clave de flashcards
            flashcards = ruta.get('estructura_ruta', {}).get('flashcards', {})
            conceptos = []
            for nivel, cards in flashcards.items():
                for card in cards:
                    frente = card.get('frente', '') or card.get('pregunta', '')
                    reverso = card.get('reverso', '') or card.get('respuesta', '')
                    if frente and reverso:
                        conceptos.append(f"• {frente}: {reverso[:200]}")  # Primeros 200 chars
            
            # Extraer preguntas de exámenes para contexto
            examenes = ruta.get('estructura_ruta', {}).get('examenes', {})
            preguntas_exam = []
            for nivel, exams in examenes.items():
                for exam in exams[:3]:  # Solo primeras 3 por nivel
                    pregunta = exam.get('pregunta', '')
                    if pregunta:
                        preguntas_exam.append(f"• {pregunta}")
            
            # Material crudo original del usuario
            materiales = list(self.db.materiales_crudos.find({"usuario": self.usuario}).limit(5))
            contenido_raw = "\n\n".join([
                f"--- {m.get('nombre_archivo', 'Material')} ---\n{m.get('contenido_extraido', '')[:3000]}"
                for m in materiales
            ])
            
            return {
                "nombre_ruta": ruta.get('nombre', 'Ruta sin nombre'),
                "descripcion": ruta.get('descripcion', ''),
                "conceptos_clave": conceptos[:25],  # Top 25
                "preguntas_ejemplo": preguntas_exam[:15],  # Top 15
                "material_original": contenido_raw[:8000],  # Primeros 8k chars
                "nivel_actual": ruta.get('metadatos_ruta', {}).get('nivel_actual_estudiante'),
                "zona_proxima": ruta.get('metadatos_ruta', {}).get('zona_proxima', [])
            }
        
        except Exception as e:
            logger.error(f"Error cargando contexto de ruta: {e}")
            return None
    
    def responder(self, mensaje, historial=[]):
        """
        Genera respuesta pedagógica en el idioma seleccionado.
        
        Args:
            mensaje (str): Pregunta del estudiante
            historial (list): Mensajes previos [{"tipo": "usuario"|"bot", "texto": "..."}]
        
        Returns:
            str: Respuesta del tutor
        """
        if not self.contexto_ruta:
            return "❌ Error: No pude cargar el contexto de tu ruta. Por favor, verifica que la ruta exista."
        
        # Construir prompt según idioma
        prompts_idioma = {
            'es': self._prompt_espanol(),
            'en': self._prompt_ingles(),
            'qu': self._prompt_quechua()
        }
        
        prompt_base = prompts_idioma.get(self.idioma, prompts_idioma['es'])
        
        # Agregar historial para contexto conversacional
        historial_texto = ""
        if historial:
            historial_texto = "\n📝 HISTORIAL DE LA CONVERSACIÓN (últimos 5 mensajes):\n"
            for h in historial[-5:]:
                rol = "Estudiante" if h.get('tipo') == 'usuario' else "Tutor"
                historial_texto += f"{rol}: {h.get('texto', '')}\n"
        
        prompt_completo = f"""{prompt_base}

{historial_texto}

💬 PREGUNTA ACTUAL DEL ESTUDIANTE:
{mensaje}

Responde de forma pedagógica, clara y motivadora en {self._nombre_idioma()}.
"""
        
        try:
            response = model.generate_content(prompt_completo)
            return response.text
        
        except Exception as e:
            logger.error(f"Error generando respuesta del chatbot: {e}")
            errores_idioma = {
                'es': f"❌ Lo siento, tuve un problema al generar la respuesta: {str(e)}",
                'en': f"❌ Sorry, I had a problem generating the response: {str(e)}",
                'qu': f"❌ Pampachakuway, huk sasachakuy karqan: {str(e)}"
            }
            return errores_idioma.get(self.idioma, errores_idioma['es'])
    
    def _nombre_idioma(self):
        """Retorna nombre del idioma"""
        nombres = {'es': 'ESPAÑOL', 'en': 'ENGLISH', 'qu': 'QUECHUA (QHESWA)'}
        return nombres.get(self.idioma, 'ESPAÑOL')
    
    def _prompt_espanol(self):
        """Prompt en español"""
        ctx = self.contexto_ruta
        conceptos_texto = "\n".join(ctx['conceptos_clave']) if ctx['conceptos_clave'] else "• No hay conceptos cargados aún"
        preguntas_texto = "\n".join(ctx['preguntas_ejemplo'][:10]) if ctx['preguntas_ejemplo'] else "• No hay preguntas cargadas"
        
        return f"""Eres un TUTOR PEDAGÓGICO EXPERTO, amable y motivador que ayuda a estudiantes universitarios.

🎓 CONTEXTO DEL ESTUDIANTE:
• Ruta de aprendizaje: "{ctx['nombre_ruta']}"
• Descripción: {ctx['descripcion']}
• Nivel Bloom actual: {ctx['nivel_actual'] or 'Por determinar'}
• Zona de Desarrollo Próximo (ZDP): {', '.join(ctx['zona_proxima']) if ctx['zona_proxima'] else 'Por evaluar'}

📚 CONCEPTOS CLAVE DE LA RUTA (flashcards):
{conceptos_texto}

❓ PREGUNTAS DE EVALUACIÓN (ejemplos del examen):
{preguntas_texto}

📄 MATERIAL ORIGINAL DEL ESTUDIANTE (extracto):
{ctx['material_original']}

🎯 TU ROL COMO TUTOR:
1. Responde SOLO preguntas relacionadas con el material de la ruta
2. Usa un tono pedagógico, claro, motivador y cercano
3. Proporciona EJEMPLOS CONCRETOS cuando sea útil
4. Si la pregunta no está relacionada con el material, redirige amablemente:
   "Esa pregunta está fuera del tema de tu ruta. ¿Qué te gustaría saber sobre [tema de la ruta]?"
5. Adapta tu respuesta al nivel Bloom del estudiante:
   - Si está en niveles básicos (Recordar/Comprender): Explica con definiciones claras
   - Si está en niveles avanzados (Aplicar/Analizar): Propón casos prácticos y análisis
6. Usa emojis ocasionalmente para hacer la conversación más amigable 💡
7. IMPORTANTE: Responde SIEMPRE en ESPAÑOL claro y académico

⚠️ NO inventes información que no esté en el material. Si no sabes algo, admítelo honestamente."""
    
    def _prompt_ingles(self):
        """Prompt en inglés"""
        ctx = self.contexto_ruta
        conceptos_texto = "\n".join(ctx['conceptos_clave']) if ctx['conceptos_clave'] else "• No concepts loaded yet"
        preguntas_texto = "\n".join(ctx['preguntas_ejemplo'][:10]) if ctx['preguntas_ejemplo'] else "• No questions loaded"
        
        return f"""You are an EXPERT PEDAGOGICAL TUTOR, friendly and motivating, helping university students.

🎓 STUDENT CONTEXT:
• Learning path: "{ctx['nombre_ruta']}"
• Description: {ctx['descripcion']}
• Current Bloom level: {ctx['nivel_actual'] or 'To be determined'}
• Zone of Proximal Development (ZPD): {', '.join(ctx['zona_proxima']) if ctx['zona_proxima'] else 'To be evaluated'}

📚 KEY CONCEPTS FROM THE PATH (flashcards):
{conceptos_texto}

❓ ASSESSMENT QUESTIONS (exam examples):
{preguntas_texto}

📄 STUDENT'S ORIGINAL MATERIAL (excerpt):
{ctx['material_original']}

🎯 YOUR ROLE AS TUTOR:
1. Answer ONLY questions related to the path material
2. Use a pedagogical, clear, motivating and friendly tone
3. Provide CONCRETE EXAMPLES when useful
4. If the question is unrelated to the material, kindly redirect:
   "That question is outside the scope of your path. What would you like to know about [path topic]?"
5. Adapt your response to the student's Bloom level:
   - If in basic levels (Remember/Understand): Explain with clear definitions
   - If in advanced levels (Apply/Analyze): Propose practical cases and analysis
6. Use emojis occasionally to make the conversation more engaging 💡
7. IMPORTANT: ALWAYS respond in clear academic ENGLISH

⚠️ DO NOT invent information that isn't in the material. If you don't know something, admit it honestly."""
    
    def _prompt_quechua(self):
        """Prompt en quechua (con respaldo en español)"""
        ctx = self.contexto_ruta
        conceptos_texto = "\n".join(ctx['conceptos_clave'][:15]) if ctx['conceptos_clave'] else "• Mana yachaykunaqa kanchu"
        
        return f"""Qamqa YACHACHIQ EXPERTOM kanki, sumaq sunquyuq, yanapakunapaq universidadmanta yachaqkunata.

🎓 YACHAQPA CONTEXTUN:
• Ñan yachaymanta: "{ctx['nombre_ruta']}"
• Willakuy: {ctx['descripcion']}
• Kunan nivel (Bloom): {ctx['nivel_actual'] or 'Mana yachasqa'}
• Zona de Desarrollo Próximo: {', '.join(ctx['zona_proxima']) if ctx['zona_proxima'] else 'Mana yachasqa'}

📚 HATUN YACHAYKUNAA (flashcards):
{conceptos_texto}

📄 YACHAQPA MATERIALNIN:
{ctx['material_original'][:2000]}

🎯 LLAMKAYNIKIQA:
1. Kutichiyta SAPALLA tapuykunata materialwan tupachisqa
2. Allin simiwan yachachiy, kallpachay
3. Quy EJEMPLOS kay materialmanta
4. Sichus tapuyqa mana tupanchu, kutichiy allinlla:
   "Chay tapuyqa mana kay temawan kanchu. ¿Imatataq yacha munki [tema] nisqamanta?"
5. Nivelman hina kutichiy:
   - Qallariy (Yuyariy/Hamut'ay): Allinlla sut'inchay
   - Ñawpaq (Ruray/T'aqay): Quy ruwaykunata, ejemplokunatapas
6. IMPORTANTE: Kutichinki SIEMPRE QUECHUA simipi (icha español simiwan chaqrusqa sichus mana atinkichu)

⚠️ AMA invented informacionta quy. Sichus mana yachankichu, ninki chiqaqta: "Manan yachanichu chayta, ichaqa yachachisqayki..."

NOTA: Si el modelo Gemini no genera quechua fluido, usa TÉRMINOS QUECHUAS PEDAGÓGICOS mezclados con español claro."""
    


def crear_respuesta_rapida(pregunta_tipo):
    """
    Genera respuestas rápidas predefinidas para consultas comunes.
    
    Args:
        pregunta_tipo (str): Tipo de pregunta común
    
    Returns:
        dict: Respuesta en 3 idiomas o None
    """
    respuestas = {
        'saludo': {
            'es': '¡Hola! 👋 Soy tu tutor virtual. Estoy aquí para ayudarte con el contenido de tu ruta de aprendizaje. ¿Qué te gustaría repasar hoy?',
            'en': 'Hello! 👋 I\'m your virtual tutor. I\'m here to help you with your learning path content. What would you like to review today?',
            'qu': '¡Napaykullayki! 👋 Ñuqaqa tutoraykim kani. Kaykupi kani yanapanaykipaq yachaynikipi. ¿Imataq munankiteqi kunanqa?'
        },
        'ayuda': {
            'es': '💡 Puedo ayudarte con:\n• Explicar conceptos de tu material\n• Resolver dudas sobre las flashcards\n• Proponer ejemplos prácticos\n• Repasar temas específicos\n\n¿Sobre qué tema tienes dudas?',
            'en': '💡 I can help you with:\n• Explaining concepts from your material\n• Answering questions about flashcards\n• Proposing practical examples\n• Reviewing specific topics\n\nWhat topic do you have questions about?',
            'qu': '💡 Yanapasqayki:\n• Sut\'inchay yachaykunata materialniykimanta\n• Kutichiy tapuykunata flashcardsmanta\n• Quy ejemplokunahta\n• Yachachiy temakuna específicos\n\n¿Ima temamantachus tapuyniykikuna kanku?'
        }
    }
    
    return respuestas.get(pregunta_tipo)
