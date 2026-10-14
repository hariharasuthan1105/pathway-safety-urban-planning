```markdown
# Incident Triage Sandbox

A standalone, dependency-free educational demo for organizing
illustrative urban-safety incidents by priority.

## Features

- Add and remove incidents.
- Record incident severity and likelihood.
- Select a band representing the population potentially affected.
- Calculate illustrative priority scores.
- Sort incidents by score.
- Filter the queue by priority.
- View dashboard statistics.
- Export incidents to CSV.
- Use a responsive interface on desktop and mobile.

## Run locally

1. Open this folder in VS Code.
2. Open `index.html` in a web browser.
3. Add incidents and explore the queue.

No npm installation, backend, database, or external dependency is
required.

## Scoring model

Score = Severity × Likelihood × Impact

Each factor ranges from 1 to 5. The maximum score is 125.

- High priority: 60 or above
- Medium priority: 25–59
- Low priority: below 25

The impact factor is a simple numeric representation of the selected
population band. It is not a statistically validated measure.

## Important limitation

This tool is for demonstration and learning only. Its score is not a
validated safety assessment, emergency dispatch system, or substitute
for professional judgment. Do not use it to make real-world emergency
decisions.

## Project isolation

This tool is located under `tools/incident-triage-sandbox/`. It does
not modify the existing frontend, backend, application dependencies,
or deployment configuration.
```
