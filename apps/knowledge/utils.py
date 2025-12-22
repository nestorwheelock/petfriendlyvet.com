"""Utility functions for knowledge base."""
from django.db.models import Q

from .models import KnowledgeArticle, FAQ


def search_knowledge_base(query: str, language: str = 'es') -> list:
    """Search across knowledge base articles.

    Args:
        query: Search query string
        language: Language code ('es' or 'en')

    Returns:
        List of matching KnowledgeArticle objects
    """
    if not query:
        return []

    # Build search across title, content, and keywords
    title_field = f'title_{language}'
    content_field = f'content_{language}'

    filters = (
        Q(**{f'{title_field}__icontains': query}) |
        Q(**{f'{content_field}__icontains': query}) |
        Q(keywords__icontains=query) |
        Q(ai_context__icontains=query)
    )

    return list(
        KnowledgeArticle.objects.filter(
            filters,
            is_published=True
        ).order_by('-priority')
    )


def get_ai_context(keywords: list, language: str = 'es', max_items: int = 5) -> str:
    """Get AI context string from knowledge base.

    Args:
        keywords: List of keywords to search for
        language: Language code ('es' or 'en')
        max_items: Maximum number of items to include

    Returns:
        Formatted context string for AI injection
    """
    if not keywords:
        return ''

    context_parts = []

    # Search for relevant articles
    title_field = f'title_{language}'
    content_field = f'content_{language}'

    for keyword in keywords:
        articles = KnowledgeArticle.objects.filter(
            Q(**{f'{title_field}__icontains': keyword}) |
            Q(keywords__icontains=keyword) |
            Q(ai_context__icontains=keyword),
            is_published=True
        ).order_by('-priority')[:max_items]

        for article in articles:
            if article.ai_context:
                context_parts.append(article.ai_context)
            else:
                # Use truncated content if no ai_context
                content = article.get_content(language)
                context_parts.append(content[:500] if len(content) > 500 else content)

    # Search for relevant FAQs
    for keyword in keywords:
        faqs = FAQ.objects.filter(
            Q(**{f'question_{language}__icontains': keyword}) |
            Q(**{f'answer_{language}__icontains': keyword}),
            is_active=True
        ).order_by('-is_featured', 'order')[:max_items]

        for faq in faqs:
            q = faq.get_question(language)
            a = faq.get_answer(language)
            context_parts.append(f'Q: {q}\nA: {a}')

    # Deduplicate and join
    seen = set()
    unique_parts = []
    for part in context_parts:
        if part not in seen:
            seen.add(part)
            unique_parts.append(part)
            if len(unique_parts) >= max_items:
                break

    return '\n\n'.join(unique_parts)


def get_featured_faqs(language: str = 'es', limit: int = 10) -> list:
    """Get featured FAQs for display.

    Args:
        language: Language code
        limit: Maximum number to return

    Returns:
        List of FAQ objects
    """
    return list(
        FAQ.objects.filter(
            is_featured=True,
            is_active=True
        ).order_by('order')[:limit]
    )


def get_articles_by_category(category_slug: str, language: str = 'es') -> list:
    """Get published articles in a category.

    Args:
        category_slug: Category slug
        language: Language code

    Returns:
        List of KnowledgeArticle objects
    """
    return list(
        KnowledgeArticle.objects.filter(
            category__slug=category_slug,
            is_published=True
        ).order_by('-priority')
    )
