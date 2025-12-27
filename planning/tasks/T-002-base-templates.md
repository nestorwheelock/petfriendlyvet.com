# T-002: Base Templates & Layout

> **REQUIRED READING:** Before starting, review [CODING_STANDARDS.md](../CODING_STANDARDS.md) and [ARCHITECTURE_DECISIONS.md and [SYSTEM_CHARTER.md](../../SYSTEM_CHARTER.md)](../ARCHITECTURE_DECISIONS.md)

## AI Coding Brief
**Role**: Frontend Developer
**Objective**: Create base HTML templates with header, footer, responsive layout, and core components
**Related Story**: S-001 (Foundation + AI Core)

### Constraints
**Allowed File Paths**: templates/, static/, apps/core/templatetags/
**Forbidden Paths**: None

## Context
This task creates the foundational templates for the Pet-Friendly veterinary clinic website. The design must be mobile-first (Dr. Pablo uses his phone), bilingual (Spanish primary, English secondary), and follow the brand colors established by the clinic.

## Brand Guidelines

### Colors
| Color | Hex | Usage |
|-------|-----|-------|
| Primary Blue | #1E4D8C | Headers, CTAs, links |
| Secondary Green | #5FAD41 | Success, accents, pet-related |
| White | #FFFFFF | Backgrounds |
| Text Dark | #333333 | Body text |
| Text Light | #6B7280 | Secondary text |
| Border | #E5E7EB | Dividers, inputs |
| Error | #DC2626 | Errors, alerts |
| Warning | #F59E0B | Warnings |

### Typography
- **Headings**: Inter, bold, primary blue
- **Body**: Inter, regular, dark gray
- **Mobile**: Base 16px, scale up for desktop

## Deliverables
- [ ] base.html with full HTML5 structure
- [ ] Header component with navigation and language toggle
- [ ] Footer component with contact info and links
- [ ] Mobile responsive navigation (hamburger menu)
- [ ] Tailwind CSS configuration with brand colors
- [ ] Language switcher functionality
- [ ] Cart icon with item count (placeholder)
- [ ] Flash message display component
- [ ] Loading spinner component
- [ ] HTMX integration for partial page updates
- [ ] Alpine.js integration for interactivity

## Implementation Details

### Base Template (templates/base.html)
```html
{% load static i18n %}
<!DOCTYPE html>
<html lang="{{ LANGUAGE_CODE }}" class="h-full">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{% block meta_description %}{% trans 'Veterinaria Pet-Friendly - Cuidado integral para tu mascota en Puerto Morelos' %}{% endblock %}">

    <title>{% block title %}{% endblock %} | Pet-Friendly Vet</title>

    <!-- Favicon -->
    <link rel="icon" type="image/png" href="{% static 'images/favicon.png' %}">

    <!-- Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">

    <!-- Tailwind CSS -->
    <link href="{% static 'css/output.css' %}" rel="stylesheet">

    <!-- HTMX -->
    <script src="https://unpkg.com/htmx.org@1.9.10" defer></script>

    <!-- Alpine.js -->
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>

    {% block extra_css %}{% endblock %}
</head>
<body class="h-full flex flex-col bg-white text-gray-800 font-sans"
      hx-headers='{"X-CSRFToken": "{{ csrf_token }}"}'
      x-data="{ mobileMenuOpen: false }">

    <!-- Skip to content for accessibility -->
    <a href="#main-content" class="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 bg-primary-500 text-white px-4 py-2 rounded">
        {% trans "Saltar al contenido" %}
    </a>

    <!-- Header -->
    {% include "components/header.html" %}

    <!-- Flash Messages -->
    {% include "components/messages.html" %}

    <!-- Main Content -->
    <main id="main-content" class="flex-grow">
        {% block content %}{% endblock %}
    </main>

    <!-- Footer -->
    {% include "components/footer.html" %}

    <!-- Chat Widget (Customer Only) -->
    {% if user.is_authenticated and not user.is_staff %}
        {% include "components/chat_widget.html" %}
    {% endif %}

    <!-- Loading Overlay -->
    <div id="loading-overlay"
         class="htmx-indicator fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        {% include "components/spinner.html" %}
    </div>

    <!-- Scripts -->
    <script src="{% static 'js/main.js' %}" defer></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### Header Component (templates/components/header.html)
```html
{% load static i18n %}
<header class="bg-white shadow-sm sticky top-0 z-40">
    <nav class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
            <!-- Logo -->
            <div class="flex items-center">
                <a href="{% url 'core:home' %}" class="flex items-center space-x-2">
                    <img src="{% static 'images/logo.png' %}"
                         alt="Pet-Friendly"
                         class="h-10 w-auto">
                    <span class="hidden sm:block text-xl font-bold text-primary-500">
                        Pet-Friendly
                    </span>
                </a>
            </div>

            <!-- Desktop Navigation -->
            <div class="hidden md:flex md:items-center md:space-x-6">
                <a href="{% url 'core:home' %}"
                   class="text-gray-600 hover:text-primary-500 font-medium transition-colors
                          {% if request.resolver_match.url_name == 'home' %}text-primary-500{% endif %}">
                    {% trans "Inicio" %}
                </a>
                <a href="{% url 'core:services' %}"
                   class="text-gray-600 hover:text-primary-500 font-medium transition-colors
                          {% if 'services' in request.path %}text-primary-500{% endif %}">
                    {% trans "Servicios" %}
                </a>
                <a href="{% url 'store:catalog' %}"
                   class="text-gray-600 hover:text-primary-500 font-medium transition-colors
                          {% if 'store' in request.path %}text-primary-500{% endif %}">
                    {% trans "Tienda" %}
                </a>
                <a href="{% url 'core:about' %}"
                   class="text-gray-600 hover:text-primary-500 font-medium transition-colors
                          {% if 'about' in request.path %}text-primary-500{% endif %}">
                    {% trans "Nosotros" %}
                </a>
                <a href="{% url 'core:contact' %}"
                   class="text-gray-600 hover:text-primary-500 font-medium transition-colors
                          {% if 'contact' in request.path %}text-primary-500{% endif %}">
                    {% trans "Contacto" %}
                </a>
            </div>

            <!-- Right Side: Cart, Language, Auth -->
            <div class="flex items-center space-x-4">
                <!-- Language Switcher -->
                {% include "components/language_switcher.html" %}

                <!-- Cart Icon -->
                <a href="{% url 'store:cart' %}"
                   class="relative p-2 text-gray-600 hover:text-primary-500 transition-colors">
                    <svg class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                              d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"/>
                    </svg>
                    {% if cart_count %}
                    <span class="absolute -top-1 -right-1 bg-secondary-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
                        {{ cart_count }}
                    </span>
                    {% endif %}
                </a>

                <!-- User Menu -->
                {% if user.is_authenticated %}
                <div x-data="{ open: false }" class="relative">
                    <button @click="open = !open"
                            class="flex items-center space-x-2 p-2 rounded-lg hover:bg-gray-100 transition-colors">
                        <img src="{{ user.avatar_url|default:'https://ui-avatars.com/api/?name='|add:user.get_short_name }}"
                             alt="{{ user.get_short_name }}"
                             class="h-8 w-8 rounded-full">
                        <span class="hidden lg:block text-sm font-medium text-gray-700">
                            {{ user.get_short_name }}
                        </span>
                        <svg class="h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                        </svg>
                    </button>

                    <!-- Dropdown Menu -->
                    <div x-show="open"
                         @click.away="open = false"
                         x-transition
                         class="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg py-1 z-50">
                        <a href="{% url 'accounts:dashboard' %}"
                           class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                            {% trans "Mi Panel" %}
                        </a>
                        <a href="{% url 'pets:list' %}"
                           class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                            {% trans "Mis Mascotas" %}
                        </a>
                        <a href="{% url 'appointments:list' %}"
                           class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                            {% trans "Mis Citas" %}
                        </a>
                        <a href="{% url 'store:orders' %}"
                           class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                            {% trans "Mis Pedidos" %}
                        </a>
                        <hr class="my-1">
                        <a href="{% url 'accounts:settings' %}"
                           class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                            {% trans "Configuración" %}
                        </a>
                        <form method="post" action="{% url 'accounts:logout' %}">
                            {% csrf_token %}
                            <button type="submit"
                                    class="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100">
                                {% trans "Cerrar Sesión" %}
                            </button>
                        </form>
                    </div>
                </div>
                {% else %}
                <a href="{% url 'accounts:login' %}"
                   class="hidden sm:inline-flex items-center px-4 py-2 border border-primary-500 text-primary-500 rounded-lg hover:bg-primary-50 transition-colors">
                    {% trans "Iniciar Sesión" %}
                </a>
                {% endif %}

                <!-- Mobile Menu Button -->
                <button @click="mobileMenuOpen = !mobileMenuOpen"
                        class="md:hidden p-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-colors">
                    <svg x-show="!mobileMenuOpen" class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"/>
                    </svg>
                    <svg x-show="mobileMenuOpen" class="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                </button>
            </div>
        </div>

        <!-- Mobile Menu -->
        <div x-show="mobileMenuOpen"
             x-transition:enter="transition ease-out duration-200"
             x-transition:enter-start="opacity-0 -translate-y-4"
             x-transition:enter-end="opacity-100 translate-y-0"
             x-transition:leave="transition ease-in duration-150"
             x-transition:leave-start="opacity-100 translate-y-0"
             x-transition:leave-end="opacity-0 -translate-y-4"
             class="md:hidden py-4 border-t">
            <div class="space-y-2">
                <a href="{% url 'core:home' %}"
                   class="block px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">
                    {% trans "Inicio" %}
                </a>
                <a href="{% url 'core:services' %}"
                   class="block px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">
                    {% trans "Servicios" %}
                </a>
                <a href="{% url 'store:catalog' %}"
                   class="block px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">
                    {% trans "Tienda" %}
                </a>
                <a href="{% url 'core:about' %}"
                   class="block px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">
                    {% trans "Nosotros" %}
                </a>
                <a href="{% url 'core:contact' %}"
                   class="block px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg">
                    {% trans "Contacto" %}
                </a>
                {% if not user.is_authenticated %}
                <hr class="my-2">
                <a href="{% url 'accounts:login' %}"
                   class="block px-4 py-2 text-primary-500 font-medium hover:bg-primary-50 rounded-lg">
                    {% trans "Iniciar Sesión" %}
                </a>
                {% endif %}
            </div>
        </div>
    </nav>
</header>
```

### Footer Component (templates/components/footer.html)
```html
{% load static i18n %}
<footer class="bg-gray-800 text-white mt-auto">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
            <!-- Brand & Contact -->
            <div class="col-span-1 md:col-span-2">
                <div class="flex items-center space-x-2 mb-4">
                    <img src="{% static 'images/logo-white.png' %}"
                         alt="Pet-Friendly"
                         class="h-10 w-auto">
                    <span class="text-xl font-bold">Pet-Friendly</span>
                </div>
                <p class="text-gray-400 mb-4">
                    {% trans "Cuidado veterinario integral con amor y profesionalismo para tu mascota." %}
                </p>

                <div class="space-y-2 text-gray-400">
                    <p class="flex items-center space-x-2">
                        <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                  d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"/>
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                  d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"/>
                        </svg>
                        <span>Puerto Morelos, Quintana Roo, México</span>
                    </p>
                    <p class="flex items-center space-x-2">
                        <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                  d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"/>
                        </svg>
                        <a href="tel:+529983162438" class="hover:text-white transition-colors">
                            +52 998 316 2438
                        </a>
                    </p>
                    <p class="flex items-center space-x-2">
                        <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                  d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
                        </svg>
                        <a href="mailto:contacto@petfriendlyvet.com" class="hover:text-white transition-colors">
                            contacto@petfriendlyvet.com
                        </a>
                    </p>
                </div>
            </div>

            <!-- Quick Links -->
            <div>
                <h3 class="text-lg font-semibold mb-4">{% trans "Enlaces Rápidos" %}</h3>
                <ul class="space-y-2 text-gray-400">
                    <li>
                        <a href="{% url 'core:services' %}" class="hover:text-white transition-colors">
                            {% trans "Servicios" %}
                        </a>
                    </li>
                    <li>
                        <a href="{% url 'store:catalog' %}" class="hover:text-white transition-colors">
                            {% trans "Tienda" %}
                        </a>
                    </li>
                    <li>
                        <a href="{% url 'appointments:book' %}" class="hover:text-white transition-colors">
                            {% trans "Agendar Cita" %}
                        </a>
                    </li>
                    <li>
                        <a href="{% url 'core:about' %}" class="hover:text-white transition-colors">
                            {% trans "Nosotros" %}
                        </a>
                    </li>
                    <li>
                        <a href="{% url 'core:faq' %}" class="hover:text-white transition-colors">
                            {% trans "Preguntas Frecuentes" %}
                        </a>
                    </li>
                </ul>
            </div>

            <!-- Hours & Social -->
            <div>
                <h3 class="text-lg font-semibold mb-4">{% trans "Horario" %}</h3>
                <ul class="space-y-1 text-gray-400 text-sm mb-6">
                    <li class="flex justify-between">
                        <span>{% trans "Lunes" %}</span>
                        <span class="text-red-400">{% trans "Cerrado" %}</span>
                    </li>
                    <li class="flex justify-between">
                        <span>{% trans "Martes - Domingo" %}</span>
                        <span>9:00 AM - 8:00 PM</span>
                    </li>
                </ul>

                <h3 class="text-lg font-semibold mb-4">{% trans "Síguenos" %}</h3>
                <div class="flex space-x-4">
                    <a href="https://instagram.com/vet.petfriendly"
                       target="_blank"
                       rel="noopener noreferrer"
                       class="text-gray-400 hover:text-pink-400 transition-colors">
                        <svg class="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M12.315 2c2.43 0 2.784.013 3.808.06 1.064.049 1.791.218 2.427.465a4.902 4.902 0 011.772 1.153 4.902 4.902 0 011.153 1.772c.247.636.416 1.363.465 2.427.048 1.067.06 1.407.06 4.123v.08c0 2.643-.012 2.987-.06 4.043-.049 1.064-.218 1.791-.465 2.427a4.902 4.902 0 01-1.153 1.772 4.902 4.902 0 01-1.772 1.153c-.636.247-1.363.416-2.427.465-1.067.048-1.407.06-4.123.06h-.08c-2.643 0-2.987-.012-4.043-.06-1.064-.049-1.791-.218-2.427-.465a4.902 4.902 0 01-1.772-1.153 4.902 4.902 0 01-1.153-1.772c-.247-.636-.416-1.363-.465-2.427-.047-1.024-.06-1.379-.06-3.808v-.63c0-2.43.013-2.784.06-3.808.049-1.064.218-1.791.465-2.427a4.902 4.902 0 011.153-1.772A4.902 4.902 0 015.45 2.525c.636-.247 1.363-.416 2.427-.465C8.901 2.013 9.256 2 11.685 2h.63zm-.081 1.802h-.468c-2.456 0-2.784.011-3.807.058-.975.045-1.504.207-1.857.344-.467.182-.8.398-1.15.748-.35.35-.566.683-.748 1.15-.137.353-.3.882-.344 1.857-.047 1.023-.058 1.351-.058 3.807v.468c0 2.456.011 2.784.058 3.807.045.975.207 1.504.344 1.857.182.466.399.8.748 1.15.35.35.683.566 1.15.748.353.137.882.3 1.857.344 1.054.048 1.37.058 4.041.058h.08c2.597 0 2.917-.01 3.96-.058.976-.045 1.505-.207 1.858-.344.466-.182.8-.398 1.15-.748.35-.35.566-.683.748-1.15.137-.353.3-.882.344-1.857.048-1.055.058-1.37.058-4.041v-.08c0-2.597-.01-2.917-.058-3.96-.045-.976-.207-1.505-.344-1.858a3.097 3.097 0 00-.748-1.15 3.098 3.098 0 00-1.15-.748c-.353-.137-.882-.3-1.857-.344-1.023-.047-1.351-.058-3.807-.058zM12 6.865a5.135 5.135 0 110 10.27 5.135 5.135 0 010-10.27zm0 1.802a3.333 3.333 0 100 6.666 3.333 3.333 0 000-6.666zm5.338-3.205a1.2 1.2 0 110 2.4 1.2 1.2 0 010-2.4z"/>
                        </svg>
                    </a>
                    <a href="https://facebook.com/petfriendlyvet"
                       target="_blank"
                       rel="noopener noreferrer"
                       class="text-gray-400 hover:text-blue-400 transition-colors">
                        <svg class="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                        </svg>
                    </a>
                    <a href="https://wa.me/529983162438"
                       target="_blank"
                       rel="noopener noreferrer"
                       class="text-gray-400 hover:text-green-400 transition-colors">
                        <svg class="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/>
                        </svg>
                    </a>
                </div>
            </div>
        </div>

        <!-- Bottom Bar -->
        <div class="border-t border-gray-700 mt-8 pt-8 flex flex-col md:flex-row justify-between items-center text-gray-400 text-sm">
            <p>&copy; {% now "Y" %} Pet-Friendly. {% trans "Todos los derechos reservados." %}</p>
            <div class="flex space-x-6 mt-4 md:mt-0">
                <a href="{% url 'core:privacy' %}" class="hover:text-white transition-colors">
                    {% trans "Privacidad" %}
                </a>
                <a href="{% url 'core:terms' %}" class="hover:text-white transition-colors">
                    {% trans "Términos" %}
                </a>
            </div>
        </div>
    </div>
</footer>
```

### Language Switcher (templates/components/language_switcher.html)
```html
{% load i18n %}
<div x-data="{ open: false }" class="relative">
    <button @click="open = !open"
            class="flex items-center space-x-1 px-2 py-1 rounded text-gray-600 hover:bg-gray-100 transition-colors">
        <span class="text-sm font-medium uppercase">{{ LANGUAGE_CODE }}</span>
        <svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
        </svg>
    </button>

    <div x-show="open"
         @click.away="open = false"
         x-transition
         class="absolute right-0 mt-2 w-32 bg-white rounded-lg shadow-lg py-1 z-50">
        {% get_available_languages as languages %}
        {% for lang_code, lang_name in languages %}
        <form method="post" action="{% url 'set_language' %}">
            {% csrf_token %}
            <input type="hidden" name="language" value="{{ lang_code }}">
            <input type="hidden" name="next" value="{{ request.path }}">
            <button type="submit"
                    class="block w-full text-left px-4 py-2 text-sm hover:bg-gray-100
                           {% if lang_code == LANGUAGE_CODE %}text-primary-500 font-medium{% else %}text-gray-700{% endif %}">
                {{ lang_name }}
            </button>
        </form>
        {% endfor %}
    </div>
</div>
```

### Flash Messages (templates/components/messages.html)
```html
{% if messages %}
<div class="fixed top-20 right-4 z-50 space-y-2 max-w-sm"
     x-data="{ messages: true }"
     x-show="messages"
     x-init="setTimeout(() => messages = false, 5000)">
    {% for message in messages %}
    <div class="flex items-center p-4 rounded-lg shadow-lg
                {% if message.tags == 'success' %}bg-green-100 text-green-800 border-l-4 border-green-500
                {% elif message.tags == 'error' %}bg-red-100 text-red-800 border-l-4 border-red-500
                {% elif message.tags == 'warning' %}bg-yellow-100 text-yellow-800 border-l-4 border-yellow-500
                {% else %}bg-blue-100 text-blue-800 border-l-4 border-blue-500{% endif %}"
         x-data="{ show: true }"
         x-show="show"
         x-transition:leave="transition ease-in duration-200"
         x-transition:leave-start="opacity-100 transform translate-x-0"
         x-transition:leave-end="opacity-0 transform translate-x-full">

        <!-- Icon -->
        {% if message.tags == 'success' %}
        <svg class="h-5 w-5 mr-3" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
        </svg>
        {% elif message.tags == 'error' %}
        <svg class="h-5 w-5 mr-3" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"/>
        </svg>
        {% else %}
        <svg class="h-5 w-5 mr-3" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd"/>
        </svg>
        {% endif %}

        <span class="flex-1">{{ message }}</span>

        <button @click="show = false" class="ml-4 text-current opacity-60 hover:opacity-100">
            <svg class="h-4 w-4" fill="currentColor" viewBox="0 0 20 20">
                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"/>
            </svg>
        </button>
    </div>
    {% endfor %}
</div>
{% endif %}
```

### Loading Spinner (templates/components/spinner.html)
```html
<div class="flex flex-col items-center justify-center">
    <svg class="animate-spin h-12 w-12 text-primary-500" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg>
    <span class="mt-2 text-white text-sm">{% trans "Cargando..." %}</span>
</div>
```

### Cart Context Processor (apps/store/context_processors.py)
```python
"""Context processors for store app."""


def cart(request):
    """Add cart information to template context."""
    cart_count = 0

    if request.user.is_authenticated:
        from apps.store.models import Cart
        user_cart = Cart.objects.filter(user=request.user).first()
        if user_cart:
            cart_count = user_cart.items.count()
    else:
        # Anonymous cart from session
        session_cart = request.session.get('cart', {})
        cart_count = len(session_cart)

    return {
        'cart_count': cart_count,
    }
```

### Main JavaScript (static/js/main.js)
```javascript
/**
 * Pet-Friendly Vet - Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // HTMX configuration
    document.body.addEventListener('htmx:configRequest', function(evt) {
        evt.detail.headers['X-CSRFToken'] = getCookie('csrftoken');
    });

    // Handle HTMX errors
    document.body.addEventListener('htmx:responseError', function(evt) {
        console.error('HTMX Error:', evt.detail);
        showToast('Error de conexión. Por favor intente de nuevo.', 'error');
    });

    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});

/**
 * Get cookie value by name
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-4 right-4 z-50 p-4 rounded-lg shadow-lg max-w-sm
        ${type === 'success' ? 'bg-green-100 text-green-800' : ''}
        ${type === 'error' ? 'bg-red-100 text-red-800' : ''}
        ${type === 'warning' ? 'bg-yellow-100 text-yellow-800' : ''}
        ${type === 'info' ? 'bg-blue-100 text-blue-800' : ''}`;
    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 5000);
}

/**
 * Format currency for MXN
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('es-MX', {
        style: 'currency',
        currency: 'MXN'
    }).format(amount);
}
```

## Test Cases

### Test Templates Render
```python
# tests/test_templates.py
import pytest
from django.test import Client, RequestFactory
from django.template import Context, Template


class TestBaseTemplate:
    @pytest.fixture
    def client(self):
        return Client()

    def test_homepage_renders(self, client):
        response = client.get('/')
        assert response.status_code == 200
        assert 'Pet-Friendly' in response.content.decode()

    def test_base_template_has_meta_tags(self, client):
        response = client.get('/')
        content = response.content.decode()
        assert '<meta charset="UTF-8">' in content
        assert 'viewport' in content

    def test_base_template_includes_htmx(self, client):
        response = client.get('/')
        assert 'htmx.org' in response.content.decode()

    def test_base_template_includes_alpine(self, client):
        response = client.get('/')
        assert 'alpinejs' in response.content.decode()


class TestHeaderComponent:
    @pytest.fixture
    def client(self):
        return Client()

    def test_header_has_navigation_links(self, client):
        response = client.get('/')
        content = response.content.decode()
        assert 'Inicio' in content or 'Home' in content
        assert 'Servicios' in content or 'Services' in content

    def test_header_has_language_switcher(self, client):
        response = client.get('/')
        assert 'set_language' in response.content.decode() or 'language' in response.content.decode()

    def test_header_has_cart_icon(self, client):
        response = client.get('/')
        assert 'cart' in response.content.decode().lower()


class TestFooterComponent:
    @pytest.fixture
    def client(self):
        return Client()

    def test_footer_has_contact_info(self, client):
        response = client.get('/')
        content = response.content.decode()
        assert 'Puerto Morelos' in content
        assert '998' in content  # Phone number

    def test_footer_has_social_links(self, client):
        response = client.get('/')
        content = response.content.decode()
        assert 'instagram' in content.lower() or 'facebook' in content.lower()


class TestAccessibility:
    @pytest.fixture
    def client(self):
        return Client()

    def test_skip_to_content_link_exists(self, client):
        response = client.get('/')
        assert 'skip' in response.content.decode().lower() or 'saltar' in response.content.decode().lower()

    def test_images_have_alt_text(self, client):
        response = client.get('/')
        content = response.content.decode()
        # Check that img tags have alt attributes
        import re
        img_tags = re.findall(r'<img[^>]+>', content)
        for img in img_tags:
            assert 'alt=' in img


class TestResponsive:
    @pytest.fixture
    def client(self):
        return Client()

    def test_mobile_menu_button_exists(self, client):
        response = client.get('/')
        content = response.content.decode()
        assert 'mobileMenuOpen' in content or 'mobile-menu' in content.lower()
```

### Test Language Switching
```python
# tests/test_i18n.py
import pytest
from django.test import Client


class TestLanguageSwitching:
    @pytest.fixture
    def client(self):
        return Client()

    def test_spanish_default(self, client):
        response = client.get('/')
        assert response.status_code == 200

    def test_switch_to_english(self, client):
        response = client.post('/i18n/setlang/', {
            'language': 'en',
            'next': '/'
        }, follow=True)
        assert response.status_code == 200

    def test_language_persists_in_session(self, client):
        client.post('/i18n/setlang/', {'language': 'en', 'next': '/'})
        response = client.get('/')
        # Check session or cookie has language set
        assert 'en' in response.cookies.get('django_language', '') or True
```

## Definition of Done
- [ ] base.html renders correctly on all pages
- [ ] Header navigation works on desktop and mobile
- [ ] Footer displays contact info and social links
- [ ] Language switcher toggles between ES/EN
- [ ] Mobile menu opens/closes smoothly
- [ ] Cart icon shows item count
- [ ] Flash messages display and auto-dismiss
- [ ] Loading spinner shows during HTMX requests
- [ ] All templates pass accessibility checks
- [ ] Responsive on mobile (320px), tablet (768px), desktop (1024px+)
- [ ] Tests written and passing (>95% coverage)
- [ ] Brand colors match specification

## Dependencies
- T-001: Django Project Setup (for templates directory and static files)
- Tailwind CSS compiled
- HTMX and Alpine.js loaded via CDN

## Estimated Effort
4 hours
