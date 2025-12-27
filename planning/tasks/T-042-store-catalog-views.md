# T-042: Store Catalog & Product Views

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Full Stack Developer
**Objective**: Implement store catalog browsing and product detail pages
**Related Story**: S-005
**Epoch**: 3
**Estimate**: 4 hours

### Constraints
**Allowed File Paths**: apps/store/, templates/store/
**Forbidden Paths**: apps/vet_clinic/

### Deliverables
- [ ] Product catalog page
- [ ] Category browsing
- [ ] Product detail page
- [ ] Search functionality
- [ ] Filtering and sorting
- [ ] Related products

### Implementation Details

#### Views
```python
class ProductCatalogView(ListView):
    """Browse all products."""

    model = Product
    template_name = 'store/catalog.html'
    context_object_name = 'products'
    paginate_by = 24

    def get_queryset(self):
        queryset = Product.objects.filter(
            is_active=True,
            is_published=True
        ).select_related('category').prefetch_related('images')

        # Category filter
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)

        # Search
        search = self.request.GET.get('q')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(sku__icontains=search)
            )

        # Price filter
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)

        # Species filter
        species = self.request.GET.get('species')
        if species:
            queryset = queryset.filter(species__contains=[species])

        # Sorting
        sort = self.request.GET.get('sort', 'featured')
        if sort == 'price_low':
            queryset = queryset.order_by('price')
        elif sort == 'price_high':
            queryset = queryset.order_by('-price')
        elif sort == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort == 'name':
            queryset = queryset.order_by('name')
        else:  # featured
            queryset = queryset.order_by('-is_featured', '-created_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(
            is_active=True, parent__isnull=True
        ).prefetch_related('children')
        context['current_category'] = self.request.GET.get('category')
        context['search_query'] = self.request.GET.get('q', '')
        context['sort'] = self.request.GET.get('sort', 'featured')
        return context


class ProductDetailView(DetailView):
    """Product detail page."""

    model = Product
    template_name = 'store/product_detail.html'
    context_object_name = 'product'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

    def get_queryset(self):
        return Product.objects.filter(
            is_active=True,
            is_published=True
        ).select_related('category').prefetch_related(
            'images', 'variants', 'reviews'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object

        # Related products
        context['related_products'] = Product.objects.filter(
            category=product.category,
            is_active=True,
            is_published=True
        ).exclude(id=product.id)[:4]

        # Reviews
        context['reviews'] = product.reviews.filter(
            is_approved=True
        ).select_related('user')[:10]

        # Average rating
        context['avg_rating'] = product.reviews.filter(
            is_approved=True
        ).aggregate(Avg('rating'))['rating__avg']

        # Stock status
        if product.track_inventory:
            if product.variants.exists():
                context['in_stock'] = product.variants.filter(
                    stock_quantity__gt=0
                ).exists()
            else:
                context['in_stock'] = product.stock_quantity > 0
        else:
            context['in_stock'] = True

        # Prescription check
        context['requires_prescription'] = product.requires_prescription

        return context


class CategoryView(ListView):
    """Products by category."""

    model = Product
    template_name = 'store/category.html'
    context_object_name = 'products'
    paginate_by = 24

    def get_queryset(self):
        self.category = get_object_or_404(
            Category, slug=self.kwargs['slug'], is_active=True
        )

        # Include subcategories
        category_ids = [self.category.id]
        category_ids.extend(
            self.category.children.values_list('id', flat=True)
        )

        return Product.objects.filter(
            category_id__in=category_ids,
            is_active=True,
            is_published=True
        ).select_related('category').prefetch_related('images')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['subcategories'] = self.category.children.filter(is_active=True)
        return context
```

#### URL Patterns
```python
urlpatterns = [
    path('', ProductCatalogView.as_view(), name='catalog'),
    path('search/', ProductCatalogView.as_view(), name='search'),
    path('category/<slug:slug>/', CategoryView.as_view(), name='category'),
    path('product/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
]
```

#### Templates (store/catalog.html)
```html
{% extends "base.html" %}
{% load i18n %}

{% block content %}
<div x-data="storeCatalog()" class="container mx-auto px-4 py-8">

    <!-- Search & Filters -->
    <div class="flex flex-col md:flex-row gap-4 mb-8">
        <!-- Search -->
        <form method="get" class="flex-grow">
            <input type="text"
                   name="q"
                   value="{{ search_query }}"
                   placeholder="{% trans 'Buscar productos...' %}"
                   class="w-full px-4 py-2 border rounded-lg">
        </form>

        <!-- Sort -->
        <select name="sort"
                @change="updateSort($event.target.value)"
                class="px-4 py-2 border rounded-lg">
            <option value="featured">{% trans 'Destacados' %}</option>
            <option value="price_low">{% trans 'Precio: Menor a Mayor' %}</option>
            <option value="price_high">{% trans 'Precio: Mayor a Menor' %}</option>
            <option value="newest">{% trans 'Más Nuevos' %}</option>
            <option value="name">{% trans 'Nombre' %}</option>
        </select>
    </div>

    <div class="flex flex-col md:flex-row gap-8">
        <!-- Sidebar Filters -->
        <aside class="w-full md:w-64 flex-shrink-0">
            <!-- Categories -->
            <div class="mb-6">
                <h3 class="font-semibold mb-3">{% trans 'Categorías' %}</h3>
                <ul class="space-y-2">
                    {% for category in categories %}
                    <li>
                        <a href="?category={{ category.slug }}"
                           class="{% if current_category == category.slug %}font-bold{% endif %}">
                            {{ category.name }}
                        </a>
                        {% if category.children.exists %}
                        <ul class="ml-4 mt-1 space-y-1">
                            {% for child in category.children.all %}
                            <li>
                                <a href="?category={{ child.slug }}">{{ child.name }}</a>
                            </li>
                            {% endfor %}
                        </ul>
                        {% endif %}
                    </li>
                    {% endfor %}
                </ul>
            </div>

            <!-- Species Filter -->
            <div class="mb-6">
                <h3 class="font-semibold mb-3">{% trans 'Especie' %}</h3>
                <div class="space-y-2">
                    <label class="flex items-center">
                        <input type="checkbox" name="species" value="dog" class="mr-2">
                        {% trans 'Perros' %}
                    </label>
                    <label class="flex items-center">
                        <input type="checkbox" name="species" value="cat" class="mr-2">
                        {% trans 'Gatos' %}
                    </label>
                </div>
            </div>

            <!-- Price Range -->
            <div class="mb-6">
                <h3 class="font-semibold mb-3">{% trans 'Precio' %}</h3>
                <div class="flex gap-2">
                    <input type="number" name="min_price"
                           placeholder="Min" class="w-20 px-2 py-1 border rounded">
                    <span>-</span>
                    <input type="number" name="max_price"
                           placeholder="Max" class="w-20 px-2 py-1 border rounded">
                </div>
            </div>
        </aside>

        <!-- Product Grid -->
        <main class="flex-grow">
            <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {% for product in products %}
                <div class="bg-white rounded-lg shadow hover:shadow-lg transition">
                    <a href="{% url 'store:product_detail' product.slug %}">
                        <img src="{{ product.primary_image.url }}"
                             alt="{{ product.name }}"
                             class="w-full h-48 object-cover rounded-t-lg">
                    </a>
                    <div class="p-4">
                        <a href="{% url 'store:product_detail' product.slug %}"
                           class="font-medium hover:text-primary">
                            {{ product.name }}
                        </a>
                        <p class="text-gray-600 text-sm mt-1">{{ product.category.name }}</p>

                        <div class="flex justify-between items-center mt-3">
                            <span class="text-lg font-bold">${{ product.price }}</span>

                            {% if product.requires_prescription %}
                            <span class="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                                {% trans 'Receta' %}
                            </span>
                            {% else %}
                            <button @click="addToCart({{ product.id }})"
                                    class="bg-primary text-white px-3 py-1 rounded hover:bg-primary-dark">
                                {% trans 'Agregar' %}
                            </button>
                            {% endif %}
                        </div>
                    </div>
                </div>
                {% empty %}
                <p class="col-span-full text-center text-gray-500 py-12">
                    {% trans 'No se encontraron productos.' %}
                </p>
                {% endfor %}
            </div>

            <!-- Pagination -->
            {% if page_obj.has_other_pages %}
            <nav class="flex justify-center mt-8">
                {% if page_obj.has_previous %}
                <a href="?page={{ page_obj.previous_page_number }}"
                   class="px-4 py-2 border rounded-l-lg">←</a>
                {% endif %}
                <span class="px-4 py-2 border-t border-b">
                    {{ page_obj.number }} / {{ page_obj.paginator.num_pages }}
                </span>
                {% if page_obj.has_next %}
                <a href="?page={{ page_obj.next_page_number }}"
                   class="px-4 py-2 border rounded-r-lg">→</a>
                {% endif %}
            </nav>
            {% endif %}
        </main>
    </div>
</div>

<script>
function storeCatalog() {
    return {
        async addToCart(productId) {
            const response = await fetch('/api/cart/add/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({ product_id: productId, quantity: 1 })
            });

            if (response.ok) {
                window.dispatchEvent(new CustomEvent('cart-updated'));
            }
        },

        updateSort(value) {
            const url = new URL(window.location);
            url.searchParams.set('sort', value);
            window.location = url;
        }
    }
}
</script>
{% endblock %}
```

### Test Cases
- [ ] Catalog displays products
- [ ] Category filtering works
- [ ] Search returns results
- [ ] Price filtering works
- [ ] Sorting works correctly
- [ ] Pagination works
- [ ] Product detail loads
- [ ] Add to cart works
- [ ] Related products show

### Definition of Done
- [ ] All views implemented
- [ ] Templates responsive
- [ ] Filtering and search functional
- [ ] Tests written and passing (>95% coverage)

### Dependencies
- T-036: Product & Category Models
- T-002: Base Templates
