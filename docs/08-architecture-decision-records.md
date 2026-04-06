# Architecture Decision Records (ADRs)

## ADR-001: Pragmatic Clean Architecture over Pure Hexagonal

**Status:** Accepted
**Date:** 2026-04-06
**Context:** The project needs a defensible architecture for a university thesis evaluated by competitive programming professors. Pure Hexagonal Architecture (Ports & Adapters) adds ceremony (port interfaces, adapter factories, DI containers) that increases complexity without proportional value for a monolithic FastAPI application.

**Decision:** Use Pragmatic Clean Architecture with four layers (domain, application, infrastructure, presentation) and FastAPI's native `Depends()` as the DI mechanism. Accept that routers know about concrete repository types ONLY through `presentation/dependencies.py` factory functions.

**Consequences:**
- Simpler codebase, faster onboarding for new thesis team members
- Domain and application layers remain vendor-agnostic (no SQLAlchemy imports)
- `dependencies.py` is the single integration point per module
- Validated automatically by `scripts/validate_architecture.py`

---

## ADR-002: Cross-module model imports accepted in infrastructure JOINs

**Status:** Accepted
**Date:** 2026-04-06
**Context:** Several repositories need cross-module JOINs (e.g., appointments listing needs patient names and doctor names). The alternatives are: database views (deployment complexity), N+1 queries (performance), or denormalization (data integrity).

**Decision:** Allow infrastructure repositories to import other modules' SQLAlchemy models for JOIN queries. This is acceptable because:
1. Only the infrastructure layer does this (domain/application remain clean)
2. The coupling is at the database level (shared schema), not at the domain level
3. Performance is critical (O(1) JOIN vs O(N) queries)

**Consequences:**
- `sqlalchemy_appointment_repository.py` may import `PatientModel`, `DoctorModel`
- `sqlalchemy_medical_record_repository.py` may import `AppointmentModel`, `DoctorModel`
- These imports are documented and validated as known exemptions

---

## ADR-003: Dashboard and Reports are cross-cutting query modules

**Status:** Accepted
**Date:** 2026-04-06
**Context:** Dashboard and EPI reports aggregate data from ALL bounded contexts (patients, appointments, doctors, inventory, medical records). They are read-only modules that don't own any entities.

**Decision:** Classify dashboard and reports as **cross-cutting query modules** with a simplified architecture:
- `domain/` contains only constants, enums, and pure functions (no entities, no repositories)
- `application/use_cases/` contains thin wrappers that call infrastructure query services
- `infrastructure/` contains query services that ARE allowed to import from other modules' infrastructure
- This exemption is hardcoded in `validate_architecture.py`

**Consequences:**
- Dashboard/reports infrastructure can import from any module's models
- They cannot modify data in other modules (read-only)
- New cross-cutting modules must be added to the `CROSS_CUTTING_MODULES` set in the validator

---

## ADR-004: FastAPI Depends() as dependency injection mechanism

**Status:** Accepted
**Date:** 2026-04-06
**Context:** The project needs DI to decouple routers from concrete repository implementations. Options: (a) Full DI container library (dependency-injector, lagom), (b) Manual factories, (c) FastAPI native `Depends()`.

**Decision:** Use FastAPI's native `Depends()` with module-level `presentation/dependencies.py` factory functions. Each factory returns a domain interface type, constructed with the concrete implementation.

**Consequences:**
- No external DI library dependency
- Type hints on factory return types enable IDE autocompletion on interface methods
- Testing can override dependencies using FastAPI's `app.dependency_overrides`
- Each module is self-contained: its `dependencies.py` is the integration point
