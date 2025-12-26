# B-084: Logo and Text Both Displaying in Navigation

**Severity**: Minor (UI/UX)
**Affected Component**: templates/components/header.html
**Discovered**: 2025-12-26

## Bug Description

In the navigation bar, both the logo image placeholder AND the "Pet-Friendly" text are displaying simultaneously. It should be one or the other - if the logo image loads successfully, show only the image; if it fails to load, show the text as a fallback.

## Steps to Reproduce

1. Visit any page on the site
2. Look at the navigation bar in the top-left corner
3. Observe: Both an image placeholder AND "Pet-Friendly" text are visible

## Expected Behavior

- If logo image exists and loads → Show only the logo image
- If logo image fails to load → Show only the "Pet-Friendly" text fallback

## Actual Behavior

Both the logo image (or placeholder) AND the text are shown together.

## Root Cause

In `templates/components/header.html`, lines 7-10:
```html
<img src="{% static 'images/logo.png' %}" alt="Pet-Friendly Vet" class="h-10 w-auto">
<span class="ml-2 text-xl font-bold text-primary-500 hidden sm:block">Pet-Friendly</span>
```

Both elements are rendered unconditionally without any logic to show one or the other.

## Proposed Fix

Use JavaScript/Alpine.js to detect image load success/failure and toggle visibility accordingly.

## Files Affected

- `templates/components/header.html`

## Definition of Done

- [x] Logo shows alone when image loads successfully
- [x] Text fallback shows alone when image fails to load
- [x] Works on both desktop and mobile
- [x] No broken image icon visible when logo is missing

## Implementation

Used Alpine.js to track image load state:
- `x-data="{ logoLoaded: false }"` - tracks whether image loaded
- `@load="logoLoaded = true"` - set true when image loads successfully
- `@error="logoLoaded = false"` - keep false when image fails
- `x-show="logoLoaded"` on image - only show if loaded
- `x-show="!logoLoaded"` on text - only show if NOT loaded
- `x-cloak` on image - prevent flash before Alpine initializes
