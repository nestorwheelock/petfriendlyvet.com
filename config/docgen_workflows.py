"""
Workflow configuration for GIF animation recording.

Define the workflows to record for documentation.
"""

WORKFLOWS = {
    "login_flow": {
        "name": "Login Flow",
        "name_es": "Flujo de Inicio de Sesión",
        "role": "customer",
        "steps": [
            {"action": "goto", "url": "/accounts/login/"},
            {"action": "wait", "selector": "input[name='email']"},
            {"action": "fill", "selector": "input[name='email']", "value": "demo@example.com"},
            {"action": "fill", "selector": "input[name='password']", "value": "demo123"},
            {"action": "click", "selector": "button[type='submit']"},
            {"action": "wait", "selector": ".dashboard"},
        ],
        "output_gif": "login_flow.gif",
    },
    "add_pet_flow": {
        "name": "Add Pet Flow",
        "name_es": "Flujo de Agregar Mascota",
        "role": "customer",
        "steps": [
            {"action": "goto", "url": "/pets/add/"},
            {"action": "wait", "selector": "form"},
            {"action": "fill", "selector": "input[name='name']", "value": "Max"},
            {"action": "click", "selector": "select[name='species']"},
            {"action": "wait", "ms": 300},
            {"action": "click", "selector": "button[type='submit']"},
            {"action": "wait", "selector": ".success-message"},
        ],
        "output_gif": "add_pet_flow.gif",
    },
    "book_appointment_flow": {
        "name": "Book Appointment",
        "name_es": "Reservar Cita",
        "role": "customer",
        "steps": [
            {"action": "goto", "url": "/appointments/book/"},
            {"action": "wait", "selector": ".service-selection"},
            {"action": "click", "selector": "[data-service='consultation']"},
            {"action": "wait", "ms": 500},
            {"action": "click", "selector": ".available-date"},
            {"action": "wait", "ms": 500},
            {"action": "click", "selector": ".time-slot.available"},
            {"action": "click", "selector": "button[type='submit']"},
            {"action": "wait", "selector": ".confirmation"},
        ],
        "output_gif": "book_appointment.gif",
    },
    "checkout_flow": {
        "name": "Checkout Flow",
        "name_es": "Flujo de Compra",
        "role": "customer",
        "steps": [
            {"action": "goto", "url": "/store/"},
            {"action": "wait", "selector": ".product-card"},
            {"action": "click", "selector": ".product-card:first-child .add-to-cart"},
            {"action": "wait", "ms": 500},
            {"action": "goto", "url": "/store/cart/"},
            {"action": "wait", "selector": ".cart-items"},
            {"action": "click", "selector": ".checkout-btn"},
            {"action": "wait", "selector": ".checkout-form"},
        ],
        "output_gif": "checkout_flow.gif",
    },
    "loyalty_redemption_flow": {
        "name": "Redeem Reward",
        "name_es": "Canjear Recompensa",
        "role": "customer",
        "steps": [
            {"action": "goto", "url": "/loyalty/rewards/"},
            {"action": "wait", "selector": ".reward-card"},
            {"action": "click", "selector": ".reward-card:first-child .redeem-btn"},
            {"action": "wait", "selector": ".confirmation-modal"},
            {"action": "click", "selector": ".confirm-redeem"},
            {"action": "wait", "selector": ".success-message"},
        ],
        "output_gif": "loyalty_redemption.gif",
    },
}
