# Informe de Auditoría de Seguridad

**Aplicación Web de Clínica Veterinaria Pet-Friendly**

---

| Campo | Valor |
|-------|-------|
| **Fecha del Informe** | 23 de diciembre de 2025 |
| **Tipo de Auditoría** | Evaluación de Seguridad Interna |
| **Aplicación** | petfriendlyvet.com |
| **Versión** | Época 1 (Fase de Construcción) |
| **Auditor** | Equipo de Desarrollo |
| **Clasificación** | Uso Interno |

---

## Resumen Ejecutivo

Esta auditoría de seguridad evalúa la aplicación web de la Clínica Veterinaria Pet-Friendly contra estándares de seguridad de la industria, incluyendo OWASP Top 10 y las mejores prácticas de seguridad de Django. La evaluación identificó **6 mejoras de prioridad media** y confirmó que **6 controles de seguridad** están correctamente implementados.

### Postura de Seguridad General: **BUENA**

La aplicación demuestra una seguridad fundamental sólida con protecciones adecuadas a nivel de framework. Las mejoras recomendadas se centran en medidas de defensa en profundidad en lugar de vulnerabilidades críticas.

---

## Alcance de la Auditoría

### Sistemas Evaluados
- Aplicación web Django (v5.0)
- Base de datos PostgreSQL
- Servicio de archivos estáticos
- Integración de chat con IA
- Sistema de autenticación de usuarios

### Fuera del Alcance
- Seguridad de infraestructura/hosting
- Seguridad de servicios de terceros (OpenRouter, Google OAuth)
- Seguridad física
- Ingeniería social

### Metodología
- Análisis de código estático
- Revisión de configuración
- Pruebas de seguridad manuales
- Lista de verificación OWASP Top 10

---

## Resumen de Hallazgos

### Controles de Seguridad - IMPLEMENTADOS ✅

| Control | Estado | Evidencia |
|---------|--------|-----------|
| Protección CSRF | ✅ Implementado | CsrfViewMiddleware de Django activo |
| Prevención de Inyección SQL | ✅ Implementado | ORM de Django usado exclusivamente |
| Prevención de XSS | ✅ Implementado | Auto-escape de plantillas habilitado |
| Gestión de Secretos | ✅ Implementado | Variables de entorno, no en código |
| HTTPS/HSTS | ✅ Configurado | Configuración de producción impone SSL |
| Control de Acceso Basado en Roles | ✅ Implementado | Modelo de usuario con campo de rol |

### Mejoras Necesarias ⚠️

| ID | Hallazgo | Severidad | Esfuerzo |
|----|----------|-----------|----------|
| F-001 | Limitación de tasa de API no implementada | Media | 2-3h |
| F-002 | Sin suite de pruebas de seguridad | Media | 3-4h |
| F-003 | Mensajes de error pueden filtrar información | Media | 1h |
| F-004 | Cabeceras CSP no configuradas | Media | 1h |
| F-005 | Formulario de contacto no funcional | Baja | 2h |
| F-006 | Validación de carga de archivos incompleta | Media | 1h |

---

## Hallazgos Detallados

### F-001: Limitación de Tasa de API No Implementada

**Severidad:** Media
**Puntuación CVSS:** 5.3 (Media)
**Estado:** Abierto

**Descripción:**
El endpoint `/chat/` de la API no tiene limitación de tasa, permitiendo solicitudes ilimitadas. Esto podría permitir:
- Abuso de costos (llamadas excesivas a la API de IA)
- Denegación de servicio
- Ataques de fuerza bruta

**Evidencia:**
```python
# apps/ai_assistant/views.py
# No hay decorador de limitación de tasa presente
class ChatView(View):
    def post(self, request):
        ...
```

**Recomendación:**
Implementar limitación de tasa usando `django-ratelimit`:
- Anónimos: 10 solicitudes/minuto por IP
- Autenticados: 50 solicitudes/hora por usuario

**Tarea de Remediación:** T-066

---

### F-002: Suite de Pruebas de Seguridad Faltante

**Severidad:** Media
**Puntuación CVSS:** N/A (Brecha de Proceso)
**Estado:** Abierto

**Descripción:**
Aunque la aplicación tiene 440 pruebas con 96% de cobertura, no hay una suite de pruebas de seguridad dedicada que valide:
- Controles de autorización
- Validación de entrada (inyección SQL, XSS)
- Seguridad de sesión
- Protección CSRF

**Evidencia:**
```bash
$ grep -r "security" tests/
# No se encontraron archivos de prueba específicos de seguridad
```

**Recomendación:**
Crear `tests/test_security.py` cubriendo casos de prueba OWASP Top 10.

**Tarea de Remediación:** T-067

---

### F-003: Mensajes de Error Pueden Filtrar Información Sensible

**Severidad:** Media
**Puntuación CVSS:** 4.3 (Media)
**Estado:** Abierto

**Descripción:**
Algunos manejadores de errores usan `str(e)` lo cual podría exponer:
- Rutas de archivos internos
- Detalles del esquema de base de datos
- Claves de API en mensajes de error
- Trazas de pila

**Evidencia:**
```python
# Patrón encontrado en el código
except Exception as e:
    return JsonResponse({'error': str(e)}, status=500)
```

**Impacto:**
Los atacantes podrían usar la información filtrada para:
- Mapear la arquitectura interna
- Identificar componentes vulnerables
- Crear ataques dirigidos

**Recomendación:**
- Registrar excepciones completas en el servidor
- Devolver mensajes genéricos a los usuarios
- Implementar manejador de excepciones personalizado para DRF

**Tarea de Remediación:** T-068

---

### F-004: Política de Seguridad de Contenido No Configurada

**Severidad:** Media
**Puntuación CVSS:** 4.3 (Media)
**Estado:** Abierto

**Descripción:**
No se envía cabecera Content-Security-Policy, reduciendo la profundidad de defensa contra XSS.

**Evidencia:**
```bash
$ curl -I https://petfriendlyvet.com | grep -i content-security
# No se encontró cabecera CSP
```

**Recomendación:**
Configurar CSP usando `django-csp`:
```python
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "unpkg.com", "cdn.jsdelivr.net")
```

**Tarea de Remediación:** T-069

---

### F-005: Formulario de Contacto No Funcional

**Severidad:** Baja
**Puntuación CVSS:** N/A (Problema Funcional)
**Estado:** Abierto

**Descripción:**
El formulario de contacto recopila información del usuario pero:
- No envía notificaciones por correo
- No almacena los envíos
- No tiene protección contra spam

**Impacto:**
- Consultas de negocio perdidas
- Sin registro de auditoría de comunicaciones
- Objetivo potencial de spam

**Recomendación:**
- Almacenar envíos en base de datos
- Enviar correos de notificación
- Implementar prevención de spam con honeypot

**Tarea de Remediación:** T-070

---

### F-006: Validación de Carga de Archivos Incompleta

**Severidad:** Media
**Puntuación CVSS:** 5.3 (Media)
**Estado:** Abierto

**Descripción:**
El campo de carga de avatar carece de:
- Validación de tipo de archivo (verificación de tipo MIME)
- Límites de tamaño de archivo
- Saneamiento de nombres de archivo

**Evidencia:**
```python
# Campo avatar del modelo de usuario
avatar = models.ImageField(upload_to='avatars/', blank=True)
# Sin validadores especificados
```

**Impacto:**
- Posible carga de archivos maliciosos
- Traversal de ruta mediante nombres de archivo
- Denegación de servicio mediante archivos grandes

**Recomendación:**
- Validar tipo MIME usando python-magic
- Limitar tamaño de archivo a 2MB
- Sanear nombres de archivo (usar UUIDs)

**Tarea de Remediación:** T-071

---

## Evaluación OWASP Top 10

### A01:2021 – Control de Acceso Roto

| Verificación | Estado | Notas |
|--------------|--------|-------|
| Denegar por defecto | ✅ | Login requerido para vistas protegidas |
| RBAC implementado | ✅ | Roles de usuario: propietario, staff, vet, admin |
| Referencias directas a objetos | ✅ | Usuario solo puede acceder sus propios datos |
| Política CORS | ✅ | Configurada correctamente |
| Listado de directorios | ✅ | Deshabilitado |

**Evaluación:** APROBADO

---

### A02:2021 – Fallos Criptográficos

| Verificación | Estado | Notas |
|--------------|--------|-------|
| TLS/HTTPS | ✅ | Forzado en producción |
| Hash de contraseñas | ✅ | PBKDF2 con iteraciones |
| Datos sensibles encriptados | ✅ | Encriptación de base de datos |
| Secretos en código | ✅ | Todo en variables de entorno |

**Evaluación:** APROBADO

---

### A03:2021 – Inyección

| Verificación | Estado | Notas |
|--------------|--------|-------|
| Inyección SQL | ✅ | ORM de Django parametrizado |
| Inyección NoSQL | N/A | Sin bases de datos NoSQL |
| Inyección de comandos OS | ✅ | Sin comandos shell desde entrada de usuario |
| Inyección LDAP | N/A | Sin LDAP |

**Evaluación:** APROBADO

---

## Matriz de Riesgos

| Riesgo | Probabilidad | Impacto | General |
|--------|--------------|---------|---------|
| Abuso de costos de API IA | Alta | Media | Media |
| Divulgación de información | Media | Baja | Baja |
| Ataques XSS | Baja | Media | Baja |
| Acceso no autorizado | Baja | Alta | Media |
| Violación de datos | Muy Baja | Crítica | Baja |

---

## Recomendaciones

### Inmediato (Este Sprint)

1. **Implementar limitación de tasa** (F-001) - Prevenir abuso de API
2. **Crear suite de pruebas de seguridad** (F-002) - Establecer línea base
3. **Corregir filtración de mensajes de error** (F-003) - Victoria rápida de seguridad
4. **Agregar cabeceras CSP** (F-004) - Defensa en profundidad

### Corto Plazo (Próximo Sprint)

5. **Completar validación de carga de archivos** (F-006)
6. **Corregir formulario de contacto** (F-005)
7. **Agregar pip-audit al pipeline de CI**
8. **Implementar registro de seguridad**

### Largo Plazo (Sprints Futuros)

9. **Autenticación de dos factores**
10. **Requisitos de complejidad de contraseña**
11. **Bloqueo de cuenta después de intentos fallidos**
12. **Prueba de penetración por terceros**

---

## Conclusión

La aplicación de la Clínica Veterinaria Pet-Friendly demuestra fundamentos de seguridad sólidos con las protecciones integradas de Django correctamente configuradas. Las mejoras identificadas son medidas de defensa en profundidad que mejorarán la postura de seguridad general.

**Fortalezas Clave:**
- Protecciones a nivel de framework activas
- Secretos gestionados correctamente
- HTTPS forzado
- Acceso basado en roles implementado

**Áreas de Mejora:**
- Limitación de tasa necesaria
- Brecha en pruebas de seguridad
- Refinamiento de manejo de errores
- Cabeceras de seguridad adicionales

**Evaluación General:** La aplicación está lista para producción con las mejoras recomendadas programadas para el sprint de endurecimiento de seguridad.

---

## Apéndice A: Herramientas Utilizadas

- Revisión manual de código
- Lista de verificación de seguridad de Django
- Lista de verificación OWASP Top 10 2021
- grep/búsqueda de patrones de seguridad

## Apéndice B: Referencias

- [OWASP Top 10 2021](https://owasp.org/Top10/)
- [Documentación de Seguridad de Django](https://docs.djangoproject.com/en/5.0/topics/security/)
- [CWE Top 25](https://cwe.mitre.org/top25/archive/2023/2023_top25_list.html)

---

*Informe Generado: 23 de diciembre de 2025*
*Próxima Auditoría: Marzo 2026*
