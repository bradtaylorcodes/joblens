# Notes

## Eval fields left out for now

`evals/cases.json` checks `company`, `work_mode`, `salary_min`, `salary_max`, `salary_currency`, and `discipline`. Two schema fields are deliberately not checked yet.

### location

- **No canonical format.** `location` is a free-form string, so the right answer for multi-city postings is ambiguous: DoorDash lists four cities, and Rise8 lists three. The order, separators, and abbreviations ("CA" vs "California") would all have to match exactly.
- **Postings contradict themselves.** Rise8's header says Los Angeles, CA, but its qualifications say El Segundo, CA.
- **Unclear when it should be null.** Tactacam says only "Remote" but excludes some US states, which suggests "United States". Stripe says only "primary location", and the CA$ salary suggests Canada but no city is named. Whether these should be `null` or an inferred region is still a product decision.
- **Needs a looser comparison.** Exact match would fail correct outputs. Checking this field properly needs normalization or fuzzy/LLM-graded matching, which the eval doesn't support yet.

### required_skills

- **Open-ended list.** No posting has a single correct set of skills. The model could reasonably include or leave out soft skills, degrees, clearances ("TS/SCI"), or practices ("TDD").
- **Required vs preferred is blurry.** Stripe puts React under preferred qualifications, Honeycomb marks OpenTelemetry as a bonus, and DoorDash names Postgres/Redis/etc. only as examples.
- **"Or" lists.** Rise8 asks for "PHP, Kotlin, Java, or Javascript". It's unclear whether that should become one entry, four entries, or nothing.
- **Naming and granularity vary.** Examples: "React" vs "React.JS", "AWS CDK" vs "AWS Cloud Development Kit", "REST APIs" vs "RESTful API design".
- **Needs set-based scoring.** A useful check would score precision/recall against a must-include core, not compare lists exactly. That's more eval machinery than the current exact-match cases.
