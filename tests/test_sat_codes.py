"""Tests for SAT code population management command."""
import pytest
from django.core.management import call_command
from io import StringIO

from apps.billing.models import SATProductCode, SATUnitCode


@pytest.mark.django_db
class TestPopulateSATCodesCommand:
    """Test the populate_sat_codes management command."""

    def test_command_creates_product_codes(self):
        """Command should populate SAT product codes."""
        # Verify empty before
        assert SATProductCode.objects.count() == 0

        # Run command
        out = StringIO()
        call_command('populate_sat_codes', stdout=out)

        # Should have product codes now
        assert SATProductCode.objects.count() > 0
        output = out.getvalue()
        assert 'product codes' in output.lower()

    def test_command_creates_unit_codes(self):
        """Command should populate SAT unit codes."""
        # Verify empty before
        assert SATUnitCode.objects.count() == 0

        # Run command
        out = StringIO()
        call_command('populate_sat_codes', stdout=out)

        # Should have unit codes now
        assert SATUnitCode.objects.count() > 0
        output = out.getvalue()
        assert 'unit codes' in output.lower()

    def test_product_code_has_required_fields(self):
        """Product codes should have code and description."""
        call_command('populate_sat_codes')

        code = SATProductCode.objects.first()
        assert code is not None
        assert code.code  # Not empty
        assert code.description  # Not empty
        assert len(code.code) <= 8  # SAT codes are max 8 digits

    def test_unit_code_has_required_fields(self):
        """Unit codes should have code and name."""
        call_command('populate_sat_codes')

        code = SATUnitCode.objects.first()
        assert code is not None
        assert code.code  # Not empty
        assert code.name  # Not empty

    def test_command_is_idempotent(self):
        """Running command twice should not duplicate codes."""
        call_command('populate_sat_codes')
        first_product_count = SATProductCode.objects.count()
        first_unit_count = SATUnitCode.objects.count()

        # Run again
        call_command('populate_sat_codes')
        second_product_count = SATProductCode.objects.count()
        second_unit_count = SATUnitCode.objects.count()

        # Counts should be the same
        assert first_product_count == second_product_count
        assert first_unit_count == second_unit_count

    def test_veterinary_product_code_exists(self):
        """Should include veterinary services code 85121800."""
        call_command('populate_sat_codes')

        # 85121800 is the SAT code for veterinary services
        assert SATProductCode.objects.filter(code='85121800').exists()

    def test_piece_unit_code_exists(self):
        """Should include H87 (piece) unit code."""
        call_command('populate_sat_codes')

        # H87 is the SAT code for "piece" (pieza)
        assert SATUnitCode.objects.filter(code='H87').exists()

    def test_service_unit_code_exists(self):
        """Should include E48 (unit of service) code."""
        call_command('populate_sat_codes')

        # E48 is the SAT code for unit of service
        assert SATUnitCode.objects.filter(code='E48').exists()

    def test_minimum_product_codes_count(self):
        """Should create at least 20 product codes for common use cases."""
        call_command('populate_sat_codes')
        assert SATProductCode.objects.count() >= 20

    def test_minimum_unit_codes_count(self):
        """Should create at least 10 unit codes for common use cases."""
        call_command('populate_sat_codes')
        assert SATUnitCode.objects.count() >= 10
