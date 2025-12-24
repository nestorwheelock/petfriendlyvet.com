"""Tests for Reviews and Testimonials app (TDD first)."""
import pytest
from django.utils import timezone

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


class TestReviewModel:
    """Tests for Review model."""

    def test_create_review(self, user):
        """Test creating a review."""
        from apps.reviews.models import Review

        review = Review.objects.create(
            user=user,
            rating=5,
            title='Excellent Service',
            content='Dr. Pablo took great care of my dog.',
            status='approved',
        )

        assert review.rating == 5
        assert review.status == 'approved'

    def test_review_str(self, user):
        """Test string representation."""
        from apps.reviews.models import Review

        review = Review.objects.create(
            user=user,
            rating=4,
            content='Good experience.',
        )

        assert '4 stars' in str(review)

    def test_review_author_property(self, user):
        """Test author property."""
        from apps.reviews.models import Review

        # With user
        review1 = Review.objects.create(
            user=user,
            rating=5,
            content='Great!',
        )
        assert review1.author == user.get_full_name() or user.email

        # With author_name
        review2 = Review.objects.create(
            author_name='John Doe',
            rating=5,
            content='Wonderful!',
        )
        assert review2.author == 'John Doe'

    def test_review_platforms(self):
        """Test different review platforms."""
        from apps.reviews.models import Review

        platforms = ['internal', 'google', 'facebook', 'yelp']
        for platform in platforms:
            review = Review.objects.create(
                rating=5,
                content='Test review',
                platform=platform,
            )
            assert review.platform == platform

    def test_featured_review(self, user):
        """Test featured review status."""
        from apps.reviews.models import Review

        review = Review.objects.create(
            user=user,
            rating=5,
            content='Amazing!',
            status='featured',
            display_on_homepage=True,
        )

        assert review.status == 'featured'
        assert review.display_on_homepage is True


class TestReviewRequestModel:
    """Tests for ReviewRequest model."""

    def test_create_review_request(self, user):
        """Test creating a review request."""
        from apps.reviews.models import ReviewRequest

        request = ReviewRequest.objects.create(
            user=user,
            service_description='Annual checkup',
        )

        assert request.user == user
        assert request.token is not None
        assert len(request.token) > 20

    def test_review_request_auto_token(self, user):
        """Test token is auto-generated."""
        from apps.reviews.models import ReviewRequest

        request = ReviewRequest.objects.create(user=user)

        assert request.token != ''


class TestTestimonialModel:
    """Tests for Testimonial model."""

    def test_create_testimonial(self):
        """Test creating a testimonial."""
        from apps.reviews.models import Testimonial

        testimonial = Testimonial.objects.create(
            author_name='Maria Garcia',
            author_title='Pet Owner',
            quote='The best veterinary clinic in Puerto Morelos!',
            short_quote='The best vet clinic!',
            show_on_homepage=True,
        )

        assert testimonial.author_name == 'Maria Garcia'
        assert testimonial.show_on_homepage is True

    def test_testimonial_from_review(self, user):
        """Test creating testimonial from review."""
        from apps.reviews.models import Review, Testimonial

        review = Review.objects.create(
            user=user,
            rating=5,
            content='Exceptional care for my pets!',
            status='featured',
        )

        testimonial = Testimonial.objects.create(
            review=review,
            author_name=user.get_full_name(),
            quote=review.content,
            is_active=True,
        )

        assert testimonial.review == review
        assert testimonial.quote == review.content


class TestReviewAITools:
    """Tests for Review AI tools."""

    def test_get_reviews_tool_exists(self):
        """Test get_reviews tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('get_reviews')
        assert tool is not None

    def test_get_reviews(self, user):
        """Test getting reviews."""
        from apps.ai_assistant.tools import get_reviews
        from apps.reviews.models import Review

        Review.objects.create(
            user=user,
            rating=5,
            content='Great!',
            status='approved',
        )

        result = get_reviews()

        assert result['success'] is True
        assert result['count'] >= 1

    def test_submit_review_tool_exists(self):
        """Test submit_review tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('submit_review')
        assert tool is not None

    def test_submit_review(self, user):
        """Test submitting a review."""
        from apps.ai_assistant.tools import submit_review

        result = submit_review(
            user_id=user.id,
            rating=5,
            content='Excellent service!',
            title='Great experience',
        )

        assert result['success'] is True
        assert 'review_id' in result

    def test_request_review_tool_exists(self):
        """Test request_review tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('request_review')
        assert tool is not None

    def test_request_review(self, user):
        """Test requesting a review from customer."""
        from apps.ai_assistant.tools import request_review

        result = request_review(
            user_id=user.id,
            service_description='Vaccination appointment',
        )

        assert result['success'] is True
        assert 'request_id' in result

    def test_get_testimonials_tool_exists(self):
        """Test get_testimonials tool is registered."""
        from apps.ai_assistant.tools import ToolRegistry

        tool = ToolRegistry.get_tool('get_testimonials')
        assert tool is not None

    def test_get_testimonials(self):
        """Test getting testimonials."""
        from apps.ai_assistant.tools import get_testimonials
        from apps.reviews.models import Testimonial

        Testimonial.objects.create(
            author_name='Test User',
            quote='Great clinic!',
            is_active=True,
        )

        result = get_testimonials()

        assert result['success'] is True
        assert result['count'] >= 1


class TestReviewIntegration:
    """Integration tests for reviews."""

    def test_review_to_testimonial_workflow(self, user):
        """Test converting review to testimonial."""
        from apps.reviews.models import Review, Testimonial

        # Create review
        review = Review.objects.create(
            user=user,
            rating=5,
            title='Highly Recommend',
            content='Dr. Pablo is the best! My dog loves going there.',
            status='approved',
        )

        # Feature it
        review.status = 'featured'
        review.display_on_homepage = True
        review.save()

        # Create testimonial
        testimonial = Testimonial.objects.create(
            review=review,
            author_name=review.author,
            quote=review.content,
            short_quote='Dr. Pablo is the best!',
            show_on_homepage=True,
        )

        assert testimonial.review == review
        assert testimonial.show_on_homepage is True


# Fixtures
@pytest.fixture
def user():
    """Create a test user."""
    return User.objects.create_user(
        username='reviewuser',
        email='review@example.com',
        password='testpass123',
        first_name='Review',
        last_name='User',
    )
