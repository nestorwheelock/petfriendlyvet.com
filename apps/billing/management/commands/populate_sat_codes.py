"""Management command to populate SAT codes for Mexican tax compliance."""
from django.core.management.base import BaseCommand

from apps.billing.models import SATProductCode, SATUnitCode


class Command(BaseCommand):
    """Populate SAT product and unit codes for CFDI compliance."""

    help = 'Populate SAT product codes (clave producto) and unit codes (clave unidad)'

    def handle(self, *args, **options):
        """Execute the command."""
        product_count = self._populate_product_codes()
        unit_count = self._populate_unit_codes()

        self.stdout.write(
            self.style.SUCCESS(
                f'Created {product_count} product codes and {unit_count} unit codes'
            )
        )

    def _populate_product_codes(self) -> int:
        """Populate SAT product codes (clave producto/servicio)."""
        codes = [
            # Healthcare & Veterinary Services
            ('85121800', 'Servicios de atención de salud', False, False, False, False),
            ('85121801', 'Servicios de consulta médica', False, False, False, False),
            ('85121802', 'Servicios de tratamiento médico', False, False, False, False),
            ('85121803', 'Servicios quirúrgicos', False, False, False, False),
            ('85121804', 'Servicios de diagnóstico por imagen', False, False, False, False),
            ('85121805', 'Servicios de laboratorio clínico', False, False, False, False),
            ('85121806', 'Servicios de urgencias médicas', False, False, False, False),
            ('85121899', 'Otros servicios de salud', False, False, False, False),

            # Veterinary Equipment & Supplies
            ('42201700', 'Equipo veterinario', False, False, False, False),
            ('42201800', 'Instrumentos veterinarios', False, False, False, False),
            ('42201900', 'Suministros veterinarios', False, False, False, False),

            # Pet Food & Nutrition
            ('10101500', 'Alimentos para animales', False, False, False, False),
            ('10101501', 'Alimento para perros', False, False, False, False),
            ('10101502', 'Alimento para gatos', False, False, False, False),
            ('10101503', 'Alimento para aves', False, False, False, False),
            ('10101504', 'Alimento para peces', False, False, False, False),
            ('10101505', 'Alimento para roedores', False, False, False, False),
            ('10101599', 'Otros alimentos para mascotas', False, False, False, False),

            # Pharmaceuticals & Medications
            ('51101500', 'Medicamentos veterinarios', False, False, False, False),
            ('51101501', 'Vacunas veterinarias', False, False, False, False),
            ('51101502', 'Antibióticos veterinarios', False, False, False, False),
            ('51101503', 'Antiparasitarios veterinarios', False, False, False, False),
            ('51101504', 'Analgésicos veterinarios', False, False, False, False),
            ('51101505', 'Anestésicos veterinarios', False, False, False, False),
            ('51101506', 'Suplementos veterinarios', False, False, False, False),

            # Pet Accessories & Products
            ('49101600', 'Productos para mascotas', False, False, False, False),
            ('49101601', 'Collares y correas', False, False, False, False),
            ('49101602', 'Camas para mascotas', False, False, False, False),
            ('49101603', 'Juguetes para mascotas', False, False, False, False),
            ('49101604', 'Transportadoras', False, False, False, False),
            ('49101605', 'Platos y comederos', False, False, False, False),

            # Hygiene & Grooming
            ('53131600', 'Productos de higiene para mascotas', False, False, False, False),
            ('53131601', 'Shampoo para mascotas', False, False, False, False),
            ('53131602', 'Cepillos y peines', False, False, False, False),
            ('53131603', 'Cortauñas para mascotas', False, False, False, False),

            # General Merchandise
            ('43231500', 'Mercancía general', False, False, False, False),

            # Delivery & Shipping
            ('78102200', 'Servicios de entrega', False, False, False, False),
            ('78102201', 'Envío local', False, False, False, False),
            ('78102202', 'Envío nacional', False, False, False, False),

            # Professional Services
            ('80111600', 'Servicios profesionales', False, False, False, False),
            ('80111601', 'Consultoría profesional', False, False, False, False),
            ('80111602', 'Servicios de capacitación', False, False, False, False),
        ]

        created = 0
        for code, desc, inc_iva, iva_ex, iva_zero, ieps in codes:
            _, was_created = SATProductCode.objects.get_or_create(
                code=code,
                defaults={
                    'description': desc,
                    'includes_iva': inc_iva,
                    'iva_exempt': iva_ex,
                    'iva_zero_rate': iva_zero,
                    'ieps_applicable': ieps,
                }
            )
            if was_created:
                created += 1

        return created

    def _populate_unit_codes(self) -> int:
        """Populate SAT unit codes (clave unidad)."""
        codes = [
            # Common units
            ('H87', 'Pieza', 'Unidad individual'),
            ('E48', 'Unidad de servicio', 'Para servicios'),
            ('ACT', 'Actividad', 'Para servicios o actividades'),

            # Weight
            ('KGM', 'Kilogramo', 'Peso en kilogramos'),
            ('GRM', 'Gramo', 'Peso en gramos'),
            ('LBR', 'Libra', 'Peso en libras'),
            ('ONZ', 'Onza', 'Peso en onzas'),

            # Volume
            ('LTR', 'Litro', 'Volumen en litros'),
            ('MLT', 'Mililitro', 'Volumen en mililitros'),
            ('GLL', 'Galón', 'Volumen en galones'),

            # Length
            ('MTR', 'Metro', 'Longitud en metros'),
            ('CMT', 'Centímetro', 'Longitud en centímetros'),

            # Time
            ('HUR', 'Hora', 'Tiempo en horas'),
            ('DAY', 'Día', 'Tiempo en días'),
            ('MON', 'Mes', 'Tiempo en meses'),
            ('ANN', 'Año', 'Tiempo en años'),
            ('MIN', 'Minuto', 'Tiempo en minutos'),

            # Packaging
            ('XBX', 'Caja', 'Caja o empaque'),
            ('XPK', 'Paquete', 'Paquete o bulto'),
            ('XBG', 'Bolsa', 'Bolsa'),
            ('XBT', 'Botella', 'Botella'),
            ('XTU', 'Tubo', 'Tubo'),

            # Sets
            ('SET', 'Juego', 'Conjunto o kit'),
            ('PR', 'Par', 'Par de artículos'),
        ]

        created = 0
        for code, name, desc in codes:
            _, was_created = SATUnitCode.objects.get_or_create(
                code=code,
                defaults={
                    'name': name,
                    'description': desc,
                }
            )
            if was_created:
                created += 1

        return created
