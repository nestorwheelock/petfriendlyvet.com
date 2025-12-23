# Documento Técnico de Seguridad

## Arquitectura de Seguridad Integral para Gestión de Práctica Veterinaria

**Clínica Veterinaria Pet-Friendly**
**Versión 1.0 | Diciembre 2025**

---

## Resumen

Este documento técnico presenta la arquitectura de seguridad integral implementada en la aplicación web de la Clínica Veterinaria Pet-Friendly. Detalla el enfoque de seguridad multicapa, el cumplimiento con estándares de la industria y la metodología sistemática utilizada para proteger datos sensibles veterinarios y de clientes. El documento sirve tanto como referencia técnica como demostración del compromiso con la seguridad para partes interesadas, auditores y socios potenciales.

---

## Tabla de Contenidos

1. [Resumen Ejecutivo](#1-resumen-ejecutivo)
2. [Panorama de Amenazas](#2-panorama-de-amenazas)
3. [Arquitectura de Seguridad](#3-arquitectura-de-seguridad)
4. [Cumplimiento OWASP Top 10](#4-cumplimiento-owasp-top-10)
5. [Protección de Datos](#5-protección-de-datos)
6. [Autenticación y Autorización](#6-autenticación-y-autorización)
7. [Controles de Seguridad de Aplicación](#7-controles-de-seguridad-de-aplicación)
8. [Seguridad de Infraestructura](#8-seguridad-de-infraestructura)
9. [Metodología de Pruebas de Seguridad](#9-metodología-de-pruebas-de-seguridad)
10. [Respuesta a Incidentes](#10-respuesta-a-incidentes)
11. [Consideraciones de Cumplimiento y Regulación](#11-consideraciones-de-cumplimiento-y-regulación)
12. [Hoja de Ruta Futura](#12-hoja-de-ruta-futura)
13. [Apéndices](#apéndices)

---

## 1. Resumen Ejecutivo

### 1.1 Propósito

La aplicación de la Clínica Veterinaria Pet-Friendly maneja datos sensibles incluyendo:
- Información de identificación personal (PII) de dueños de mascotas
- Registros médicos de pacientes animales
- Datos de transacciones financieras
- Datos operacionales críticos del negocio

Este documento técnico documenta las medidas de seguridad implementadas para proteger estos datos y asegurar la continuidad del negocio.

### 1.2 Filosofía de Seguridad

Nuestro enfoque de seguridad sigue tres principios fundamentales:

1. **Defensa en Profundidad** - Múltiples capas de seguridad superpuestas aseguran que la falla de un control no comprometa el sistema
2. **Mínimo Privilegio** - Los usuarios y sistemas tienen solo el acceso mínimo requerido para realizar sus funciones
3. **Seguridad por Diseño** - Las consideraciones de seguridad se integran desde las fases de diseño más tempranas, no se agregan después

### 1.3 Alcance

Este documento cubre:
- Seguridad de aplicación web (basada en Django)
- Seguridad de API
- Protección de datos y encriptación
- Autenticación y control de acceso
- Seguridad de infraestructura
- Consideraciones de cumplimiento

---

## 2. Panorama de Amenazas

### 2.1 Amenazas Específicas de la Industria

Las prácticas veterinarias enfrentan desafíos de seguridad únicos:

| Categoría de Amenaza | Ejemplos | Nivel de Riesgo |
|----------------------|----------|-----------------|
| **Robo de Datos** | PII de clientes, datos de pago, registros médicos | Alto |
| **Fraude Financiero** | Manipulación de pagos, fraude de facturas | Medio |
| **Ransomware** | Interrupción del negocio, encriptación de datos | Alto |
| **Inteligencia de Competidores** | Datos de precios, listas de clientes | Bajo |
| **Amenazas Internas** | Empleados descontentos, divulgación accidental | Medio |

### 2.2 Vectores de Ataque Comunes

Basado en datos de la industria e investigación de OWASP, los principales vectores de ataque incluyen:

```
┌─────────────────────────────────────────────────────────┐
│                   Vectores de Ataque                     │
├─────────────────────────────────────────────────────────┤
│  1. Ataques de Inyección (SQL, XSS, Comando) [BLOQUEADO]│
│  2. Autenticación Rota                       [MITIGADO] │
│  3. Exposición de Datos Sensibles            [PROTEGIDO]│
│  4. Entidades Externas XML (XXE)             [N/A]      │
│  5. Control de Acceso Roto                   [MITIGADO] │
│  6. Configuración Incorrecta de Seguridad    [ENDURECIDO]│
│  7. Cross-Site Scripting (XSS)               [BLOQUEADO]│
│  8. Deserialización Insegura                 [MITIGADO] │
│  9. Componentes con Vulnerabilidades         [MONITOREADO]│
│  10. Registro y Monitoreo Insuficiente       [MEJORANDO]│
└─────────────────────────────────────────────────────────┘
```

### 2.3 Actores de Amenaza

| Tipo de Actor | Motivación | Capacidad | Probabilidad |
|---------------|------------|-----------|--------------|
| Hackers Oportunistas | Ganancia financiera | Baja-Media | Alta |
| Crimen Organizado | Robo de datos, ransomware | Alta | Media |
| Competidores | Inteligencia de negocio | Baja | Baja |
| Internos | Varios | Variable | Media |
| Script Kiddies | Notoriedad | Baja | Alta |

---

## 3. Arquitectura de Seguridad

### 3.1 Modelo de Defensa en Profundidad

```
┌─────────────────────────────────────────────────────────┐
│                   CAPA 1: PERÍMETRO                      │
│    ┌─────────────────────────────────────────────────┐  │
│    │  CDN/WAF (Cloudflare)                           │  │
│    │  - Protección DDoS                              │  │
│    │  - Mitigación de bots                           │  │
│    │  - Terminación SSL/TLS                          │  │
│    └─────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│                     CAPA 2: RED                          │
│    ┌─────────────────────────────────────────────────┐  │
│    │  Proxy Inverso Nginx                            │  │
│    │  - Limitación de tasa                           │  │
│    │  - Cabeceras de seguridad                       │  │
│    │  - Filtrado de solicitudes                      │  │
│    └─────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│                   CAPA 3: APLICACIÓN                     │
│    ┌─────────────────────────────────────────────────┐  │
│    │  Framework Django                               │  │
│    │  - Protección CSRF                              │  │
│    │  - Prevención XSS                               │  │
│    │  - Prevención de inyección SQL                  │  │
│    │  - Gestión de sesiones                          │  │
│    │  - Autenticación/Autorización                   │  │
│    └─────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────┤
│                     CAPA 4: DATOS                        │
│    ┌─────────────────────────────────────────────────┐  │
│    │  Base de Datos PostgreSQL                       │  │
│    │  - Encriptación en reposo                       │  │
│    │  - Controles de acceso                          │  │
│    │  - Registro de auditoría                        │  │
│    └─────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 3.2 Seguridad del Stack Tecnológico

| Componente | Tecnología | Características de Seguridad |
|------------|------------|------------------------------|
| Framework | Django 5.0 | Middleware de seguridad incorporado, ORM, CSRF |
| Base de Datos | PostgreSQL 15 | Seguridad a nivel de fila, encriptación |
| Servidor Web | Nginx | Limitación de tasa, cabeceras de seguridad |
| Caché | Redis | Autenticación, conexiones encriptadas |
| CDN | Cloudflare | Protección DDoS, WAF, SSL |
| Integración IA | OpenRouter | Autenticación con clave API, límites de tasa |

---

## 4. Cumplimiento OWASP Top 10

### 4.1 A01:2021 – Control de Acceso Roto

**Riesgo:** Acceso no autorizado a recursos o funcionalidad

**Implementación:**

```python
# Control de acceso basado en roles
class User(AbstractUser):
    ROLE_CHOICES = [
        ('owner', 'Dueño de Mascota'),
        ('staff', 'Miembro del Personal'),
        ('vet', 'Veterinario'),
        ('admin', 'Administrador'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    @property
    def is_staff_member(self):
        return self.role in ['staff', 'vet', 'admin']
```

**Controles:**
- ✅ Denegar por defecto
- ✅ Control de acceso basado en roles (RBAC)
- ✅ Permisos a nivel de objeto
- ✅ CORS configurado correctamente
- ✅ Listado de directorios deshabilitado

### 4.2 A02:2021 – Fallos Criptográficos

**Riesgo:** Exposición de datos sensibles debido a criptografía débil

**Implementación:**
- TLS 1.2+ para todas las conexiones
- HSTS con duración de 1 año
- Hash de contraseñas PBKDF2 con alto conteo de iteraciones
- Secretos almacenados en variables de entorno

**Controles:**
- ✅ HTTPS forzado
- ✅ Hash de contraseñas fuerte
- ✅ Sin datos sensibles en URLs
- ✅ Flags de cookies seguros

### 4.3 A03:2021 – Inyección

**Riesgo:** Ataques de inyección SQL, NoSQL, OS o LDAP

**Implementación:**

```python
# El ORM de Django previene inyección SQL
# Seguro:
User.objects.filter(email=user_input)

# Nunca usado:
# cursor.execute(f"SELECT * FROM users WHERE email = '{user_input}'")
```

**Controles:**
- ✅ Consultas parametrizadas (ORM)
- ✅ Validación de entrada
- ✅ Auto-escape de plantillas
- ✅ Sin ejecución de comandos shell desde entrada de usuario

---

## 5. Protección de Datos

### 5.1 Clasificación de Datos

| Clasificación | Ejemplos | Nivel de Protección |
|---------------|----------|---------------------|
| **Público** | Descripciones de servicios, horarios | Estándar |
| **Interno** | Horarios del personal, precios | Control de acceso |
| **Confidencial** | PII de clientes, registros de mascotas | Encriptación + Control de acceso |
| **Restringido** | Datos de pago, contraseñas | Encriptación + Acceso estricto |

### 5.2 Encriptación

**En Reposo:**
- Base de datos: Encriptación de PostgreSQL
- Archivos: Volúmenes de almacenamiento encriptados
- Respaldos: Encriptados y con acceso controlado

**En Tránsito:**
- TLS 1.2+ para todas las conexiones
- HSTS forzado
- Transparencia de certificados

---

## 6. Autenticación y Autorización

### 6.1 Métodos de Autenticación

| Método | Caso de Uso | Nivel de Seguridad |
|--------|-------------|-------------------|
| Email/Contraseña | Login estándar | Alto |
| Google OAuth | Login social | Alto |
| Tokens de Sesión | Estado mantenido | Alto |
| Claves API | Integración de servicios | Alto |

### 6.2 Modelo de Autorización

```
┌─────────────────────────────────────────────────────────┐
│                   Flujo de Autorización                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Solicitud → Autenticación → Verificación → Permiso    │
│                   │              de Rol        │        │
│                   ▼                ▼           ▼        │
│         ¿Está logueado?      ¿Qué rol?   ¿Tiene acceso?│
│                   │                │           │        │
│            No → 401           propietario  Sí → Permitir│
│            Sí ↓              personal     No → 403     │
│                               veterinario              │
│                                admin                   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 6.3 Matriz de Permisos por Rol

| Recurso | Propietario | Personal | Veterinario | Admin |
|---------|-------------|----------|-------------|-------|
| Perfil propio | ✅ RW | ✅ RW | ✅ RW | ✅ RW |
| Mascotas propias | ✅ RW | - | - | ✅ RW |
| Todas las mascotas | - | ✅ R | ✅ RW | ✅ RW |
| Citas | ✅ Propias | ✅ RW | ✅ RW | ✅ RW |
| Registros médicos | ✅ R | ✅ R | ✅ RW | ✅ RW |
| Panel de admin | - | ✅ Limitado | ✅ Limitado | ✅ Completo |
| Config del sistema | - | - | - | ✅ RW |

---

## 7. Controles de Seguridad de Aplicación

### 7.1 Validación de Entrada

Toda entrada de usuario es validada:

```python
# Validación de formulario
class ContactForm(forms.Form):
    email = forms.EmailField()
    message = forms.CharField(max_length=5000)

    def clean_message(self):
        message = self.cleaned_data['message']
        if len(message) < 10:
            raise ValidationError('Mensaje muy corto')
        return message
```

### 7.2 Codificación de Salida

Las plantillas de Django escapan automáticamente por defecto:

```html
<!-- Escapado automáticamente -->
<p>{{ user_input }}</p>

<!-- Marcado explícitamente como seguro (usado con moderación) -->
<p>{{ trusted_html|safe }}</p>
```

### 7.3 Política de Seguridad de Contenido

```python
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "unpkg.com", "cdn.jsdelivr.net")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "fonts.googleapis.com")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FRAME_ANCESTORS = ("'none'",)
```

### 7.4 Limitación de Tasa

```python
# Límites de tasa de API
@ratelimit(key='ip', rate='10/m', block=True)  # Anónimo
@ratelimit(key='user', rate='50/h', block=True)  # Autenticado
def chat_api(request):
    ...
```

---

## 8. Seguridad de Infraestructura

### 8.1 Endurecimiento del Servidor

- Instalación mínima del SO
- Parches de seguridad regulares
- Reglas de firewall (permitir solo 80, 443, 22)
- Autenticación SSH solo por clave
- Fail2ban para protección contra fuerza bruta

### 8.2 Seguridad de Red

```
┌─────────────────────────────────────────────────────────┐
│                   Arquitectura de Red                    │
├─────────────────────────────────────────────────────────┤
│                                                          │
│   Internet                                               │
│       │                                                  │
│       ▼                                                  │
│   ┌──────────┐                                          │
│   │Cloudflare│ ← Protección DDoS, WAF                   │
│   └────┬─────┘                                          │
│        │                                                 │
│        ▼                                                 │
│   ┌──────────┐                                          │
│   │  Nginx   │ ← Limitación de tasa, cabeceras          │
│   └────┬─────┘                                          │
│        │                                                 │
│        ▼                                                 │
│   ┌──────────┐                                          │
│   │  Django  │ ← Seguridad de aplicación                │
│   └────┬─────┘                                          │
│        │                                                 │
│        ▼                                                 │
│   ┌──────────┐                                          │
│   │PostgreSQL│ ← Controles de acceso, encriptación      │
│   └──────────┘                                          │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 9. Metodología de Pruebas de Seguridad

### 9.1 Pirámide de Pruebas

```
                    ┌─────────────┐
                    │  Pruebas de │  ← Anual, terceros
                    │ Penetración │
                   ┌┴─────────────┴┐
                   │  Integración   │  ← Trimestral
                   │  de Seguridad  │
                  ┌┴───────────────┴┐
                  │   Pruebas de     │  ← Continuo
                  │ Seguridad Auto.  │
                 ┌┴─────────────────┴┐
                 │  Análisis Estático │  ← Cada commit
                 │    de Código       │
                └─────────────────────┘
```

### 9.2 Categorías de Pruebas de Seguridad

| Categoría | Pruebas | Frecuencia |
|-----------|---------|------------|
| Autorización | 10+ | Cada build |
| Inyección | 15+ | Cada build |
| Autenticación | 8+ | Cada build |
| Sesión | 5+ | Cada build |
| Validación de entrada | 20+ | Cada build |

---

## 10. Respuesta a Incidentes

### 10.1 Plan de Respuesta

```
┌─────────────────────────────────────────────────────────┐
│              Flujo de Respuesta a Incidentes             │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. DETECCIÓN         2. CONTENCIÓN                     │
│     ┌──────┐            ┌──────┐                        │
│     │Alerta│ ─────────▶ │Aislar│                        │
│     └──────┘            └──────┘                        │
│                             │                            │
│                             ▼                            │
│  4. RECUPERACIÓN      3. ERRADICACIÓN                   │
│     ┌──────┐            ┌──────┐                        │
│     │Restaurar│◀────────│Corregir│                      │
│     └──────┘            └──────┘                        │
│         │                                                │
│         ▼                                                │
│  5. LECCIONES APRENDIDAS                                 │
│     ┌──────────────┐                                    │
│     │Documentar/Mejorar│                                │
│     └──────────────┘                                    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 10.2 Información de Contacto

- **Equipo de Seguridad:** security@petfriendlyvet.com
- **Tiempo de Respuesta:** 24-48 horas
- **Escalación:** Lista de contactos de emergencia mantenida internamente

---

## 11. Consideraciones de Cumplimiento y Regulación

### 11.1 Protección de Datos

**Protección de Datos Mexicana (LFPDPPP):**
- Aviso de privacidad proporcionado
- Consentimiento obtenido para procesamiento de datos
- Derechos del titular de datos soportados
- Medidas de seguridad documentadas

**Consideraciones GDPR (para visitantes de la UE):**
- Base legal para procesamiento
- Minimización de datos
- Derecho a borrado soportado
- Salvaguardas de transferencia transfronteriza

### 11.2 Estándares de la Industria

| Estándar | Estado | Notas |
|----------|--------|-------|
| OWASP Top 10 | ✅ Cumple | Ver Sección 4 |
| PCI DSS | ⚠️ Parcial | Procesamiento de pagos externalizado a Stripe |
| SOC 2 | ❌ No certificado | Considerar para clientes empresariales |

---

## 12. Hoja de Ruta Futura

### 12.1 Corto Plazo (2025 Q1)

- ✅ Implementar limitación de tasa
- ✅ Agregar suite de pruebas de seguridad
- ✅ Configurar cabeceras CSP
- ⬜ Escaneo automatizado de vulnerabilidades

### 12.2 Mediano Plazo (2025 Q2-Q3)

- ⬜ Autenticación de dos factores
- ⬜ Registro de seguridad mejorado
- ⬜ Prueba de penetración por terceros
- ⬜ Preparación SOC 2 Tipo 1

### 12.3 Largo Plazo (2025 Q4+)

- ⬜ Programa de recompensas por bugs
- ⬜ Certificación SOC 2 Tipo 2
- ⬜ Detección avanzada de amenazas
- ⬜ Evaluación de arquitectura de confianza cero

---

## Apéndices

### Apéndice A: Lista de Verificación de Configuración de Seguridad

```
□ Configuración de Django
  □ DEBUG = False
  □ SECRET_KEY desde entorno
  □ ALLOWED_HOSTS configurado
  □ SECURE_SSL_REDIRECT = True
  □ SESSION_COOKIE_SECURE = True
  □ CSRF_COOKIE_SECURE = True

□ Configuración de Nginx
  □ Solo TLS 1.2+
  □ Cabeceras de seguridad presentes
  □ Limitación de tasa habilitada

□ Base de Datos
  □ Credenciales no predeterminadas
  □ Acceso de red restringido
  □ Encriptación habilitada
```

### Apéndice B: Dependencias de Seguridad

| Paquete | Propósito | Versión |
|---------|-----------|---------|
| django | Framework web | 5.0.x |
| django-ratelimit | Limitación de tasa | 4.1.x |
| django-csp | Política de Seguridad de Contenido | 3.8.x |
| python-magic | Validación de tipo de archivo | 0.4.x |
| Pillow | Validación de imagen | 10.x |

### Apéndice C: Referencias

1. OWASP Top 10 2021 - https://owasp.org/Top10/
2. Documentación de Seguridad de Django - https://docs.djangoproject.com/en/5.0/topics/security/
3. Marco de Ciberseguridad NIST - https://www.nist.gov/cyberframework
4. CWE Top 25 - https://cwe.mitre.org/top25/

---

*Versión del Documento: 1.0*
*Última Actualización: 23 de diciembre de 2025*
*Clasificación: Uso Interno*
*Propietario: Equipo de Desarrollo*
