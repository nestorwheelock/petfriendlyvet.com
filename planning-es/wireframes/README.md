# Wireframes: Sitio Web Pet-Friendly

## Resumen

Este documento contiene wireframes ASCII para todas las páginas del sitio web Pet-Friendly. Estos wireframes definen el diseño, componentes y flujos de usuario antes de la implementación.

## Páginas Cubiertas

### Wireframes Existentes

| Archivo Wireframe | Página(s) | Época |
|-------------------|-----------|-------|
| 01-homepage.txt | Página de inicio (escritorio + móvil) | 1 |
| 02-about.txt | Sobre el Dr. Pablo y la Clínica | 1 |
| 03-services.txt | Servicios Veterinarios | 1 |
| 04-contact.txt | Contacto y Ubicación | 1 |
| 05-appointment.txt | Formulario de Reserva de Citas | 2 |
| 06-store.txt | Catálogo de Tienda y Páginas de Productos | 3 |
| 07-cart-checkout.txt | Carrito de Compras y Pago | 3 |
| 08-pharmacy.txt | Información de Farmacia | 3 |
| 09-ai-chat.txt | Interfaz de Chat IA (cliente + admin) | 1 |
| 10-competitive-intelligence.txt | Mapa y Análisis de Competidores | 5 |
| 11-pet-profile.txt | Panel de Perfil de Mascota | 2 |
| 12-travel-certificates.txt | Flujo de Solicitud de Certificado de Viaje | 2 |
| 13-external-services.txt | Directorio de Socios y Referencias | 2 |

### Wireframes Necesarios (Por Crear)

| Archivo Wireframe | Página(s) | Época | Historia |
|-------------------|-----------|-------|----------|
| 14-inventory-admin.txt | Panel de Gestión de Inventario | 3 | S-024 |
| 15-billing-admin.txt | Gestión de Facturación y Facturas | 3 | S-020 |
| 16-communications-inbox.txt | Bandeja Unificada (WhatsApp, SMS, Email) | 4 | S-006 |
| 17-emergency-triage.txt | Flujo de Servicios de Emergencia | 4 | S-015 |
| 18-referral-network.txt | Especialistas y Veterinarios Visitantes | 4 | S-025 |
| 19-crm-dashboard.txt | Perfiles de Propietarios CRM | 5 | S-007 |
| 20-loyalty-program.txt | Puntos de Lealtad y Recompensas | 5 | S-016 |
| 21-reports-dashboard.txt | Reportes y Analíticas | 6 | S-017 |
| 22-accounting-dashboard.txt | Resumen de Contabilidad | 6 | S-026 |

## Patrones de Diseño

### Esquema de Colores (del logo)
- **Azul Primario:** #1E4D8C (texto PET-FRIENDLY)
- **Verde Secundario:** #5FAD41 (CLÍNICA FARMACIA TIENDA)
- **Blanco/Claro:** Fondo, tarjetas
- **Texto Oscuro:** #333333

### Tipografía
- Encabezados: Sans-serif en negrita (similar al logo)
- Cuerpo: Sans-serif limpia (Inter, Open Sans, o similar)

### Patrones de Componentes

**Encabezado (Todas las Páginas)**
- Logo (izquierda)
- Navegación (centro)
- Selector de idioma + ícono de carrito (derecha)

**Pie de Página (Todas las Páginas)**
- Información de contacto
- Enlaces rápidos
- Redes sociales
- Copyright

**Botones**
- Primario: Fondo azul, texto blanco
- Secundario: Fondo verde, texto blanco
- Contorno: Fondo blanco, borde de color

### Puntos de Ruptura Responsivos
- Escritorio: > 1024px
- Tableta: 768px - 1024px
- Móvil: < 768px

## Flujos de Usuario

### Flujo de Chat IA (Interfaz Principal)
```
Cualquier Página → Widget de Chat → Conversación → IA Maneja Solicitud
    ├── Consulta de Información → IA Responde
    ├── Solicitud de Cita → IA Reserva → Confirmación
    ├── Pregunta sobre Producto → IA Muestra Productos → Agregar al Carrito
    └── Pregunta sobre Mascota → IA Recupera Registros → Mostrar Info
```

### Flujo de Reserva de Citas
```
Página de inicio → Servicios → Reservar Cita → Llenar Formulario → Confirmación
    o
Página de inicio → CTA Reservar Ahora → Llenar Formulario → Confirmación
    o
Chat IA → "Necesito una cita" → IA Agenda → Confirmación
```

### Flujo de Compras
```
Página de inicio → Tienda → Categoría → Producto → Agregar al Carrito →
Carrito → Pago → Pago → Confirmación de Pedido
    o
Chat IA → "Necesito medicina antipulgas" → IA Muestra Opciones → Agregar al Carrito
```

### Flujo de Certificado de Viaje
```
Perfil de Mascota → Planes de Viaje → Seleccionar Destino →
Lista de Requisitos → Agendar Examen → Certificado Emitido
```

### Flujo de Emergencia
```
Página de inicio → Botón de Emergencia → Preguntas de Triaje →
Evaluación de Gravedad → Acción (Escalar/Consejo/Agendar)
```

### Flujo de Referencia
```
Registro de Mascota → Referencia Necesaria → Buscar Especialista →
Crear Referencia → Enviar → Rastrear Estado → Recibir Reporte
```

### Flujo de Información
```
Página de inicio → Sobre/Servicios/Contacto/Farmacia → Detalles
```

## Notas de Accesibilidad

- Todas las imágenes necesitan texto alternativo
- Los campos de formulario necesitan etiquetas
- El contraste de color debe cumplir con WCAG AA
- Soporte de navegación por teclado
- Estructura amigable para lectores de pantalla

## Notas de Implementación

- Usar Tailwind CSS para estilos
- HTMX para interacciones dinámicas
- Alpine.js para estado del carrito y estado de UI
- Todo el texto debe soportar multilingüe (ES/EN/DE/FR/IT + IA bajo demanda)
- Widget de Chat IA presente en todas las páginas (esquina inferior derecha)
- Enfoque de diseño móvil primero
- Los wireframes de administración deben soportar acceso móvil (Dr. Pablo usa teléfono)

---

**Versión:** 2.2.0
**Historias Cubiertas:** 26 historias de usuario a través de 6 épocas
**Fecha:** 21 de diciembre de 2025
