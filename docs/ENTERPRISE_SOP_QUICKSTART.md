# Enterprise SOP Quick Start

## What v16.0 adds

- Role-based SOP catalog with Published and Pending HR approval states.
- Required knowledge check and version acknowledgement.
- 1/7/30-day new-starter journey.
- Attendance records, monthly summary, CSV import/export, and correction requests.
- Backend audit events for SOP acknowledgements, attendance imports, and corrections.
- Multilingual Traditional Chinese, English, and Thai interface.
- RAG chatbot that can cite published system SOPs and must not invent unpublished company policy.

## Safe rollout order

1. HR, EHS, QA, and IT replace every `HR-DRAFT` template with approved documents.
2. Record document owner, version, effective date, site, role scope, and review date.
3. Build the RAG index and test answers in all three languages.
4. Import employees, supervisor/department mapping, Saturday groups, and attendance data.
5. Disable demo mode and shared passwords.
6. Deploy FastAPI and PostgreSQL outside GitHub Pages, configure HTTPS, CORS, secrets, backups, and access logs.
7. Pilot with one department before company-wide release.

## GitHub Pages limitation

Pages can host the front-end demonstration and automatically updated holiday JSON. Real attendance, acknowledgements, approvals, employee records, and audit logs require the FastAPI/PostgreSQL backend.
