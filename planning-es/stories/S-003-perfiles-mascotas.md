# S-003: Perfiles de Mascotas + Registros Médicos

**Tipo de Historia:** Historia de Usuario
**Prioridad:** Alta
**Estimación:** 4 días
**Época:** 2
**Estado:** Pendiente

## Historia de Usuario
**Como** dueño de mascota
**Quiero** ver y gestionar los perfiles y registros médicos de mis mascotas
**Para que** tenga toda la información de salud de mis mascotas en un solo lugar

## Criterios de Aceptación
- [ ] Puedo ver todos mis mascotas en mi dashboard
- [ ] Puedo ver información básica de cada mascota (nombre, especie, raza, edad)
- [ ] Puedo ver historial de vacunas
- [ ] Puedo ver medicamentos actuales
- [ ] Puedo ver historial de visitas
- [ ] Puedo subir fotos de mi mascota
- [ ] Puedo ver documentos médicos
- [ ] Información de alergias claramente visible

## Definición de Hecho
- [ ] Modelos de mascota completos
- [ ] Vista de perfil responsiva
- [ ] Carga de archivos funcionando
- [ ] Pruebas >95% cobertura

## Tareas Relacionadas
- T-024: Modelos de Mascota
- T-025: Modelos de Registros Médicos
- T-026: Vistas de Perfil de Mascota
- T-027: Herramientas de IA para Mascotas

## Wireframe
Ver: `planning/wireframes/11-pet-profile.txt`

## Modelos de Datos

### Mascota
| Campo | Tipo | Descripción |
|-------|------|-------------|
| nombre | CharField | Nombre de la mascota |
| especie | CharField | perro, gato, ave, conejo, otro |
| raza | CharField | Raza |
| color | CharField | Color/marcas |
| fecha_nacimiento | Date | Fecha de nacimiento |
| genero | CharField | macho, hembra |
| peso_kg | Decimal | Peso actual |
| microchip | CharField | Número de microchip |
| foto | ImageField | Foto de la mascota |
| notas | TextField | Notas generales |
| activo | Boolean | Activo en sistema |

### Registro Médico
| Campo | Tipo | Descripción |
|-------|------|-------------|
| mascota | FK(Mascota) | Mascota relacionada |
| tipo | CharField | examen, vacuna, cirugía, lab |
| fecha | Date | Fecha del registro |
| titulo | CharField | Título del registro |
| descripcion | TextField | Detalles |
| diagnostico | TextField | Diagnóstico |
| tratamiento | TextField | Tratamiento dado |
| creado_por | FK(User) | Personal que creó |

### Vacuna
| Campo | Tipo | Descripción |
|-------|------|-------------|
| mascota | FK(Mascota) | Mascota vacunada |
| vacuna | CharField | Nombre de vacuna |
| lote | CharField | Número de lote |
| fecha_aplicacion | Date | Fecha aplicada |
| proxima_fecha | Date | Próxima dosis |
| aplicado_por | FK(User) | Veterinario |
