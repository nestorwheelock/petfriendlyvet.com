# T-016: AI Context Injection

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Backend Developer
**Objective**: Implement knowledge base context injection for AI responses
**Related Story**: S-011
**Estimate**: 3 hours

### Constraints
**Allowed File Paths**: apps/ai_assistant/, apps/knowledge/
**Forbidden Paths**: None

### Deliverables
- [ ] Context builder service
- [ ] Relevance scoring
- [ ] Dynamic context selection
- [ ] Token budget management
- [ ] Context caching
- [ ] Priority-based inclusion

### Implementation Details

#### Context Builder
```python
class AIContextBuilder:
    """Builds AI system context from knowledge base."""

    def __init__(self, language: str = 'es', max_tokens: int = 2000):
        self.language = language
        self.max_tokens = max_tokens
        self.token_count = 0

    def build_system_prompt(
        self,
        user_query: str = None,
        user: User = None
    ) -> str:
        """Build complete system prompt with relevant context."""

        sections = []

        # Core clinic info (always included)
        sections.append(self._get_clinic_info())

        # User-specific context
        if user:
            sections.append(self._get_user_context(user))

        # Query-relevant knowledge
        if user_query:
            sections.append(self._get_relevant_knowledge(user_query))

        return "\n\n".join(sections)

    def _get_clinic_info(self) -> str:
        """Get core clinic information."""
        return """
        Eres el asistente virtual de Pet-Friendly, una clínica veterinaria
        en Puerto Morelos, Quintana Roo, México.

        Horario: Martes a Domingo, 9:00am - 8:00pm (Cerrado los Lunes)
        Teléfono: +52 998 316 2438
        Servicios: Clínica, Farmacia, Tienda de mascotas

        El Dr. Pablo Rojo Mendoza es el veterinario principal.
        """

    def _get_relevant_knowledge(self, query: str) -> str:
        """Search and retrieve relevant knowledge articles."""
        articles = search_knowledge_base(query, self.language)[:3]

        context = "Información relevante:\n"
        for article in articles:
            if self.token_count + len(article.ai_context) / 4 < self.max_tokens:
                context += f"- {article.ai_context}\n"
                self.token_count += len(article.ai_context) / 4

        return context
```

#### Relevance Scoring
```python
def calculate_relevance(query: str, article: KnowledgeArticle) -> float:
    """Calculate relevance score for an article."""
    score = 0.0

    # Keyword matches
    query_words = set(query.lower().split())
    article_keywords = set(article.keywords)
    score += len(query_words & article_keywords) * 0.3

    # Title match
    if any(word in article.title.lower() for word in query_words):
        score += 0.3

    # Priority boost
    score += article.priority * 0.1

    # Recency (articles updated recently rank higher)
    days_old = (timezone.now() - article.updated_at).days
    score += max(0, (30 - days_old) / 30) * 0.1

    return min(score, 1.0)
```

#### Dynamic Selection Algorithm
1. Always include: Clinic hours, location, contact
2. Query-based: Search knowledge base, include top 3
3. User-based: If logged in, include pet names, appointment history
4. Conversation-based: Include relevant past context
5. Token budget: Stop adding when approaching limit

#### Caching Strategy
```python
# Cache frequently accessed context
@cached(ttl=300)  # 5 minutes
def get_clinic_context(language: str) -> str:
    """Get cached clinic information."""
    pass

@cached(ttl=60)  # 1 minute for search results
def search_cached(query: str, language: str) -> list:
    """Cached knowledge search."""
    pass
```

#### Priority Levels
| Priority | Content Type | Example |
|----------|--------------|---------|
| 100 | Emergency | Poison hotline, emergency hours |
| 80 | Core services | Vaccination schedule, surgery prep |
| 60 | General info | Pet care tips, nutrition |
| 40 | Policies | Cancellation, payment policies |
| 20 | Nice-to-have | Staff bios, clinic history |

### Test Cases
- [ ] System prompt builds correctly
- [ ] Relevant knowledge included
- [ ] Token budget respected
- [ ] User context included
- [ ] Caching works
- [ ] Priority ordering correct
- [ ] Language switching works

### Definition of Done
- [ ] Context builder working
- [ ] Search integration complete
- [ ] Token management in place
- [ ] Caching implemented
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-009: AI Service Layer
- T-014: Knowledge Base Models
