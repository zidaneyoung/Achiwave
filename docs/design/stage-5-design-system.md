# Stage 5 mobile design system

## Brand and reference direction

Achiwave is a focused gamified-productivity application with a restrained,
native Android character. The original direction and read-only inspiration
workflow are recorded in [Stage 5 visual direction](stage-5-visual-direction.md).
Progress hierarchy and clear status language provide the game influence; copied
layouts, artwork, ornamental HUD elements, and constant glow are prohibited.

## Semantic colour and themes

Components consume semantic names from `src/theme/colors.ts`; raw colour values
belong only in that palette. Both themes expose background, surface, elevated,
pressed, disabled, foreground, muted, accent, action, border, focus, overlay,
success, warning, error, danger, and information roles.

- Dark: navy `#171A21` foundation, `#1B2838` surface, `#2A475E` elevated
  surface, `#66C0F4` brand accent, and `#C7D5E0` foreground.
- Light: neutral light backgrounds with navy foreground and action colours.
  Cyan remains a brand accent and is not small text on white.
- Theme resolution is centralized, follows the Android system setting, and
  defaults to dark only while the system value is unavailable. Stage 4 has no
  explicit theme preference, so no unsupported preference is invented.
- Status always includes text or another non-colour cue. Executable checks
  enforce 4.5:1 for normal text pairs and 3:1 for focus indicators.

## Typography

`AppText` and the typography tokens use the Android-compatible system font and
preserve native font scaling.

| Variant | Size / line height | Use |
| --- | --- | --- |
| Display | 32 / 38 | Primary destination heading |
| Heading 1 | 28 / 34 | Screen or modal heading |
| Heading 2 | 22 / 28 | Section heading |
| Title | 18 / 24 | Card and list title |
| Body | 16 / 24 | Content and instructions |
| Label | 14 / 20 | Controls, fields, and status |
| Caption | 12 / 16 | Secondary metadata |

Text may wrap, reflow, or scroll. Required copy and actions must never depend on
truncation, fixed-height text, or disabled font scaling.

## Spacing, sizing, radii, and elevation

Spacing uses a 4 dp unit: 4, 8, 12, 16, 24, 32, 40, and 48. Reusable sizing
tokens define a 48 dp minimum target, 52 dp form control, 320 x 568 dp minimum
viewport, and readable content measure. Radii are 8, 12, 16, or pill. Borders
are 1 dp normally and 2 dp for selected/focused emphasis. Prefer borders and
surface changes; low elevation is reserved for a genuinely raised layer.

## Icons and navigation

Material Community Icons is the single icon family. Outlined icons are the
default; a filled silhouette plus label and selected surface identifies the
active tab. Decorative icons are hidden from accessibility services. Every
icon-only action has an accessible name and at least a 48 dp target.

Authenticated roots are Home, Campaigns, Progress, and Profile in bottom tabs.
Stacks handle drill-down, modals handle temporary focused work, and native
navigation owns Android back behavior. Authentication resolution guards all
protected navigation. Stage 5 shells do not expose campaign or progression data.

## Component contracts

- Buttons: primary, secondary, ghost, destructive, and icon-only; pressed,
  focused, disabled, and loading states; loading prevents repeat submission.
- Inputs and selectors: persistent label, value/placeholder, helper or error,
  required and disabled states, secure entry, current selector value.
- Cards and list items: static or interactive, readable title/metadata/status,
  optional leading/trailing content, restrained elevation, no nested activation.
- Dialogs and sheets: labelled focused surface, explicit dismissal, safe
  destructive confirmation, Android back dismissal, scrollable long content.
- Progress: determinate, indeterminate, compact, and labelled; clamped values,
  accessibility value, and static reduced-motion alternative.
- Badges: compact and regular semantic statuses pairing text with shape/icon.

The development-only component showcase demonstrates every variant, disabled
state, long label, theme, and representative application state without becoming
a production tab.

## Application states and feedback

Skeletons approximate final text/card/list/profile layouts and become static
when motion is reduced. Empty states distinguish first use, filters, completion,
and unavailable content. Errors can be inline, section, validation,
authentication, recoverable network, or full-screen and never expose internal
details. Offline/synchronization labels distinguish only states confirmed by the
current client; they do not imply a Stage 7 queue or successful synchronization.
Android press feedback is immediate, disabled controls are silent, and haptics
are reserved for meaningful actions when the Stage 4 preference permits them.

## Accessibility behaviour

Controls expose name, role, state, and value where applicable. Reading order is
logical, decorative content is hidden, and material loading/error/offline/modal
changes are announced without repetition. Layout verification covers 320 x 568,
360 x 640, and 412 x 915 dp at font scales 1.0, 1.3, 1.5, and 2.0. Content must
wrap or scroll while controls retain 48 x 48 dp targets and separation.

Reduced motion resolves in this order: `reduce` always reduces, `allow` permits
nonessential motion, and `system` follows the operating-system setting. Reduced
mode disables shimmer, decorative loops, parallax, and large movement while
preserving immediate state changes and progress information.

## Deferred work

Stage 6 campaign creation, lists, quests, completion, progression, rewards, and
all production domain data remain deferred. Stage 5 also does not introduce an
offline mutation/synchronization engine, notification delivery, evidence upload,
or authoritative mobile progression.
