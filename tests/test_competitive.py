"""Tests for Competitive Intelligence app (TDD first)."""
import pytest
from datetime import datetime, timedelta
from django.utils import timezone
from decimal import Decimal

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


class TestCompetitorModel:
    """Tests for Competitor model."""

    def test_create_competitor(self):
        """Test creating a competitor."""
        from apps.competitive.models import Competitor

        competitor = Competitor.objects.create(
            name='Fauna Silvestre',
            address='Puerto Morelos, QR',
            phone='+52 998 231 9402',
            website='https://faunasilvestre.com',
            is_active=True,
        )

        assert competitor.name == 'Fauna Silvestre'
        assert competitor.is_active is True

    def test_competitor_str(self):
        """Test string representation."""
        from apps.competitive.models import Competitor

        competitor = Competitor.objects.create(
            name='La Vet del Puerto',
        )

        assert 'La Vet del Puerto' in str(competitor)

    def test_competitor_with_location(self):
        """Test competitor with GPS coordinates."""
        from apps.competitive.models import Competitor

        competitor = Competitor.objects.create(
            name='Miramar Vet',
            latitude=20.8654,
            longitude=-86.8756,
            distance_km=2.5,
        )

        assert competitor.latitude is not None
        assert competitor.distance_km == 2.5


class TestCompetitorServiceModel:
    """Tests for CompetitorService model."""

    def test_create_service(self):
        """Test creating a competitor service."""
        from apps.competitive.models import Competitor, CompetitorService

        competitor = Competitor.objects.create(name='Test Vet')

        service = CompetitorService.objects.create(
            competitor=competitor,
            name='General Checkup',
            price=Decimal('500.00'),
            currency='MXN',
        )

        assert service.name == 'General Checkup'
        assert service.price == Decimal('500.00')

    def test_price_tracking(self):
        """Test updating service price creates history."""
        from apps.competitive.models import Competitor, CompetitorService

        competitor = Competitor.objects.create(name='Test Vet')

        service = CompetitorService.objects.create(
            competitor=competitor,
            name='Vaccination',
            price=Decimal('350.00'),
            previous_price=Decimal('300.00'),
        )

        assert service.price == Decimal('350.00')
        assert service.previous_price == Decimal('300.00')


class TestCompetitorReviewModel:
    """Tests for CompetitorReview model."""

    def test_create_review(self):
        """Test creating a competitor review record."""
        from apps.competitive.models import Competitor, CompetitorReview

        competitor = Competitor.objects.create(name='Test Vet')

        review = CompetitorReview.objects.create(
            competitor=competitor,
            platform='google',
            rating=4.5,
            review_count=67,
            sample_review='Great service!',
        )

        assert review.platform == 'google'
        assert review.rating == 4.5
        assert review.review_count == 67


class TestMarketTrendModel:
    """Tests for MarketTrend model."""

    def test_create_trend(self):
        """Test creating a market trend."""
        from apps.competitive.models import MarketTrend

        trend = MarketTrend.objects.create(
            category='pricing',
            title='Competitors raising prices',
            description='Most competitors increased vaccination prices by 10%',
            impact_level='medium',
            source='Manual observation',
        )

        assert trend.category == 'pricing'
        assert trend.impact_level == 'medium'


class TestCompetitiveAITools:
    """Tests for Competitive Intelligence AI tools."""

    def test_get_competitors_tool_exists(self):
        """Test get_competitors tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('get_competitors')
        assert tool is not None

    def test_get_competitors(self):
        """Test getting competitor list."""
        from apps.ai_assistant.tools import get_competitors
        from apps.competitive.models import Competitor

        Competitor.objects.create(name='Vet A', is_active=True)
        Competitor.objects.create(name='Vet B', is_active=True)

        result = get_competitors()

        assert result['success'] is True
        assert result['count'] >= 2

    def test_get_competitor_prices_tool_exists(self):
        """Test get_competitor_prices tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('get_competitor_prices')
        assert tool is not None

    def test_get_competitor_prices(self):
        """Test getting competitor prices."""
        from apps.ai_assistant.tools import get_competitor_prices
        from apps.competitive.models import Competitor, CompetitorService

        competitor = Competitor.objects.create(name='Test Vet')
        CompetitorService.objects.create(
            competitor=competitor,
            name='Checkup',
            price=Decimal('450.00'),
        )

        result = get_competitor_prices(service_name='Checkup')

        assert result['success'] is True
        assert 'prices' in result

    def test_add_competitor_tool_exists(self):
        """Test add_competitor tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('add_competitor')
        assert tool is not None

    def test_add_competitor(self):
        """Test adding a new competitor."""
        from apps.ai_assistant.tools import add_competitor

        result = add_competitor(
            name='New Competitor',
            address='123 Test St',
            phone='+52 999 123 4567',
        )

        assert result['success'] is True
        assert 'competitor_id' in result

    def test_update_competitor_price_tool_exists(self):
        """Test update_competitor_price tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('update_competitor_price')
        assert tool is not None

    def test_update_competitor_price(self):
        """Test updating a competitor's service price."""
        from apps.ai_assistant.tools import update_competitor_price
        from apps.competitive.models import Competitor, CompetitorService

        competitor = Competitor.objects.create(name='Test Vet')
        service = CompetitorService.objects.create(
            competitor=competitor,
            name='Surgery',
            price=Decimal('2000.00'),
        )

        result = update_competitor_price(
            competitor_id=competitor.id,
            service_name='Surgery',
            new_price=2200.00,
        )

        assert result['success'] is True

    def test_get_market_position_tool_exists(self):
        """Test get_market_position tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('get_market_position')
        assert tool is not None

    def test_get_market_position(self):
        """Test getting market position analysis."""
        from apps.ai_assistant.tools import get_market_position
        from apps.competitive.models import Competitor, CompetitorReview

        competitor = Competitor.objects.create(name='Test Vet')
        CompetitorReview.objects.create(
            competitor=competitor,
            platform='google',
            rating=4.2,
            review_count=50,
        )

        result = get_market_position()

        assert result['success'] is True


class TestCompetitiveIntegration:
    """Integration tests for competitive intelligence."""

    def test_full_competitor_tracking(self):
        """Test complete competitor tracking workflow."""
        from apps.competitive.models import (
            Competitor, CompetitorService, CompetitorReview
        )
        from apps.ai_assistant.tools import (
            add_competitor, get_competitors, update_competitor_price
        )

        # Add competitor
        result = add_competitor(
            name='Puerto Morelos Vet',
            address='Centro, Puerto Morelos',
            phone='+52 998 555 1234',
        )
        assert result['success'] is True

        # Add service
        competitor = Competitor.objects.get(name='Puerto Morelos Vet')
        CompetitorService.objects.create(
            competitor=competitor,
            name='Vaccination',
            price=Decimal('380.00'),
        )

        # Add review
        CompetitorReview.objects.create(
            competitor=competitor,
            platform='google',
            rating=4.3,
            review_count=45,
        )

        # Get competitors
        result = get_competitors()
        assert result['count'] >= 1

        # Update price
        result = update_competitor_price(
            competitor_id=competitor.id,
            service_name='Vaccination',
            new_price=400.00,
        )
        assert result['success'] is True
