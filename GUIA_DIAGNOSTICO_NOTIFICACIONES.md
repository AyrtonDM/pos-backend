# 🔍 Guía de Diagnóstico de Notificaciones Firebase

## Problema Actual
Las notificaciones no llegan al móvil ni se registran en historial.

## 🚀 Pasos a Ejecutar

### 1. **Ejecutar el diagnóstico completo**

Abre una terminal PowerShell en `pos-backend` y ejecuta:

```powershell
python diagnostic_firebase.py
```

**Qué esperar:**
- ✅ Si Firebase está correctamente inicializado, verás: `✅ [FIREBASE] Inicializado exitosamente`
- ✅ Si hay tokens en BD, verás: `Total de tokens registrados: X`
- ⚠️ Si Firebase no se inicializa, verás el mensaje de error específico

**Qué hacer si falla:**
- Si dice "Archivo NO existe": verifica que el path en `.env` sea correcto
- Si dice "Campos faltantes en JSON": el archivo de credenciales está corrupto
- Si dice "No inicializado": probablemente falta la variable `FIREBASE_SERVICE_ACCOUNT` en `.env`

---

### 2. **Listar todos los tokens registrados**

```powershell
python test_send_notification.py list
```

**Qué esperar:**
```
Total: 4 token(s)

  ID: 1
    Usuario: 4
    Plataforma: android
    Token: cY-_2M-FAV0:APA91b...
    Activo: True
```

**Si no hay tokens:**
- El cliente móvil no está registrando tokens correctamente
- Verifica que `/notifications/register-token` esté siendo llamado desde el móvil

---

### 3. **Enviar una notificación de prueba**

Abre **otra terminal** (deja Uvicorn corriendo en la primera) y ejecuta:

```powershell
# Enviar alerta a empresa 1
python test_send_notification.py alert 1

# O enviar notificación personal al usuario 4 en empresa 1
python test_send_notification.py user 4 1
```

**Qué buscar en los logs:**

#### ✅ Si todo funciona:
```
🔔 [ALERTA] Iniciando envío de alerta para empresa 1
   Título: Alerta de Prueba
   Mensaje: Este es un mensaje de prueba
   ✅ Historial guardado con ID: 123
   📱 Tokens recuperados de BD: 4
   ✅ Cliente Firebase disponible
   📦 Batch preparado con 4 mensajes
   📤 Enviando batch a Firebase...
🚀 [FCM SUCCESS] Alerta enviada para empresa 1. Enviados: 4, Fallidos: 0
```

#### ❌ Si falla en Firebase:
```
❌ [FCM ERROR] Error crítico al invocar Firebase en enviar_alerta: Invalid registration token provided. Please make sure it matches the format provided by the client application that authorizes the sender.
```

#### ⚠️ Si hay tokens mock (para pruebas):
```
📱 Tokens recuperados de BD: 5
   ⊘ Ignorando token mock: mock_token_testing_123456
   📦 Batch preparado con 4 mensajes
```

---

## 🔧 Solución de Problemas

### Problema: "Firebase service account not found"
**Solución:**
1. Verifica el path en `.env`:
   ```
   FIREBASE_SERVICE_ACCOUNT=c:\Users\HP\OneDrive\Escritorio\Sistema_POS_SI2\pos-backend\app\secrets\pos-si2-firebase-adminsdk-fbsvc-4364781c9e.json
   ```
2. Asegúrate de que el archivo existe
3. Si uses rutas relativas, cámbialo a rutas absolutas

### Problema: "Invalid registration token"
**Solución:**
- El token guardado en BD es inválido o expiró
- El cliente móvil debe re-registrar el token
- Implementa refresh de tokens cuando la app se abre

### Problema: "Historial guardado pero notificaciones no llegan"
**Solución:**
1. Verifica que el cliente móvil esté escuchando eventos de Firebase Cloud Messaging
2. Asegúrate de que la app tiene permisos de notificaciones en Android/iOS
3. Intenta re-registrar el token desde el cliente móvil

### Problema: "No hay tokens para esta empresa"
**Solución:**
- Verifica que `id_empresa` sea correcto en el registro del token
- Ejecuta `python test_send_notification.py list` para ver qué empresa tiene tokens

---

## 📊 Flujo Completo de Verificación

```
1. ¿Firebase está inicializado?
   → Ejecuta: python diagnostic_firebase.py
   → Busca: ✅ [FIREBASE] Inicializado exitosamente

2. ¿Hay tokens en BD?
   → Ejecuta: python test_send_notification.py list
   → Busca: Total: X token(s)

3. ¿Se puede enviar?
   → Ejecuta: python test_send_notification.py alert 1
   → Busca: 🚀 [FCM SUCCESS] ... Enviados: X, Fallidos: 0

4. ¿Llegan al móvil?
   → Abre la app y mira la bandeja de notificaciones
   → Si no llegan, verifica permisos en Android/iOS
```

---

## 💡 Tips para Debugging

### Ver logs en tiempo real mientras envías desde la app:
```powershell
# Terminal 1: Uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Test
python test_send_notification.py alert 1

# Vuelve a Terminal 1 y busca los logs 🔍
```

### Registrar un token manualmente para debugging:
```powershell
# Desde PowerShell
$token = "token_del_movil_aqui"
$body = @{
    token = $token
    uid_usuario = "4"
    id_empresa = "1"
    plataforma = "android"
} | ConvertTo-Json

Invoke-WebRequest -Uri "http://localhost:8000/notifications/register-token" `
  -Method Post `
  -Body $body `
  -ContentType "application/json"
```

---

## 🎯 Resumen de Cambios Realizados

✅ Mejorados logs en `firebase_admin_client.py` - ahora explícitamente indica si Firebase se inicializa  
✅ Mejorados logs en `notification_service.py` - logs detallados en cada etapa del envío  
✅ Creado `diagnostic_firebase.py` - verifica credenciales y configuración  
✅ Creado `test_send_notification.py` - envía notificaciones de prueba desde línea de comandos  

**Próximo paso:** Ejecuta el diagnóstico y compartí los resultados para identificar exactamente dónde se rompe la cadena.
