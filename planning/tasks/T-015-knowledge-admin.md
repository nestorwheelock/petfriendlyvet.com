# T-015: Custom Admin for Knowledge Base

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Full Stack Developer
**Objective**: Implement mobile-first admin for knowledge base content
**Related Story**: S-011
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/knowledge/, apps/dashboard/, templates/admin/
**Forbidden Paths**: None

### Deliverables
- [ ] Knowledge base dashboard
- [ ] Article editor (WYSIWYG)
- [ ] Category management
- [ ] FAQ management
- [ ] Content preview
- [ ] Publish workflow
- [ ] Bulk operations

### Implementation Details

#### Dashboard Layout
Mobile-first design for Dr. Pablo:
```
┌─────────────────────────────────────┐
│ Knowledge Base                    ≡ │
├─────────────────────────────────────┤
│ ┌─────────┐ ┌─────────┐ ┌─────────┐│
│ │ Articles│ │  FAQs   │ │Categories││
│ │   23    │ │   45    │ │    8    ││
│ └─────────┘ └─────────┘ └─────────┘│
├─────────────────────────────────────┤
│ [+ New Article] [+ New FAQ]         │
├─────────────────────────────────────┤
│ Recent Updates                      │
│ ─────────────────────────────────── │
│ • Dog Nutrition Guide - 2h ago      │
│ • Clinic Hours Updated - 1d ago     │
│ • New Emergency FAQ - 3d ago        │
└─────────────────────────────────────┘
```

#### Article Editor
```html
<form hx-post="/admin/knowledge/articles/save/" hx-swap="none">
    <!-- Language tabs -->
    <div class="tabs">
        <button class="tab active">Español</button>
        <button class="tab">English</button>
    </div>

    <!-- Title -->
    <input type="text" name="title_es" placeholder="Título">

    <!-- WYSIWYG Editor -->
    <div id="editor" data-quill>
        <!-- Rich text editor -->
    </div>

    <!-- AI Context Summary -->
    <textarea name="ai_context" placeholder="Resumen para AI (opcional)">
    </textarea>

    <!-- Keywords -->
    <input type="text" name="keywords" placeholder="Palabras clave">

    <!-- Actions -->
    <button type="button" @click="preview()">Preview</button>
    <button type="submit" name="action" value="draft">Save Draft</button>
    <button type="submit" name="action" value="publish">Publish</button>
</form>
```

#### WYSIWYG Options
Using Quill.js for rich text editing:
- Bold, italic, underline
- Headers (H2, H3)
- Bullet and numbered lists
- Links
- Images (upload to S3)
- Code blocks (for medical info)

#### AI Context Generation
```python
async def generate_ai_context(article: KnowledgeArticle) -> str:
    """Generate condensed AI context from article content."""
    prompt = f"""
    Summarize this article in 2-3 sentences for AI context.
    Keep key facts and remove formatting.

    Title: {article.title}
    Content: {article.content}
    """
    return await ai_service.complete(prompt, max_tokens=150)
```

#### Bulk Operations
- Publish/unpublish multiple articles
- Move articles to category
- Export to CSV/JSON
- Import from CSV

### Test Cases
- [ ] Dashboard loads with stats
- [ ] Article editor saves correctly
- [ ] Rich text formats properly
- [ ] AI context generates
- [ ] Categories manageable
- [ ] FAQs CRUD works
- [ ] Publish workflow functions
- [ ] Mobile layout works

### Definition of Done
- [ ] Full CRUD for articles
- [ ] WYSIWYG working
- [ ] Mobile-optimized
- [ ] Publish workflow in place
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-014: Knowledge Base Models
- T-002: Base Templates
