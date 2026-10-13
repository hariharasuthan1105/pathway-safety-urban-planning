# Implementation decisions

1. Reconcile with merged PR #3 instead of duplicating its source changes.
2. Keep HashRouter and the Pages repository subpath. Publishing occurs after
   owner-approved merge to main; pushing this feature branch cannot publish.
3. Backend validation is strict origin-only HTTPS (no trailing slash). Four
   health attempts each time out after 15 seconds, with three 5-second pauses:
   at most approximately 75 seconds before publication is blocked.
4. Authentication design review: third-party cookies cannot be assumed to work
   on Pages → Render. Existing API already returns bearer tokens, but logout
   currently ignores them. Preserve SQLite and cookie compatibility. Before any
   transport change, test cross-browser behavior and document refresh/expiry
   implications. Hosted cross-site behavior requires independent verification.
5. Existing illustrative geometry is reusable. Do not replace it or assert
   simulated actors represent real tracked assets. Performance must be measured.
6. Do not change Render configuration or repository settings. No secrets belong
   in VITE variables, artifacts or documentation. No ZIP unless requested.
