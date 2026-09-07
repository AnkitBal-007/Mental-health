# Design guidelines

## Tone

This system deals with victims of serious trauma (rape, murder, caste-based violence, witness intimidation). The UI must never feel clinical-cold or, conversely, gamified. Calm, clear, low-stimulus design throughout — this applies to both the victim-facing chatbot and the official-facing dashboard.

## Victim-facing chatbot

- Conversational, warm, non-judgmental phrasing — never diagnostic or alarming language ("How have you been feeling since we last talked?" not "Rate your distress level 1–10").
- No visible score, risk label, or alert status shown to the victim — that information is for counsellors/officials only. Showing a victim their own "distress score" could cause harm or distort their answers.
- Support English and Hindi at minimum; language selection up front, not buried in settings.
- Keep interactions short — a check-in should take under 2 minutes to reduce dropout.
- Always include a visible, easy way to reach a human (helpline number) directly from the chat.

## Official-facing dashboard

### Layout

- Victim list as the default landing view after login — sortable/filterable by risk level and district, not a generic homepage.
- Color-coded risk badges: use a consistent, colorblind-safe scale (e.g. green/amber/red) rather than relying on color alone — pair with a text label ("Low" / "Moderate" / "High").
- Victim detail view always shows three things together: the trend chart, the factor breakdown, and the recommended interventions — never the score in isolation.
- Alerts feed is prioritized by recency and severity, with a clear "assign to counsellor" action on each row.

### Explainability panel

- Show factors as short, plain-language statements with their point contribution (e.g. "Declining sentiment trend: +18", "Missed last 2 check-ins: +12") — not raw model internals or feature names.
- Order factors by contribution size, largest first.

### Role scoping

- District users see only their district's victims.
- State users see state-aggregated data with drill-down into districts.
- National users see the highest-level aggregate with drill-down into states.
- Never let a lower-privilege role see data outside its scope, even in a demo.

### Visual identity

- Calm, low-saturation palette (muted blues/teals/greys) with the risk-badge colors as the only high-saturation accents — the interface itself should not visually amplify urgency.
- Clear typography hierarchy; avoid dense data-table walls without whitespace.
- Every screen with synthetic demo data carries a small, visible "demo data" label so it's never mistaken for real victim information.

## Accessibility

- Sufficient color contrast for all text and badges.
- All interactive elements keyboard-navigable.
- Chatbot and dashboard both usable at standard mobile viewport widths, since access may be via a basic smartphone browser.
