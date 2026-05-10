# Design Token System

Design tokens for a Flutter mobile app, structured for Token Studio (Figma) import and Flutter code generation.

## Golden Rule: Reference Chain

```
Brand → Alias → Component
```

- **Brand** contains ONLY raw hex values. No references.
- **Alias** references ONLY Brand tokens. Never raw hex.
- **Component** references ONLY Alias tokens. Never Brand. Never raw hex.

No layer may skip its parent. If a value doesn't exist in the parent layer, add it there first.

## Token Studio Format

Every leaf token must have this structure:

```json
{
  "$extensions": {
    "com.figma.scopes": ["ALL_SCOPES"],
    "com.figma.hiddenFromPublishing": false
  },
  "value": "#hex or {reference}",
  "type": "color"
}
```

### Type mapping

| Category         | `type` value        |
|------------------|---------------------|
| Colors           | `color`             |
| Spacing / layout | `spacing`           |
| Component sizes  | `sizing`            |
| Border radius    | `borderRadius`      |
| Border width     | `borderWidth`       |
| Opacity          | `opacity`           |
| Font size        | `fontSizes`         |
| Line height      | `lineHeights`       |
| Letter spacing   | `letterSpacing`     |
| Paragraph spacing| `paragraphSpacing`  |
| Generic numbers  | `number`            |
| Text values      | `text`              |

## File Structure

### Single import file

`tokens_to_figma.json` — import this one file into Token Studio. Top-level keys are token set names.

### Source files (for reference / code generation)

| File | Purpose |
|------|---------|
| `theme_colors.json` | Structured color tokens (primitive → semantic → theme) |
| `theme_dimension.json` | Spacing, sizing, radius, border, opacity, elevation, animation |
| `theme_typography.json` | Font families, weights, text style scale with mobile/tablet |

## Token Sets

### Colors

| Set | Role | Contains |
|-----|------|----------|
| `Brand` | Raw palette | `blue`, `gray`, `green`, `red`, `amber`, `teal`, `slate`, `overlay`, `core` — only hex values |
| `Alias` | Semantic roles | `primary`→blue, `neutral`→gray, `base`→slate, `error`→red, `warning`→amber, `success`→green, `information`→teal, `overlay`, `white`, `black`, `transparent` |
| `Component/Light` | Light theme | References Alias only — background, surface, content, action, input, border, focus |
| `Component/Dark` | Dark theme | Same structure as Light, different Alias references |

### Dimensions

| Set | Role | Contains |
|-----|------|----------|
| `Dimension/Mobile` | Mobile dimensions | spacing, layout, component sizes, radius, border, opacity, elevation |
| `Dimension/Tablet` | Tablet dimensions | Same groups, tablet-scaled values |

### Typography

| Set | Role | Contains |
|-----|------|----------|
| `Typography/Mobile` | Mobile type scale | 19 text styles × (fontSize, lineHeight, letterSpacing, paragraphSpacing) |
| `Typography/Tablet` | Tablet type scale | Same styles, tablet-scaled values |

## Token Set Naming Rules

- Use `/` in set names for folder grouping in Token Studio sidebar: `Component/Light`, `Dimension/Mobile`
- Do NOT use `/Value` suffix — `Brand` not `Brand/Value`
- Sets that share a prefix group into a folder: `Dimension/Mobile` + `Dimension/Tablet` → "Dimension" folder

## Figma Variable Collections (via $themes)

Token sets map to Figma Variable Collections through `$themes`. Each theme group becomes one collection, each theme becomes a mode.

| Collection | Modes | Enabled sets |
|------------|-------|-------------|
| **Component** | Light, Dark | `Component/Light` or `Component/Dark` (Brand + Alias as source) |
| **Dimension** | Mobile, Tablet | `Dimension/Mobile` or `Dimension/Tablet` |
| **Typography** | Mobile, Tablet | `Typography/Mobile` or `Typography/Tablet` |

### Theme configuration

```json
{
  "$themes": [
    {
      "id": "unique-id",
      "name": "Light",
      "group": "Component",
      "selectedTokenSets": {
        "Brand": "source",
        "Alias": "source",
        "Component/Light": "enabled"
      }
    }
  ]
}
```

- `"source"` — used for reference resolution only, does NOT create a separate Figma collection
- `"enabled"` — tokens are exported to the Figma collection as the specified mode
- Brand and Alias are always `"source"` — they power the reference chain but don't become standalone collections

### Non-responsive values

Tokens that don't change between modes (spacing base scale, radius, border widths, opacity, elevation) are duplicated into BOTH mode sets (e.g., `Dimension/Mobile` and `Dimension/Tablet`). This ensures one Figma collection with a mode switcher instead of separate orphan collections.

## Color Architecture

### Brand layer

Raw color palette. 8 families + core tokens.

| Family | Shades | Purpose |
|--------|--------|---------|
| `blue` | 50–1200 | Primary / brand color |
| `gray` | 50–1200 | Pure neutral for text, icons, borders |
| `slate` | 50–950 | Blue-tinted neutral for backgrounds, dark surfaces |
| `green` | 50–1300 | Success states |
| `red` | 50–1300 | Error / destructive states |
| `amber` | 50–1300 | Warning states (distinct from red) |
| `teal` | 50–1200 | Information states (distinct from blue) |
| `overlay` | 4 values | Alpha colors (black-48, black-32, dark-12, light-12) |
| `core` | 3 values | white, black, transparent |

Shades 1300 are very dark tints used for dark mode surface backgrounds.

### Alias layer

Maps semantic role names to Brand references. Two naming patterns:

**Shade pass-through** — full palette access:
```
primary.500 → {blue.500}
neutral.900 → {gray.900}
base.800    → {slate.800}
```

**Semantic shortcuts** — named intent:
```
primary.subtle   → {blue.50}     (tint background)
primary.muted    → {blue.200}    (soft background, badge/chip fill)
primary.default  → {blue.500}    (main color)
primary.emphasis → {blue.700}    (pressed / darker)
primary.on       → {core.white}  (text ON a primary-colored surface)
```

Exception: `warning.on → {amber.900}` (dark text because amber backgrounds are too light for white).

### Component layer

Theme-aware tokens for direct use in UI components. Grouped by function:

- **background** — page hierarchy: `page`, `subtle`, `elevated`, `overlay`, `scrim`
- **surface** — component fills: `default`, `subtle`, `raised`, + status variants
- **content** — text/icon colors: `primary`, `secondary`, `tertiary`, `disabled`, `inverse`, `onX`, `status.*`
- **action** — interactive fills: `primary`, `secondary`, `destructive`, `ghost` × `default`, `pressed`, `disabled`
- **input** — form elements: `background.*`, `border.*`, `placeholder`, `text`
- **border** — decorative borders: `subtle`, `default`, `strong`
- **focus** — accessibility: `ring`, `ringOffset`

## Mobile App Constraints

This system is designed for a mobile Flutter app:

- **No hover states** — only `default`, `pressed`, `disabled` for actions. Hover is a pointer/cursor concept.
- **No z-index** — Flutter uses Stack/Overlay ordering, not numeric z-index.
- **No CSS font fallbacks** — Flutter loads fonts directly, no fallback chains.
- **No desktop breakpoint** — only `mobile` (0dp) and `tablet` (600dp).
- **Dark mode page background** — `#0f172a` (dark navy), not pure black. Avoids OLED smearing.

## Adding New Tokens

### Adding a new color

1. Add the raw hex to `Brand` under the appropriate family
2. Add an alias reference in `Alias` under the appropriate role: `{family.shade}`
3. Reference the alias in `Component/Light` and/or `Component/Dark`: `{role.shade}`
4. Never skip a layer

### Adding a new component dimension

1. Add the value to BOTH `Dimension/Mobile` and `Dimension/Tablet` under the component group
2. Use `"type": "sizing"` for component sizes, `"type": "spacing"` for gaps/padding

### Adding a new text style

1. Add the style group to BOTH `Typography/Mobile` and `Typography/Tablet`
2. Each style has: `fontSize` (fontSizes), `lineHeight` (lineHeights), `letterSpacing` (letterSpacing), `paragraphSpacing` (paragraphSpacing)

## Validation Checklist

Before importing into Token Studio:

- [ ] Brand tokens contain ONLY raw hex values
- [ ] Alias tokens reference ONLY Brand paths that exist
- [ ] Component tokens reference ONLY Alias paths that exist
- [ ] Zero raw hex in Alias or Component layers
- [ ] No standalone leaf tokens at set root level — nest inside groups
- [ ] Every token has correct `type` field
- [ ] `$themes` groups define proper `source` / `enabled` mapping
- [ ] Non-responsive values are duplicated in both mode sets
- [ ] `$metadata.tokenSetOrder` lists all sets
# figma_design_system_guide
