# S-016: Programa de Lealtad y Recompensas

> **LECTURA OBLIGATORIA:** Antes de la implementación, revisar [ESTANDARES_CODIGO.md](../ESTANDARES_CODIGO.md) y [DECISIONES_ARQUITECTURA.md](../DECISIONES_ARQUITECTURA.md)

**Tipo de Historia:** Historia de Usuario
**Prioridad:** Baja
**Época:** 5 (con CRM)
**Estado:** PENDIENTE
**Módulo:** django-crm-lite

## Historia de Usuario

**Como** dueño de mascota
**Quiero** ganar recompensas por mi lealtad a la clínica
**Para que** me sienta valorado y ahorre dinero en el cuidado de mascotas

**Como** dueño de clínica
**Quiero** recompensar a clientes leales
**Para que** aumente la retención y fomente visitas repetidas

**Como** dueño de mascota
**Quiero** referir amigos y ganar bonos
**Para que** pueda ayudar a otros a encontrar excelente atención y beneficiarme

## Criterios de Aceptación

### Sistema de Puntos
- [ ] Ganar puntos en compras y servicios
- [ ] Conversión clara de puntos a moneda
- [ ] Puntos visibles en panel de cuenta
- [ ] Política de expiración de puntos
- [ ] Promociones de puntos de bonificación
- [ ] IA notifica del saldo de puntos

### Niveles de Recompensa
- [ ] Múltiples niveles de membresía (Bronce, Plata, Oro, Platino)
- [ ] Beneficios de nivel claramente mostrados
- [ ] Actualización automática basada en gasto
- [ ] Notificaciones de estado de nivel
- [ ] Ventajas exclusivas por nivel

### Redención
- [ ] Canjear puntos por descuentos
- [ ] Canjear por servicios gratuitos
- [ ] Canjear por productos
- [ ] Redención fácil vía chat IA
- [ ] Historial de redención

### Programa de Referencias
- [ ] Códigos/enlaces de referencia únicos
- [ ] Recompensa para quien refiere
- [ ] Bono de bienvenida para referido
- [ ] Rastrear estado de referencia
- [ ] Tabla de clasificación de referencias (opcional)

### Recompensas Especiales
- [ ] Recompensas de cumpleaños (cumpleaños de mascotas)
- [ ] Recompensas de aniversario (cliente desde)
- [ ] Descuentos por múltiples mascotas
- [ ] Descuentos de paquetes prepagos
- [ ] Promociones estacionales

## Requisitos Técnicos

### Modelos

```python
class LoyaltyProgram(models.Model):
    """Configuración del programa de lealtad"""
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    # Points configuration
    points_per_peso = models.DecimalField(max_digits=5, decimal_places=2, default=1)
    peso_per_point = models.DecimalField(max_digits=5, decimal_places=2, default=0.10)
    # 1 peso spent = 1 point, 1 point = $0.10 discount

    # Expiration
    points_expire = models.BooleanField(default=True)
    expiration_months = models.IntegerField(default=12)

    # Minimum redemption
    min_points_to_redeem = models.IntegerField(default=100)
    max_discount_percentage = models.IntegerField(default=20)
    # Can't discount more than 20% of purchase with points

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LoyaltyTier(models.Model):
    """Niveles de membresía"""
    program = models.ForeignKey(LoyaltyProgram, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    name_es = models.CharField(max_length=50)

    # Requirements
    min_spend = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    # Lifetime spend to reach this tier
    min_visits = models.IntegerField(default=0)

    # Benefits
    points_multiplier = models.DecimalField(max_digits=3, decimal_places=1, default=1.0)
    # 1.0 = normal, 1.5 = 50% bonus points
    discount_percentage = models.IntegerField(default=0)
    # Automatic discount on all purchases

    # Perks
    perks = models.JSONField(default=list)
    # ["priority_booking", "free_nail_trim", "birthday_gift", ...]

    # Display
    color = models.CharField(max_length=7, default='#CD7F32')  # Bronze
    icon = models.CharField(max_length=50, blank=True)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']


class MemberProfile(models.Model):
    """Membresía de lealtad del cliente"""
    owner = models.OneToOneField(User, on_delete=models.CASCADE)
    program = models.ForeignKey(LoyaltyProgram, on_delete=models.CASCADE)
    tier = models.ForeignKey(LoyaltyTier, on_delete=models.SET_NULL, null=True)

    # Points
    points_balance = models.IntegerField(default=0)
    points_earned_lifetime = models.IntegerField(default=0)
    points_redeemed_lifetime = models.IntegerField(default=0)

    # Spending
    total_spend = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_visits = models.IntegerField(default=0)

    # Referral
    referral_code = models.CharField(max_length=20, unique=True)
    referred_by = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True
    )
    referral_count = models.IntegerField(default=0)
    referral_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Status
    is_active = models.BooleanField(default=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    tier_updated_at = models.DateTimeField(null=True)


class PointsTransaction(models.Model):
    """Historial de ganancia y redención de puntos"""
    TRANSACTION_TYPES = [
        ('earned', 'Points Earned'),
        ('redeemed', 'Points Redeemed'),
        ('bonus', 'Bonus Points'),
        ('expired', 'Points Expired'),
        ('adjustment', 'Manual Adjustment'),
        ('referral', 'Referral Bonus'),
    ]

    member = models.ForeignKey(MemberProfile, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    points = models.IntegerField()  # Positive = earned, Negative = spent
    balance_after = models.IntegerField()

    # Reference
    description = models.CharField(max_length=200)
    order = models.ForeignKey(
        'store.Order', on_delete=models.SET_NULL, null=True, blank=True
    )
    appointment = models.ForeignKey(
        'appointments.Appointment', on_delete=models.SET_NULL, null=True, blank=True
    )

    # For expiration tracking
    expires_at = models.DateTimeField(null=True, blank=True)
    expired = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ['-created_at']


class Reward(models.Model):
    """Recompensas canjeables"""
    REWARD_TYPES = [
        ('discount', 'Discount'),
        ('service', 'Free Service'),
        ('product', 'Free Product'),
        ('upgrade', 'Service Upgrade'),
    ]

    name = models.CharField(max_length=100)
    name_es = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    reward_type = models.CharField(max_length=20, choices=REWARD_TYPES)

    # Cost
    points_required = models.IntegerField()

    # Value
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    discount_percentage = models.IntegerField(null=True, blank=True)
    free_service = models.ForeignKey(
        'appointments.ServiceType', on_delete=models.SET_NULL, null=True, blank=True
    )
    free_product = models.ForeignKey(
        'store.Product', on_delete=models.SET_NULL, null=True, blank=True
    )

    # Restrictions
    min_tier = models.ForeignKey(
        LoyaltyTier, on_delete=models.SET_NULL, null=True, blank=True
    )
    min_purchase = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    valid_days = models.IntegerField(default=30)  # Days until expiration

    # Availability
    is_active = models.BooleanField(default=True)
    limited_quantity = models.IntegerField(null=True, blank=True)
    quantity_remaining = models.IntegerField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    # Display
    image = models.ImageField(upload_to='rewards/', null=True, blank=True)
    featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order', 'points_required']


class RedeemedReward(models.Model):
    """Seguimiento de recompensas canjeadas"""
    member = models.ForeignKey(MemberProfile, on_delete=models.CASCADE)
    reward = models.ForeignKey(Reward, on_delete=models.CASCADE)
    points_spent = models.IntegerField()

    # Redemption code
    code = models.CharField(max_length=20, unique=True)

    # Status
    status = models.CharField(max_length=20, default='active')
    # active, used, expired, cancelled
    used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()

    # Usage reference
    order = models.ForeignKey(
        'store.Order', on_delete=models.SET_NULL, null=True, blank=True
    )
    appointment = models.ForeignKey(
        'appointments.Appointment', on_delete=models.SET_NULL, null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)


class Referral(models.Model):
    """Seguimiento de referencias"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('registered', 'Registered'),
        ('qualified', 'Qualified'),
        ('rewarded', 'Rewarded'),
    ]

    referrer = models.ForeignKey(
        MemberProfile, on_delete=models.CASCADE, related_name='referrals_made'
    )
    referred_email = models.EmailField(blank=True)
    referred_phone = models.CharField(max_length=20, blank=True)

    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    referred_member = models.ForeignKey(
        MemberProfile, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='referred_by_referral'
    )

    # Rewards
    referrer_points = models.IntegerField(default=0)
    referred_points = models.IntegerField(default=0)
    qualification_purchase = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )

    # Tracking
    referral_link_clicks = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    registered_at = models.DateTimeField(null=True, blank=True)
    qualified_at = models.DateTimeField(null=True, blank=True)
    rewarded_at = models.DateTimeField(null=True, blank=True)


class BirthdayReward(models.Model):
    """Recompensas de cumpleaños de mascotas"""
    pet = models.ForeignKey('vet_clinic.Pet', on_delete=models.CASCADE)
    member = models.ForeignKey(MemberProfile, on_delete=models.CASCADE)
    year = models.IntegerField()

    reward = models.ForeignKey(
        RedeemedReward, on_delete=models.SET_NULL, null=True, blank=True
    )
    points_bonus = models.IntegerField(default=0)

    notified_at = models.DateTimeField(null=True, blank=True)
    claimed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['pet', 'year']


class SpecialPromotion(models.Model):
    """Promociones por tiempo limitado"""
    name = models.CharField(max_length=100)
    description = models.TextField()

    # Bonus points
    points_multiplier = models.DecimalField(max_digits=3, decimal_places=1, default=1.0)
    bonus_points = models.IntegerField(default=0)

    # Conditions
    min_purchase = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    service_types = models.JSONField(default=list)  # Empty = all
    product_categories = models.JSONField(default=list)

    # Validity
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    # Targeting
    tiers = models.ManyToManyField(LoyaltyTier, blank=True)  # Empty = all
    new_members_only = models.BooleanField(default=False)

    # Tracking
    times_used = models.IntegerField(default=0)
    max_uses = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
```

### Herramientas de IA

```python
LOYALTY_TOOLS = [
    {
        "name": "get_loyalty_status",
        "description": "Obtener estado del programa de lealtad del miembro",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"}
            }
        }
    },
    {
        "name": "get_points_balance",
        "description": "Obtener saldo de puntos e historial del miembro",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "include_history": {"type": "boolean", "default": False}
            }
        }
    },
    {
        "name": "get_available_rewards",
        "description": "Obtener recompensas disponibles para canjear",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "points_max": {"type": "integer"}
            }
        }
    },
    {
        "name": "redeem_reward",
        "description": "Canjear puntos por una recompensa",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"},
                "reward_id": {"type": "integer"}
            },
            "required": ["user_id", "reward_id"]
        }
    },
    {
        "name": "apply_reward_code",
        "description": "Aplicar una recompensa canjeada a una compra",
        "parameters": {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "order_id": {"type": "integer"}
            },
            "required": ["code"]
        }
    },
    {
        "name": "get_referral_link",
        "description": "Obtener enlace/código de referencia del miembro",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"}
            }
        }
    },
    {
        "name": "check_tier_progress",
        "description": "Verificar progreso al siguiente nivel",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {"type": "integer"}
            }
        }
    },
    {
        "name": "get_active_promotions",
        "description": "Obtener promociones actualmente activas",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
]
```

## Ejemplos de Conversaciones con IA

### Verificación de Saldo de Puntos
```
Dueño: ¿Cuántos puntos tengo?

IA: Aquí está tu estado de Recompensas Pet-Friendly, Maria:

    🏆 Miembro Plata

    💰 Saldo de Puntos: 1,250 puntos
    (Vale $125 MXN en descuentos)

    📊 Este Mes:
    • Ganados: 350 puntos
    • Canjeados: 0 puntos

    🎁 Puedes canjear por:
    • Corte de uñas gratis (500 pts)
    • Descuento de $100 (1,000 pts)
    • Baño y cepillado gratis (1,500 pts - necesitas 250 más)

    🎯 Progreso a Oro:
    ████████░░ 80%
    $2,000 más en gastos para llegar a nivel Oro

    ¿Te gustaría canjear puntos o ver todas las recompensas?
```

### Programa de Referencias
```
Dueño: ¿Cómo funciona el programa de referencias?

IA: ¡Excelente pregunta! Así es como puedes ganar recompensas
    al referir amigos:

    🎁 Recompensas por Referencia

    Tú Recibes: 500 puntos (valor $50)
    Ellos Reciben: 300 puntos de bienvenida + 10% de descuento en primera visita

    Cómo Funciona:
    1. Comparte tu enlace único o código: MARIA2025
    2. Amigo se registra y reserva primera cita
    3. ¡Después de su primera visita, ambos reciben recompensas!

    Tus Estadísticas de Referencias:
    • Amigos referidos: 3
    • Puntos ganados: 1,500
    • Referencias pendientes: 1 (esperando primera visita)

    Comparte tu enlace:
    petfriendlyvet.com/ref/MARIA2025

    [Copiar Enlace] [Compartir en WhatsApp] [Compartir en Facebook]
```

### Recompensa de Cumpleaños
```
IA (WhatsApp):
    🎂 ¡Feliz Cumpleaños, Luna! 🐕

    ¡Luna cumple 3 años hoy! Esperamos que tenga un día maravilloso.

    Como miembro Plata, aquí está el regalo de cumpleaños de Luna:

    🎁 Corte de Uñas GRATIS
    (Normalmente $150 MXN)

    Válido por los próximos 30 días.
    Usa el código: LUNA-BDAY-2025

    ¡Nos encantaría verla! Reserva una cita de peluquería
    y muestra ese brillo de cumpleaños.

    [Reservar Peluquería] [Guardar para Después]

    ¡Con amor de la familia Pet-Friendly! 💚
```

## Estructura de Niveles

| Nivel | Gasto Requerido | Multiplicador de Puntos | Ventajas |
|------|---------------|-------------------|-------|
| Bronce | $0 | 1x | Recompensas básicas |
| Plata | $5,000 | 1.25x | Reserva prioritaria, regalos de cumpleaños |
| Oro | $15,000 | 1.5x | Revisión anual gratis, 5% en todas las compras |
| Platino | $30,000 | 2x | Todo VIP, peluquería gratis mensual |

## Definición de Hecho

- [ ] Configuración del programa de lealtad
- [ ] Inscripción de miembros
- [ ] Ganancia de puntos en compras
- [ ] Actualización automática de nivel
- [ ] Catálogo de recompensas
- [ ] Canje de puntos
- [ ] Seguimiento de referencias
- [ ] Recompensas de cumpleaños
- [ ] Campañas promocionales
- [ ] Expiración de puntos
- [ ] Panel de miembros
- [ ] Pruebas escritas y aprobadas (>95% cobertura)

## Dependencias

- S-005: Comercio Electrónico (puntos en compras)
- S-007: CRM (perfiles de dueños)
- S-012: Notificaciones (notificaciones de recompensas)

## Notas

- Considerar elementos de gamificación (insignias, logros)
- Los puntos nunca deben expirar para miembros inactivos
- Considerar cuentas familiares (puntos compartidos entre mascotas)
- Integración con procesador de pagos para puntos automáticos
- Considerar paquetes prepagos (compra 5 revisiones, obtén 1 gratis)

## Proceso de Desarrollo

**Antes de implementar esta historia**, revisar y seguir el **Ciclo TDD de 23 Pasos** en:
- `CLAUDE.md` - Flujo de trabajo de desarrollo global
- `planning/TASK_BREAKDOWN.md` - Tareas específicas para esta historia

Las pruebas deben escribirse antes de la implementación. Se requiere >95% de cobertura.
