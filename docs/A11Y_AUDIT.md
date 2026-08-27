# Accessibility audit (WCAG 2.2 AA target)

## Status: Phase 1–6 implementation
Accessibility is an acceptance criterion, not a cleanup task. The following are built into the Expo client and API:

## Implemented
- **Screen-reader semantics:** Every interactive element carries `accessibilityLabel`, `accessibilityRole` (button, header, alert), and logical grouping.
- **Touch targets:** All buttons are ≥44pt (`minHeight: 48` for primary actions).
- **Dynamic/large text:** Uses React Native's default scaling; no fixed clipping containers in core screens.
- **Color independence:** Status is never communicated by color alone — text labels ("completed"/"planned", "estimate"/"confirmed") accompany any color.
- **No drag-only interactions:** Reordering uses buttons, not drag.
- **Reduced motion:** Native `AccessibilityInfo` respected for animations (GSAP not yet introduced).
- **Error/loading/empty/offline states:** Every screen has explicit `ActivityIndicator`, empty-state text, and `accessibilityRole="alert"` for errors.
- **High contrast & dark mode:** High-contrast palette (`#0B3D2E` on white); dark-mode tokens prepared.
- **Keyboard accessibility (Expo web):** Standard focusable components; labels ensure operable without a screen reader.
- **Plain language in Today mode:** Short actions ("Departed", "Arrived", "Emergency pause").
- **Confirmation for destructive/schedule-changing actions:** Proposals require explicit Owner/Editor approval.
- **Copy/open actions:** Addresses, phone numbers, reservation numbers, and navigation are tappable/copyable.

## Known gaps (deferred)
- Full screen-reader walkthrough on every screen not yet QA'd with VoiceOver/TalkBack.
- Reduced-motion toggles not yet wired to a user preference.
- Tablet layout optimizations (orientation flexibility) are scaffolded but not fully tuned.
- Automated a11y testing (e.g., axe) not yet integrated into CI.

## Recommendation
Run a manual screen-reader pass on iOS (VoiceOver) and Android (TalkBack) before release, and add automated a11y linting to CI.
