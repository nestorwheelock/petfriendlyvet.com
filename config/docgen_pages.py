"""
Page configuration for documentation generation.

Define the pages to capture for each guide type.
"""

PAGES = {
    "admin": {
        "practice": {
            "name": "Practice Management",
            "name_es": "Gestión de Práctica",
            "role": "staff",
            "pages": [
                {
                    "id": "practice_dashboard",
                    "url": "/practice/",
                    "title": "Practice Dashboard",
                    "title_es": "Panel de Práctica",
                    "wait_for": ".max-w-7xl",
                },
                {
                    "id": "staff_list",
                    "url": "/practice/staff/",
                    "title": "Staff Directory",
                    "title_es": "Directorio de Personal",
                },
            ],
        },
        "inventory": {
            "name": "Inventory Management",
            "name_es": "Gestión de Inventario",
            "role": "staff",
            "pages": [
                {
                    "id": "inventory_dashboard",
                    "url": "/inventory/",
                    "title": "Inventory Dashboard",
                    "title_es": "Panel de Inventario",
                },
                {
                    "id": "stock_levels",
                    "url": "/inventory/stock/",
                    "title": "Stock Levels",
                    "title_es": "Niveles de Stock",
                },
            ],
        },
        "referrals": {
            "name": "Referral Network",
            "name_es": "Red de Referidos",
            "role": "staff",
            "pages": [
                {
                    "id": "referrals_dashboard",
                    "url": "/referrals/",
                    "title": "Referrals Dashboard",
                    "title_es": "Panel de Referidos",
                },
            ],
        },
        "delivery": {
            "name": "Delivery Operations",
            "name_es": "Operaciones de Entrega",
            "role": "staff",
            "pages": [
                {
                    "id": "delivery_dashboard",
                    "url": "/delivery/",
                    "title": "Delivery Dashboard",
                    "title_es": "Panel de Entregas",
                },
                {
                    "id": "delivery_zones",
                    "url": "/delivery/zones/",
                    "title": "Delivery Zones",
                    "title_es": "Zonas de Entrega",
                },
            ],
        },
        "reports": {
            "name": "Reports & Analytics",
            "name_es": "Informes y Análisis",
            "role": "staff",
            "pages": [
                {
                    "id": "reports_dashboard",
                    "url": "/reports/",
                    "title": "Reports Dashboard",
                    "title_es": "Panel de Informes",
                },
            ],
        },
    },
    "user": {
        "account": {
            "name": "Account",
            "name_es": "Cuenta",
            "role": "customer",
            "pages": [
                {
                    "id": "profile",
                    "url": "/accounts/profile/",
                    "title": "Profile",
                    "title_es": "Perfil",
                },
            ],
        },
        "pets": {
            "name": "Pet Management",
            "name_es": "Gestión de Mascotas",
            "role": "customer",
            "pages": [
                {
                    "id": "pets_list",
                    "url": "/pets/",
                    "title": "My Pets",
                    "title_es": "Mis Mascotas",
                },
                {
                    "id": "add_pet",
                    "url": "/pets/add/",
                    "title": "Add Pet",
                    "title_es": "Agregar Mascota",
                },
            ],
        },
        "appointments": {
            "name": "Appointments",
            "name_es": "Citas",
            "role": "customer",
            "pages": [
                {
                    "id": "appointments_list",
                    "url": "/appointments/",
                    "title": "My Appointments",
                    "title_es": "Mis Citas",
                },
                {
                    "id": "book_appointment",
                    "url": "/appointments/book/",
                    "title": "Book Appointment",
                    "title_es": "Reservar Cita",
                },
            ],
        },
        "store": {
            "name": "Online Store",
            "name_es": "Tienda en Línea",
            "role": "customer",
            "pages": [
                {
                    "id": "store_home",
                    "url": "/store/",
                    "title": "Store Home",
                    "title_es": "Tienda",
                },
                {
                    "id": "cart",
                    "url": "/store/cart/",
                    "title": "Shopping Cart",
                    "title_es": "Carrito de Compras",
                },
            ],
        },
        "loyalty": {
            "name": "Loyalty Program",
            "name_es": "Programa de Lealtad",
            "role": "customer",
            "pages": [
                {
                    "id": "loyalty_dashboard",
                    "url": "/loyalty/",
                    "title": "Loyalty Dashboard",
                    "title_es": "Panel de Lealtad",
                },
                {
                    "id": "rewards",
                    "url": "/loyalty/rewards/",
                    "title": "Available Rewards",
                    "title_es": "Recompensas Disponibles",
                },
            ],
        },
        "billing": {
            "name": "Billing",
            "name_es": "Facturación",
            "role": "customer",
            "pages": [
                {
                    "id": "invoices",
                    "url": "/billing/",
                    "title": "Invoices",
                    "title_es": "Facturas",
                },
            ],
        },
    },
}
