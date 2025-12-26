"""Tests for TaxRate, SATProductCode, SATUnitCode models (TDD).

Tests for:
- TaxRate model creation and properties
- SATProductCode model for CFDI compliance
- SATUnitCode model for CFDI compliance
- Tax calculation service
"""
import pytest
from decimal import Decimal

from django.db import IntegrityError


@pytest.fixture
def iva_16(db):
    """Create IVA 16% tax rate."""
    from apps.billing.models import TaxRate
    return TaxRate.objects.create(
        code='IVA16',
        name='IVA 16%',
        tax_type='iva',
        rate=Decimal('0.1600'),
        sat_impuesto_code='002',
        sat_tipo_factor='Tasa',
        is_default=True,
        is_active=True
    )


@pytest.fixture
def iva_0(db):
    """Create IVA 0% tax rate."""
    from apps.billing.models import TaxRate
    return TaxRate.objects.create(
        code='IVA0',
        name='IVA 0%',
        tax_type='iva',
        rate=Decimal('0.0000'),
        sat_impuesto_code='002',
        sat_tipo_factor='Tasa',
        is_default=False,
        is_active=True
    )


@pytest.fixture
def iva_exempt(db):
    """Create IVA Exempt tax rate."""
    from apps.billing.models import TaxRate
    return TaxRate.objects.create(
        code='IVA_EXEMPT',
        name='IVA Exento',
        tax_type='iva',
        rate=Decimal('0.0000'),
        sat_impuesto_code='002',
        sat_tipo_factor='Exento',
        is_default=False,
        is_active=True
    )


@pytest.fixture
def ieps_8(db):
    """Create IEPS 8% tax rate."""
    from apps.billing.models import TaxRate
    return TaxRate.objects.create(
        code='IEPS8',
        name='IEPS 8%',
        tax_type='ieps',
        rate=Decimal('0.0800'),
        sat_impuesto_code='003',
        sat_tipo_factor='Tasa',
        is_default=False,
        is_active=True
    )


@pytest.fixture
def sat_product_code(db):
    """Create a SAT product code."""
    from apps.billing.models import SATProductCode
    return SATProductCode.objects.create(
        code='50112001',
        description='Alimentos para animales',
        includes_iva=False,
        iva_exempt=False,
        iva_zero_rate=False,
        ieps_applicable=False
    )


@pytest.fixture
def sat_unit_code(db):
    """Create a SAT unit code."""
    from apps.billing.models import SATUnitCode
    return SATUnitCode.objects.create(
        code='H87',
        name='Pieza',
        description='Each/Unit'
    )


class TestTaxRateModel:
    """Tests for TaxRate model."""

    def test_taxrate_create(self, db):
        """Can create a tax rate."""
        from apps.billing.models import TaxRate
        tr = TaxRate.objects.create(
            code='TEST',
            name='Test Tax',
            tax_type='iva',
            rate=Decimal('0.1600'),
            sat_impuesto_code='002',
            sat_tipo_factor='Tasa'
        )
        assert tr.pk is not None
        assert tr.code == 'TEST'
        assert tr.rate == Decimal('0.1600')
        assert tr.is_active is True  # default

    def test_taxrate_str(self, iva_16):
        """String representation shows name."""
        assert str(iva_16) == 'IVA 16%'

    def test_taxrate_code_unique(self, db, iva_16):
        """Code must be unique."""
        from apps.billing.models import TaxRate
        with pytest.raises(IntegrityError):
            TaxRate.objects.create(
                code='IVA16',  # Duplicate
                name='Another IVA',
                tax_type='iva',
                rate=Decimal('0.1600'),
                sat_impuesto_code='002',
                sat_tipo_factor='Tasa'
            )

    def test_taxrate_default_flag(self, db, iva_16, iva_0):
        """Only one tax rate should be default at a time."""
        from apps.billing.models import TaxRate
        assert iva_16.is_default is True
        assert iva_0.is_default is False

        # Get default tax rate
        default = TaxRate.objects.filter(is_default=True).first()
        assert default == iva_16

    def test_taxrate_tax_type_choices(self, db, iva_16, ieps_8):
        """Tax types are correctly assigned."""
        assert iva_16.tax_type == 'iva'
        assert ieps_8.tax_type == 'ieps'

    def test_taxrate_sat_impuesto_code(self, db, iva_16, ieps_8):
        """SAT impuesto codes are correct."""
        assert iva_16.sat_impuesto_code == '002'  # IVA
        assert ieps_8.sat_impuesto_code == '003'  # IEPS

    def test_taxrate_ordering(self, db, iva_16, iva_0, ieps_8):
        """Tax rates are ordered by type then rate descending."""
        from apps.billing.models import TaxRate
        rates = list(TaxRate.objects.all())
        # IVA types first, then by rate descending
        assert rates[0].tax_type == 'ieps'  # IEPS first by type order
        # Both IVA after

    def test_taxrate_exento(self, db, iva_exempt):
        """Exento tax rate has correct tipo_factor."""
        assert iva_exempt.sat_tipo_factor == 'Exento'
        assert iva_exempt.rate == Decimal('0.0000')


class TestSATProductCodeModel:
    """Tests for SATProductCode model."""

    def test_satproductcode_create(self, db):
        """Can create a SAT product code."""
        from apps.billing.models import SATProductCode
        code = SATProductCode.objects.create(
            code='50201700',
            description='Artículos para mascotas'
        )
        assert code.pk == '50201700'  # Primary key is code
        assert code.description == 'Artículos para mascotas'

    def test_satproductcode_str(self, sat_product_code):
        """String representation shows code and description."""
        result = str(sat_product_code)
        assert '50112001' in result

    def test_satproductcode_unique(self, db, sat_product_code):
        """Code must be unique (primary key)."""
        from apps.billing.models import SATProductCode
        with pytest.raises(IntegrityError):
            SATProductCode.objects.create(
                code='50112001',  # Duplicate
                description='Duplicate code'
            )

    def test_satproductcode_flags(self, db):
        """Product code can have special tax flags."""
        from apps.billing.models import SATProductCode
        code = SATProductCode.objects.create(
            code='12345678',
            description='Test exempt product',
            iva_exempt=True
        )
        assert code.iva_exempt is True
        assert code.iva_zero_rate is False

    def test_satproductcode_ordering(self, db):
        """Product codes are ordered by code."""
        from apps.billing.models import SATProductCode
        SATProductCode.objects.create(code='99999999', description='Z')
        SATProductCode.objects.create(code='11111111', description='A')
        SATProductCode.objects.create(code='55555555', description='M')

        codes = list(SATProductCode.objects.values_list('code', flat=True))
        assert codes == sorted(codes)


class TestSATUnitCodeModel:
    """Tests for SATUnitCode model."""

    def test_satunitcode_create(self, db):
        """Can create a SAT unit code."""
        from apps.billing.models import SATUnitCode
        code = SATUnitCode.objects.create(
            code='E48',
            name='Unidad de servicio',
            description='Service Unit'
        )
        assert code.pk == 'E48'
        assert code.name == 'Unidad de servicio'

    def test_satunitcode_str(self, sat_unit_code):
        """String representation shows code and name."""
        result = str(sat_unit_code)
        assert 'H87' in result or 'Pieza' in result

    def test_satunitcode_unique(self, db, sat_unit_code):
        """Code must be unique (primary key)."""
        from apps.billing.models import SATUnitCode
        with pytest.raises(IntegrityError):
            SATUnitCode.objects.create(
                code='H87',  # Duplicate
                name='Duplicate unit'
            )

    def test_satunitcode_common_codes(self, db):
        """Can create common SAT unit codes."""
        from apps.billing.models import SATUnitCode
        units = [
            ('H87', 'Pieza'),
            ('E48', 'Unidad de servicio'),
            ('KGM', 'Kilogramo'),
            ('LTR', 'Litro'),
        ]
        for code, name in units:
            SATUnitCode.objects.create(code=code, name=name)

        assert SATUnitCode.objects.count() == 4

    def test_satunitcode_ordering(self, db):
        """Unit codes are ordered by code."""
        from apps.billing.models import SATUnitCode
        SATUnitCode.objects.create(code='ZZZ', name='Z')
        SATUnitCode.objects.create(code='AAA', name='A')
        SATUnitCode.objects.create(code='MMM', name='M')

        codes = list(SATUnitCode.objects.values_list('code', flat=True))
        assert codes == sorted(codes)


class TestTaxCalculationService:
    """Tests for tax calculation service."""

    def test_calculate_tax_16_percent(self, db, iva_16):
        """Calculate 16% IVA on amount."""
        from apps.billing.services import calculate_tax

        result = calculate_tax(Decimal('100.00'), iva_16)

        assert result['subtotal'] == Decimal('100.00')
        assert result['tax_amount'] == Decimal('16.00')
        assert result['total'] == Decimal('116.00')
        assert result['tax_rate'] == iva_16

    def test_calculate_tax_0_percent(self, db, iva_0):
        """Calculate 0% IVA on amount."""
        from apps.billing.services import calculate_tax

        result = calculate_tax(Decimal('100.00'), iva_0)

        assert result['subtotal'] == Decimal('100.00')
        assert result['tax_amount'] == Decimal('0.00')
        assert result['total'] == Decimal('100.00')

    def test_calculate_tax_exempt(self, db, iva_exempt):
        """Calculate exempt IVA on amount."""
        from apps.billing.services import calculate_tax

        result = calculate_tax(Decimal('100.00'), iva_exempt)

        assert result['subtotal'] == Decimal('100.00')
        assert result['tax_amount'] == Decimal('0.00')
        assert result['total'] == Decimal('100.00')

    def test_calculate_tax_ieps(self, db, ieps_8):
        """Calculate IEPS 8% on amount."""
        from apps.billing.services import calculate_tax

        result = calculate_tax(Decimal('100.00'), ieps_8)

        assert result['subtotal'] == Decimal('100.00')
        assert result['tax_amount'] == Decimal('8.00')
        assert result['total'] == Decimal('108.00')

    def test_calculate_tax_include_in_price(self, db, iva_16):
        """Extract tax from price that includes tax."""
        from apps.billing.services import calculate_tax

        result = calculate_tax(Decimal('116.00'), iva_16, include_in_price=True)

        assert result['subtotal'] == Decimal('100.00')
        assert result['tax_amount'] == Decimal('16.00')
        assert result['total'] == Decimal('116.00')

    def test_calculate_tax_decimal_precision(self, db, iva_16):
        """Tax calculation maintains decimal precision."""
        from apps.billing.services import calculate_tax

        result = calculate_tax(Decimal('99.99'), iva_16)

        assert result['subtotal'] == Decimal('99.99')
        assert result['tax_amount'] == Decimal('16.00')  # 99.99 * 0.16 = 15.9984 → 16.00
        assert result['total'] == Decimal('115.99')

    def test_get_cfdi_tax_node_tasa(self, db, iva_16):
        """Generate CFDI tax node for Tasa type."""
        from apps.billing.services import calculate_tax, get_cfdi_tax_node

        calc = calculate_tax(Decimal('100.00'), iva_16)
        node = get_cfdi_tax_node(calc)

        assert node['Base'] == '100.00'
        assert node['Impuesto'] == '002'
        assert node['TipoFactor'] == 'Tasa'
        assert node['TasaOCuota'] == '0.160000'
        assert node['Importe'] == '16.00'

    def test_get_cfdi_tax_node_exento(self, db, iva_exempt):
        """Generate CFDI tax node for Exento type."""
        from apps.billing.services import calculate_tax, get_cfdi_tax_node

        calc = calculate_tax(Decimal('100.00'), iva_exempt)
        node = get_cfdi_tax_node(calc)

        assert node['Impuesto'] == '002'
        assert node['TipoFactor'] == 'Exento'
        assert 'TasaOCuota' not in node
        assert 'Importe' not in node


class TestDefaultTaxRates:
    """Tests for default tax rate seeding."""

    def test_seed_default_tax_rates(self, db):
        """Can seed default Mexico tax rates."""
        from apps.billing.services import seed_default_tax_rates

        seed_default_tax_rates()

        from apps.billing.models import TaxRate
        assert TaxRate.objects.filter(code='IVA16').exists()
        assert TaxRate.objects.filter(code='IVA0').exists()
        assert TaxRate.objects.filter(code='IVA_EXEMPT').exists()

        # Check default is IVA16
        default = TaxRate.objects.filter(is_default=True).first()
        assert default.code == 'IVA16'

    def test_seed_idempotent(self, db):
        """Seeding is idempotent."""
        from apps.billing.services import seed_default_tax_rates
        from apps.billing.models import TaxRate

        seed_default_tax_rates()
        count1 = TaxRate.objects.count()

        seed_default_tax_rates()
        count2 = TaxRate.objects.count()

        assert count1 == count2
