# Blike Moomberg's Calendar

An independent interview practice exercise reconstructed from the supplied workshop screenshots. It is not Bloomberg's original code or an official interview assessment. The visible package layout, SQLite schema fields, request submission flow, and deterministic scorer have been closely mirrored; unseen behavior and tickets are original.

Open **candidate-pack/** as your editor workspace and start with its README. There are exactly two deliberately planted behavioral defects and one unimplemented function. No solution is included inside the candidate pack.

```text
blike-calendar/
├── candidate-pack/
│   ├── blike_calendar/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── directory.py
│   │   ├── models.py
│   │   ├── scheduler.py
│   │   ├── scorer.py
│   │   └── service.py
│   ├── tests/
│   ├── tickets/
│   ├── README.md
│   └── SETUP.md
├── interviewer-materials/        # Spoilers: open only after your attempt
└── blike-calendar-candidate-pack.zip
```

The ZIP contains only candidate materials. For an AI-assisted mock interview, give your assistant access to that ZIP or candidate-pack only. Ask it to act as your interviewer, discuss one ticket at a time, and withhold fixes unless explicitly requested.

Suggested session: 5–10 minutes exploring, 30–40 minutes on one ticket, then 10 minutes explaining tests, complexity, and the final diff. Completing every ticket is optional; the repository contains all three for repeated practice. These timings are practice suggestions, not a claim about Bloomberg's interview process.
