---
name: Nexus
colors:
  surface: '#18181b'
  surface-dim: '#131315'
  surface-bright: '#39393b'
  surface-container-lowest: '#0e0e10'
  surface-container-low: '#1c1b1d'
  surface-container: '#201f22'
  surface-container-high: '#2a2a2c'
  surface-container-highest: '#353437'
  on-surface: '#e5e1e4'
  on-surface-variant: '#bbcabf'
  inverse-surface: '#e5e1e4'
  inverse-on-surface: '#313032'
  outline: '#86948a'
  outline-variant: '#3c4a42'
  surface-tint: '#4edea3'
  primary: '#4edea3'
  on-primary: '#003824'
  primary-container: '#10b981'
  on-primary-container: '#00422b'
  inverse-primary: '#006c49'
  secondary: '#c6c6cf'
  on-secondary: '#2f3037'
  secondary-container: '#45464e'
  on-secondary-container: '#b4b4bd'
  tertiary: '#ffb3af'
  on-tertiary: '#650911'
  tertiary-container: '#fc7c78'
  on-tertiary-container: '#711419'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#6ffbbe'
  primary-fixed-dim: '#4edea3'
  on-primary-fixed: '#002113'
  on-primary-fixed-variant: '#005236'
  secondary-fixed: '#e2e1eb'
  secondary-fixed-dim: '#c6c6cf'
  on-secondary-fixed: '#1a1b22'
  on-secondary-fixed-variant: '#45464e'
  tertiary-fixed: '#ffdad7'
  tertiary-fixed-dim: '#ffb3af'
  on-tertiary-fixed: '#410005'
  on-tertiary-fixed-variant: '#842225'
  background: '#131315'
  on-background: '#e5e1e4'
  surface-variant: '#353437'
  border: '#27272a'
  text-primary: '#ffffff'
  text-secondary: '#a1a1aa'
typography:
  headline-lg:
    fontFamily: Geist
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-lg-mobile:
    fontFamily: Geist
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Geist
    fontSize: 20px
    fontWeight: '600'
    lineHeight: '1.4'
    letterSpacing: -0.01em
  body-lg:
    fontFamily: Geist
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: '0'
  body-md:
    fontFamily: Geist
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: '0'
  label-md:
    fontFamily: Geist
    fontSize: 12px
    fontWeight: '500'
    lineHeight: '1'
    letterSpacing: 0.02em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 4px
  gutter: 16px
  margin-mobile: 16px
  margin-desktop: 32px
  max-width: 1280px
---

## Brand & Style
This design system centers on a "Digital Studio" aesthetic—fusing the high-performance feel of developer tools with the accessibility required for a student-centric platform. The personality is professional yet energetic, utilizing high-contrast dark surfaces to eliminate visual noise and focus the user's attention on productivity.

The design style is **Minimalist** with a technical edge. It prioritizes generous whitespace to prevent the dark interface from feeling cramped, while utilizing precise, vibrant accents to guide the eyes. The interaction model is snappy and fluid, evoking a sense of speed and modern intelligence.

## Colors
The palette is built on a "True Dark" foundation. The background uses a near-black neutral to maintain OLED-friendly depth, while surfaces are layered using subtle zinc-toned grays to create clear visual hierarchy without the need for heavy shadows.

Emerald Green serves as the high-energy action color, reserved strictly for primary buttons, active states, and critical progress indicators. Text contrast is kept intentionally high to ensure legibility during long study or coding sessions, with secondary text providing a clear step down in the information hierarchy.

## Typography
Geist Sans is used exclusively across all levels to maintain a cohesive, technical character. Headlines utilize a semi-bold weight and tighter letter-spacing to create a strong, authoritative presence. 

Body text is optimized for readability with a slightly increased line-height. Labels and small metadata should use a medium weight to ensure they don't disappear against the dark background. On mobile devices, headline sizes scale down to prevent awkward word-wrapping in narrow containers.

## Layout & Spacing
The layout follows a 12-column fluid grid system for desktop, transitioning to a 4-column system for mobile. Spacing is based on a 4px base unit to ensure mathematical precision in all component dimensions.

The philosophy is "Airy Architecture"—meaning margins and paddings are generous to counteract the heaviness of the dark theme. Elements should be grouped into distinct card-based modules, separated by wide gutters. Layout reflows should focus on stacking content vertically on mobile while maintaining the same 16px safe-area margins.

## Elevation & Depth
In this design system, depth is achieved through **Tonal Layering** and **Low-Contrast Outlines** rather than traditional shadows. 

1. **Base Level:** The background layer (#09090b).
2. **Surface Level:** Elevated cards and containers use #18181b with a 1px border of #27272a to define edges.
3. **Floating Level:** Modals or menus may use a slightly lighter surface (#27272a) with a very soft, high-spread ambient shadow (10% opacity black) to suggest they are sitting above the content.

This "border-first" approach ensures that the UI feels sharp and modern, avoiding the muddy look that shadows can sometimes create on dark backgrounds.

## Shapes
The shape language is defined by "Rounded-XL" corners for major containers, creating a friendly and approachable contrast to the professional dark theme. 

- **Cards & Modals:** Use the primary `rounded-xl` (1.5rem / 24px) setting.
- **Buttons & Inputs:** Use the standard `rounded-lg` (1rem / 16px) for a cohesive but slightly more compact feel.
- **Selections:** Indicators like active tabs or pill-tags use a fully rounded (pill) shape to distinguish them from structural containers.

## Components
- **Buttons:** Primary buttons use a solid Emerald Green fill with white text. Secondary buttons use a transparent background with a #27272a border, shifting to a subtle gray hover state.
- **Cards:** Cards are the primary organizational unit. They feature the #18181b background and the 1px #27272a border.
- **Input Fields:** Use a #18181b fill and a #27272a border. On focus, the border transitions to Emerald Green with a subtle glow (2px outer stroke).
- **Chips & Tags:** Use a low-opacity version of the primary color (Emerald Green at 15% opacity) with solid green text for high visibility without overwhelming the layout.
- **Lists:** Items are separated by subtle horizontal rules (#27272a). Interactive list items should feature a subtle background highlight on hover.
- **Navigation:** Vertical sidebars use the base background color, with active links indicated by a vertical Emerald Green line and semi-bold text.