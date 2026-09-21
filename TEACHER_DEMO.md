# PhoenixML – Teacher Demo Script (Using Only Current Project Files)

## 1. Project Goal

This project is a documentation-based demonstration of PhoenixML, an intelligent MLOps decision-support platform for monitoring and maintaining deployed machine learning models, with a focus on spam email detection.

The core problem described in [FINAL_REPORT.md](FINAL_REPORT.md) is that models often degrade silently in production because of data drift, concept drift, and shifting user behavior. Traditional monitoring tools often only raise alerts without explaining the issue or recommending an action.

PhoenixML addresses this by combining:
- telemetry ingestion
- health scoring
- drift detection
- explainability
- human-in-the-loop decision support

---

## 2. What is in the project files

The project contains the following design and report files:
- [FINAL_REPORT.md](FINAL_REPORT.md) – complete project report
- [01-literature-review.md](01-literature-review.md) – background and review of spam detection and MLOps
- [02-decision-engine.md](02-decision-engine.md) – AIMD decision engine design
- [03-architecture.md](03-architecture.md) – system architecture
- [04-srs.md](04-srs.md) – requirements specification
- [05-sdd.md](05-sdd.md) – software design document
- [06-database-design.md](06-database-design.md) – database design
- [07-api-design.md](07-api-design.md) – API design

These files are enough to explain the system conceptually and present a strong project demonstration even without the actual application source code.

---

## 3. Demo narrative for the teacher

### Slide 1: Problem statement

"Machine learning models often work well during training but degrade in real-world production due to changing data patterns. In spam detection, new attack patterns, changed vocabulary, and evolving user behavior can cause silent performance collapse."

Evidence: [FINAL_REPORT.md](FINAL_REPORT.md) and [01-literature-review.md](01-literature-review.md)

### Slide 2: Proposed solution

"PhoenixML is an MLOps decision-support platform that continuously monitors deployed models, evaluates health, detects drift, and recommends actions instead of letting the system fail silently."

Evidence: [03-architecture.md](03-architecture.md) and [FINAL_REPORT.md](FINAL_REPORT.md)

### Slide 3: Architecture overview

The system has a layered architecture:
- user interface
- FastAPI backend
- monitoring service
- drift detection module
- health assessment module
- AIMD decision engine
- PostgreSQL database

This architecture is presented in [03-architecture.md](03-architecture.md).

### Slide 4: How the decision engine works

The AIMD engine receives monitoring metrics, drift detection results, and health assessments, then generates recommendations such as:
- CONTINUE_MONITORING
- INCREASED_MONITORING
- DATA_COLLECTION
- RETRAIN
- ROLLBACK
- HUMAN_REVIEW

The decision engine is explained in [02-decision-engine.md](02-decision-engine.md).

### Slide 5: Human-in-the-loop safety

A major design principle is that model actions are not automated without human approval.

The report specifically states that every recommendation has `requires_human_approval = True`, and the workflow uses a state machine with:
- PENDING
- APPROVED
- REJECTED

This is presented in [FINAL_REPORT.md](FINAL_REPORT.md) and [02-decision-engine.md](02-decision-engine.md).

### Slide 6: Example operational scenario

The report includes a demonstration using a registered model named SpamGuard-v1.

Healthy observation:
- F1 Score = 0.92
- Health Score = 92.3/100
- Status = HEALTHY

Degraded observation:
- F1 Score = 0.66
- Health Score = 66.7/100
- Status = WARNING

The AIMD engine then recommends HUMAN_REVIEW for investigation and approval.

Evidence: [FINAL_REPORT.md](FINAL_REPORT.md)

### Slide 7: Why this is useful

This project is valuable because it does not merely monitor a model; it explains the issue and supports a safe maintenance decision.

It improves transparency, auditability, and operational trust in production ML systems.

### Slide 8: Security and access control

The system uses:
- JWT-based authentication
- password hashing with bcrypt
- RBAC roles: ADMIN, ML_ENGINEER, VIEWER

Evidence: [FINAL_REPORT.md](FINAL_REPORT.md) and [07-api-design.md](07-api-design.md)

### Slide 9: API and database support

The API allows operations such as:
- user login
- model registration
- monitoring ingestion
- decision evaluation
- decision approval
- dashboard queries

The database stores users, registered models, monitoring observations, and decision logs.

Evidence: [07-api-design.md](07-api-design.md) and [06-database-design.md](06-database-design.md)

### Slide 10: Proof of quality

The final report states that the project achieved:
- 439 passing tests out of 439
- 32 dedicated test modules
- 0 failures

This is a strong sign that the design and implementation are well-structured and validated.

Evidence: [FINAL_REPORT.md](FINAL_REPORT.md)

---

## 4. Short 2-minute speech you can say to the teacher

"This project is PhoenixML, an intelligent MLOps decision-support platform for deployed machine learning models. The problem is that production ML systems degrade silently due to data drift, concept drift, and changing user behavior. PhoenixML continuously monitors model health, detects drift, and generates explainable maintenance recommendations through its AIMD engine. The key innovation is that the platform does not automatically retrain or rollback models without human approval. It follows a human-in-the-loop model and maintains audit logs for accountability. The project includes system architecture, database design, API design, security model, and a real demonstration scenario using the SpamGuard-v1 model. The report also states that the system passed 439 out of 439 tests. This makes it a robust academic project in MLOps, decision support, and responsible AI operations."

---

## 5. Best way to present this without running the app

Use the existing files as a live walkthrough:
1. Open [FINAL_REPORT.md](FINAL_REPORT.md) and start with the abstract.
2. Show the architecture in [03-architecture.md](03-architecture.md).
3. Explain the AIMD logic in [02-decision-engine.md](02-decision-engine.md).
4. Mention API and security in [07-api-design.md](07-api-design.md).
5. Refer to the test summary and operational demonstration in [FINAL_REPORT.md](FINAL_REPORT.md).

This gives the teacher a complete, structured presentation even though the actual application code is not present in the workspace.

---

## 6. Final note

The current workspace contains project documentation, not the runnable application code. So the right approach is a documentation-based demo rather than a live UI demo. This still demonstrates the full project concept, engineering design, and academic completeness.
