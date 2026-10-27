# Notes

## Eval fields left out for now

### Per-posting omissions

- In posting_1.txt the `location` field was left off because the only stated location is "Remote" plus a list of excluded US states. The model could reasonably return "Remote", "United States", "Remote (US)", or `null` (treating "Remote" as a work mode, not a location).
- In posting_2.txt the `location` field was left off because "Remote - United States" could come back verbatim or as "United States" / "Remote (US)". Both are correct, but exact match would fail one of them.
- In posting_3.txt the `location` field was left off because it lists three cities (Colorado Springs, CO; Aurora, CO; Los Angeles, CA) with no canonical order or separator. The qualifications also contradict the header by saying El Segundo, CA instead of Los Angeles.
- In posting_3.txt the `discipline` field was left off because the title is just "Software Engineer III" and the qualifications ask for "experience with both frontend and backend" (Spring Boot plus React/Vue/Redux). "backend" and "fullstack" are both defensible.
- In posting_4.txt the `location` field was left off because it lists four cities (San Francisco, CA; New York City, NY; Sunnyvale, CA; Seattle, WA). Order, separators, and abbreviations would all have to match exactly.
- In posting_5.txt the `work_mode` field was left off because the role is "available either in an office or a remote location." Office-assigned staff are hybrid (50% in office), but remote staff are fully remote, so "hybrid" and "remote" are both defensible.
- In posting_5.txt the `salary_currency` field was left off because the posting writes "CA$172,000 - CA$258,000" and the schema doesn't require ISO codes. The model could return "CAD" or "CA$".

### required_skills
