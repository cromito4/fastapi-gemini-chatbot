# 🤖 FastAPI AI Chatbot Backend con Gemini y JWT

Un sistema completo de backend para chat con inteligencia artificial desarrollado con **FastAPI**, **SQLite**, autenticación segura con **Tokens JWT** y la API oficial de **Google Gemini**.

---

## 🚀 Características

- 🔐 **Autenticación con JWT**: Registro y Login con contraseñas encriptadas mediante `bcrypt`.
- 💬 **Gestión de Conversaciones (CRUD)**:
  - Crear conversaciones privadas asignadas a cada usuario.
  - Listar únicamente las conversaciones propias.
  - Consultar el historial cronológico de mensajes.
  - Eliminar conversaciones con borrado en cascada de sus mensajes (`cascade="all, delete-orphan"`).
- 🧠 **Memoria Contextual con Google Gemini**: Envío del historial acumulado para respuestas contextuales con sistema de reintentos y fallback ante picos de demanda.
- 📖 **Documentación Interactiva Moderna**: Integración completa con **Scalar** en `/scalar`.

---

## 🛠️ Tecnologías Utilizadas

- **Lenguaje:** Python 3.11+
- **Framework Web:** FastAPI & Uvicorn
- **Base de Datos:** SQLite & SQLAlchemy (ORM)
- **Seguridad:** PyJWT & Bcrypt
- **Inteligencia Artificial:** SDK oficial `google-genai` (Google Gemini)
- **Documentación API:** Scalar (`@scalar/api-reference`)

---

## 📦 Instalación y Configuración

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/TU_USUARIO/TU_REPOSITORIO.git
   cd chatbot
   ```

2. **Crear y activar el entorno virtual:**
   ```bash
   python -m venv .venv
   # En Windows:
   .\.venv\Scripts\Activate
   # En Linux/Mac:
   source .venv/bin/activate
   ```

3. **Instalar las dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar las variables de entorno:**
   Copia el archivo `.env.example` a `.env`:
   ```bash
   cp .env.example .env
   ```
   Abre `.env` y coloca tu API Key de Gemini obtenida de [Google AI Studio](https://aistudio.google.com/apikey):
   ```env
   GEMINI_API_KEY=AIzaSy...
   ```

---

## ▶️ Ejecución del Servidor

Inicia el servidor de desarrollo:
```bash
uvicorn main:app --reload
```

Abre tu navegador para interactuar con la API en **Scalar**:
👉 **[http://127.0.0.1:8000/scalar](http://127.0.0.1:8000/scalar)**

---

## 📋 Endpoints de la API

| Método | Endpoint | Descripción | Protegido |
|---|---|---|:---:|
| `POST` | `/register` | Registrar un nuevo usuario | ❌ No |
| `POST` | `/login` | Iniciar sesión y obtener Token JWT | ❌ No |
| `POST` | `/conversations` | Crear nueva conversación privada | ✅ Sí |
| `GET` | `/conversations` | Listar todas las conversaciones del usuario | ✅ Sí |
| `GET` | `/conversations/{id}/messages` | Ver historial de mensajes de un chat | ✅ Sí |
| `DELETE` | `/conversations/{id}` | Eliminar una conversación y sus mensajes | ✅ Sí |
| `POST` | `/chat` | Enviar mensaje y recibir respuesta de Gemini | ✅ Sí |
