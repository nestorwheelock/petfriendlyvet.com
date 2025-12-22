"""AI Context Builder for injecting knowledge base into AI prompts."""
from django.utils import timezone

from apps.knowledge.models import KnowledgeArticle
from apps.knowledge.utils import search_knowledge_base


def calculate_relevance(query: str, article: KnowledgeArticle) -> float:
    """Calculate relevance score for an article.

    Args:
        query: User query string
        article: KnowledgeArticle instance

    Returns:
        Float between 0 and 1 indicating relevance
    """
    score = 0.0

    if not query:
        return article.priority / 100  # Base on priority only

    query_words = set(query.lower().split())

    # Keyword matches (30% weight)
    if article.keywords:
        article_keywords = set(k.lower() for k in article.keywords if isinstance(k, str))
        keyword_matches = len(query_words & article_keywords)
        score += min(keyword_matches * 0.15, 0.3)

    # Title match (30% weight)
    title = (article.title_en or article.title_es or article.title).lower()
    title_matches = sum(1 for word in query_words if word in title)
    score += min(title_matches * 0.1, 0.3)

    # Priority boost (30% weight)
    score += (article.priority / 100) * 0.3

    # Recency bonus (10% weight)
    if article.updated_at:
        days_old = (timezone.now() - article.updated_at).days
        recency_score = max(0, (30 - days_old) / 30) * 0.1
        score += recency_score

    return min(score, 1.0)


class AIContextBuilder:
    """Builds AI system context from knowledge base."""

    # Core clinic information (hardcoded for reliability)
    CLINIC_INFO_ES = """
Eres el asistente virtual de Pet-Friendly, una clínica veterinaria en Puerto Morelos, Quintana Roo, México.

Información de la clínica:
- Nombre: Veterinaria Pet Friendly
- Veterinario: Dr. Pablo Rojo Mendoza
- Horario: Martes a Domingo, 9:00am - 8:00pm (Cerrado los Lunes)
- Teléfono/WhatsApp: +52 998 316 2438
- Ubicación: Puerto Morelos, Quintana Roo, México
- Servicios: Clínica veterinaria, Farmacia, Tienda de mascotas, Laboratorio

Directrices:
- Responde siempre de manera amable y profesional
- Si no sabes algo, sugiere contactar a la clínica
- Para emergencias, indica el teléfono de la clínica
- Puedes responder en español o inglés según el cliente
"""

    CLINIC_INFO_EN = """
You are the virtual assistant for Pet-Friendly, a veterinary clinic in Puerto Morelos, Quintana Roo, Mexico.

Clinic Information:
- Name: Veterinaria Pet Friendly
- Veterinarian: Dr. Pablo Rojo Mendoza
- Hours: Tuesday to Sunday, 9:00am - 8:00pm (Closed Mondays)
- Phone/WhatsApp: +52 998 316 2438
- Location: Puerto Morelos, Quintana Roo, Mexico
- Services: Veterinary clinic, Pharmacy, Pet store, Laboratory

Guidelines:
- Always respond in a friendly and professional manner
- If you don't know something, suggest contacting the clinic
- For emergencies, provide the clinic phone number
- You can respond in Spanish or English based on the customer
"""

    def __init__(self, language: str = 'es', max_tokens: int = 2000):
        """Initialize context builder.

        Args:
            language: Language code ('es' or 'en')
            max_tokens: Maximum tokens for context
        """
        self.language = language
        self.max_tokens = max_tokens
        self.token_count = 0

    def build_system_prompt(
        self,
        user_query: str = None,
        user=None
    ) -> str:
        """Build complete system prompt with relevant context.

        Args:
            user_query: Optional user query for relevance matching
            user: Optional User instance for personalization

        Returns:
            Complete system prompt string
        """
        sections = []

        # Core clinic info (always included)
        clinic_info = self._get_clinic_info()
        sections.append(clinic_info)
        self.token_count += len(clinic_info) / 4

        # User-specific context
        if user and user.is_authenticated:
            user_context = self._get_user_context(user)
            if user_context:
                sections.append(user_context)
                self.token_count += len(user_context) / 4

        # Query-relevant knowledge
        if user_query:
            knowledge_context = self._get_relevant_knowledge(user_query)
            if knowledge_context:
                sections.append(knowledge_context)

        return "\n\n".join(sections)

    def _get_clinic_info(self) -> str:
        """Get core clinic information in appropriate language."""
        if self.language == 'en':
            return self.CLINIC_INFO_EN
        return self.CLINIC_INFO_ES

    def _get_user_context(self, user) -> str:
        """Get user-specific context.

        Args:
            user: User instance

        Returns:
            User context string or empty string
        """
        if not user or not hasattr(user, 'username'):
            return ""

        # Basic user info
        name = user.first_name or user.username

        if self.language == 'en':
            return f"Customer: {name}"
        return f"Cliente: {name}"

    def _get_relevant_knowledge(self, query: str) -> str:
        """Search and retrieve relevant knowledge articles.

        Args:
            query: User query to search for

        Returns:
            Formatted knowledge context string
        """
        # Search for relevant articles
        articles = search_knowledge_base(query, self.language)

        if not articles:
            return ""

        # Score and sort by relevance
        scored = [(calculate_relevance(query, a), a) for a in articles]
        scored.sort(key=lambda x: x[0], reverse=True)

        # Build context within token budget
        context_parts = []
        remaining_tokens = self.max_tokens - self.token_count

        if self.language == 'en':
            header = "Relevant information:"
        else:
            header = "Información relevante:"

        context_parts.append(header)

        for score, article in scored[:5]:  # Max 5 articles
            # Prefer ai_context, fallback to content
            if article.ai_context:
                text = article.ai_context
            else:
                content = article.get_content(self.language)
                text = content[:300] if len(content) > 300 else content

            # Check token budget
            estimated_tokens = len(text) / 4
            if self.token_count + estimated_tokens > self.max_tokens:
                break

            context_parts.append(f"- {text}")
            self.token_count += estimated_tokens

        if len(context_parts) <= 1:  # Only header
            return ""

        return "\n".join(context_parts)


def get_system_prompt(
    language: str = 'es',
    user_query: str = None,
    user=None,
    max_tokens: int = 2000
) -> str:
    """Convenience function to build system prompt.

    Args:
        language: Language code
        user_query: Optional query for relevance
        user: Optional user for personalization
        max_tokens: Token budget

    Returns:
        Complete system prompt
    """
    builder = AIContextBuilder(language=language, max_tokens=max_tokens)
    return builder.build_system_prompt(user_query=user_query, user=user)
