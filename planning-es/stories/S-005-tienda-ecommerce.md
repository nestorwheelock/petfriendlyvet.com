# S-005: Tienda de Comercio Electrónico

**Tipo de Historia:** Historia de Usuario
**Prioridad:** Alta
**Estimación:** 4 días
**Época:** 3
**Estado:** Pendiente

## Historia de Usuario
**Como** dueño de mascota
**Quiero** comprar productos para mi mascota en línea
**Para que** pueda obtener lo que necesito sin tener que ir a la clínica

## Criterios de Aceptación
- [ ] Puedo navegar el catálogo de productos
- [ ] Puedo filtrar por categoría y especie
- [ ] Puedo buscar productos
- [ ] Puedo ver detalles de cada producto
- [ ] Puedo agregar productos al carrito
- [ ] Puedo ver y modificar mi carrito
- [ ] Puedo proceder al checkout
- [ ] Puedo pagar con tarjeta (Stripe)
- [ ] Puedo pagar en efectivo con OXXO
- [ ] Recibo confirmación de mi pedido
- [ ] Puedo ver el estado de mis pedidos

## Definición de Hecho
- [ ] Catálogo completo funcionando
- [ ] Carrito persistente
- [ ] Stripe integrado
- [ ] OXXO funcionando
- [ ] Emails de confirmación
- [ ] Pruebas >95% cobertura

## Tareas Relacionadas
- T-034: Modelos de Producto
- T-035: Modelos de Categoría
- T-036: Modelos de Inventario
- T-037: Carrito de Compras
- T-038: Checkout con Stripe
- T-039: Gestión de Pedidos
- T-042: Vistas del Catálogo
- T-043: Herramientas de IA para Compras

## Wireframes
Ver:
- `planning/wireframes/06-store.txt`
- `planning/wireframes/07-cart-checkout.txt`

## Categorías de Productos

| Categoría | Descripción |
|-----------|-------------|
| Alimento | Croquetas, alimento húmedo, snacks |
| Medicamentos | Con y sin receta |
| Suplementos | Vitaminas, probióticos |
| Accesorios | Collares, correas, juguetes |
| Higiene | Shampoos, cepillos, productos dentales |
| Camas y Casas | Camas, transportadoras |

## Métodos de Pago

### Stripe (En línea)
- Tarjetas de crédito/débito
- Visa, Mastercard, Amex
- **Comisión:** 3.6% + $3 MXN

### OXXO (Efectivo)
- Cliente recibe voucher
- Paga en cualquier OXXO
- **Vigencia:** 72 horas
- **Comisión:** 3.6% + $3 MXN

## Flujo de Compra

```
1. Usuario navega catálogo
         │
         ▼
2. Agrega productos al carrito
         │
         ▼
3. Revisa carrito
         │
         ▼
4. Inicia checkout
         │
         ├─────────────────────┐
         ▼                     ▼
5a. Pago con tarjeta     5b. Pago OXXO
    (inmediato)              (genera voucher)
         │                     │
         ▼                     ▼
6. Confirmación          Espera pago
   de pedido                   │
         │                     ▼
         ▼              Pago confirmado
7. Preparación               │
   de pedido                  ▼
         │              6. Confirmación
         ▼
8. Entrega o recogida
```

## Ejemplo Conversación con IA

```
Usuario: Necesito comprar croquetas para mi perro

IA: ¡Claro! Te ayudo a encontrar el alimento
perfecto para tu mascota. 🐕

Veo que tienes a "Max" (Golden Retriever, 3 años).
¿Qué marca de croquetas usa actualmente?

Usuario: Usa Royal Canin

IA: Excelente elección. Tenemos disponible:

🦴 **Royal Canin Golden Retriever Adult**
   Bolsa 13.6 kg - $1,850 MXN
   ⭐ Recomendado para Max

🦴 **Royal Canin Medium Adult**
   Bolsa 10 kg - $1,250 MXN

🦴 **Royal Canin Medium Adult**
   Bolsa 4 kg - $580 MXN

¿Cuál te gustaría agregar al carrito?

Usuario: La bolsa grande de Golden

IA: ✅ Agregado al carrito:
   Royal Canin Golden Retriever 13.6kg - $1,850

   Tu carrito: 1 producto - $1,850 MXN

   ¿Deseas continuar comprando o ir al checkout?
```
