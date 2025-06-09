# Sistema de Gestión Académica

## Instalación y Configuración

#### Crear base de datos:
```sql
-- Conectar a PostgreSQL como superusuario
psql -U postgres

-- Crear la base de datos
CREATE DATABASE academic_management2;

-- Salir
\q
```

### 5. Configurar variables de entorno

El archivo `.env` ya está configurado con:

```env
# Configuración de la base de datos
DB_USER=postgres
DB_PASSWORD=admin
DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=academic_management2

# Clave secreta para JWT
JWT_SECRET_KEY=kenny_y_marycielo  

# Configuración de Flask
FLASK_DEBUG=True
```

### Inicializar la base de datos

```bash
# Inicializar migraciones (solo la primera vez)
flask db init

# Crear migración inicial
flask db migrate -m "Initial migration"

# Aplicar migraciones
flask db upgrade
```

### Ejecutar la aplicación

```bash
# Opción 1: Usando flask run
flask run

# Opción 2: Usando el archivo run.py
python run.py
```

La aplicación estará disponible en: `http://localhost:5000`

## Cómo Funciona el Sistema de Tokens JWT

### ¿Qué son los tokens JWT?

JWT (JSON Web Token) es un estándar para transmitir información de forma segura entre partes. En esta aplicación, los tokens sirven como "llaves digitales" que prueban que un usuario está autenticado.

### Flujo completo de autenticación:

```
1. Usuario → Login (username/password) → Servidor
2. Servidor → Valida credenciales → Genera 2 tokens
3. Servidor → Envía tokens al cliente
4. Cliente → Guarda tokens → Usa access_token para peticiones
5. Servidor → Valida token en cada petición → Permite/Deniega acceso
```

### Tipos de tokens en la aplicación:

#### 1. **Access Token** (Token de Acceso)
- **Duración**: 15 minutos
- **Propósito**: Acceder a recursos protegidos
- **Ubicación**: Header `Authorization: Bearer <token>`
- **Contenido**: ID del usuario, rol, fecha de expiración

#### 2. **Refresh Token** (Token de Refresco)  
- **Duración**: 30 días
- **Propósito**: Renovar access tokens expirados
- **Almacenamiento**: Base de datos + cliente
- **Ventaja**: Evita logins constantes

**Problemas sin tokens:**
- 🔴 **Inseguro**: Contraseña viaja en cada petición
- 🔴 **Ineficiente**: Servidor debe validar contraseña constantemente  
- 🔴 **Sin control**: No puedes revocar sesiones específicas
- 🔴 **Sin expiración**: Sesión dura para siempre

**Ventajas con tokens:**
- ✅ **Seguro**: Contraseña solo viaja una vez
- ✅ **Eficiente**: Servidor solo valida firma del token
- ✅ **Controlable**: Puedes revocar tokens específicos
- ✅ **Con expiración**: Access tokens expiran automáticamente

## Uso de la API

### Autenticación

#### 1. Registrar usuario
```bash
POST /api/auth/register
Content-Type: application/json

{
    "username": "usuario_ejemplo",
    "email": "usuario@ejemplo.com",
    "password": "mi_password",
    "first_name": "Nombre",
    "last_name": "Apellido",
    "role": "user",
    "orcid_id": "0000-0000-0000-0000"
}
```

#### 2. Iniciar sesión
```bash
POST /api/auth/login
Content-Type: application/json

{
    "username": "usuario_ejemplo",
    "password": "mi_password"
}
```

**Respuesta:**
```json
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {
        "id": "uuid-del-usuario",
        "username": "usuario_ejemplo",
        "email": "usuario@ejemplo.com",
        "role": "user"
    }
}
```

#### 3. Usar tokens en peticiones

Para acceder a endpoints protegidos, incluye el access token:

```bash
GET /api/auth/me
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...
```

#### 4. Renovar token de acceso

```bash
POST /api/auth/refresh
Authorization: Bearer <refresh_token>
```

#### 5. Cerrar sesión

```bash
POST /refresh_tokens/logout
Authorization: Bearer <access_token>
```

### Ejemplo Práctico: Flujo Completo de Usuario

Veamos un ejemplo real de cómo un usuario interactúa con la API:

```bash
# 🔸 PASO 1: Usuario intenta acceder sin token
GET http://localhost:5000/api/auth/me

# ❌ RESPUESTA SIN TOKEN:
{
    "msg": "Missing Authorization Header"
}
# Status: 401 Unauthorized

# 🔸 PASO 2: Usuario hace login
POST http://localhost:5000/api/auth/login
Content-Type: application/json

{
    "username": "maria123",
    "password": "mi_password"
}

# ✅ RESPUESTA EXITOSA:
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTcwNDczNjgwMCwianRpIjoiYWJjZGVmZ2giLCJ0eXBlIjoiYWNjZXNzIiwic3ViIjoiMTIzNDU2NzgtYWJjZC1lZmdoLWlqa2wtbW5vcHFyc3R1dnciLCJuYmYiOjE3MDQ3MzY4MDAsImV4cCI6MTcwNDczNzYwMH0.signature",
    "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6dHJ1ZSwiaWF0IjoxNzA0NzM2ODAwLCJqdGkiOiJ4eXp3dnV0cyIsInR5cGUiOiJyZWZyZXNoIiwic3ViIjoiMTIzNDU2NzgtYWJjZC1lZmdoLWlqa2wtbW5vcHFyc3R1dnciLCJuYmYiOjE3MDQ3MzY4MDAsImV4cCI6MTcwNzMyODgwMH0.signature",
    "user": {
        "id": "12345678-abcd-efgh-ijkl-mnopqrstuvw",
        "username": "maria123",
        "email": "maria@ejemplo.com",
        "role": "user"
    }
}

# 🔸 PASO 3: Usuario guarda tokens y accede a recursos
GET http://localhost:5000/api/auth/me
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6ZmFsc2U...

# ✅ RESPUESTA CON TOKEN VÁLIDO:
{
    "user": {
        "id": "12345678-abcd-efgh-ijkl-mnopqrstuvw",
        "username": "maria123",
        "email": "maria@ejemplo.com",
        "first_name": "María",
        "last_name": "González",
        "role": "user",
        "orcid_id": null,
        "created_at": "2024-01-08T10:30:00"
    }
}

# 🔸 PASO 4: Access token expira
GET http://localhost:5000/users/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc... (token expirado)

# ❌ RESPUESTA TOKEN EXPIRADO:
{
    "msg": "Token has expired"
}
# Status: 422 Unprocessable Entity

# 🔸 PASO 5: Usuario renueva token con refresh token
POST http://localhost:5000/api/auth/refresh
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJmcmVzaCI6dHJ1ZS... (refresh token)

# ✅ NUEVO ACCESS TOKEN:
{
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.NUEVO_TOKEN_AQUI..."
}

# 🔸 PASO 6: Usuario continúa usando el nuevo token
GET http://localhost:5000/users/
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc... (nuevo token)

# ✅ ACCESO EXITOSO DE NUEVO!
```
**Lo que hace `@jwt_required()`:**
1. Busca el header `Authorization: Bearer <token>`
2. Extrae el token
3. Verifica que no esté expirado
4. Valida la firma con `JWT_SECRET_KEY`
5. Si todo es válido, permite ejecutar la función
6. Si algo falla, devuelve error 401/422
