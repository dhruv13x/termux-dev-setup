# Strategic ROADMAP.md

A strategic living document balancing **Innovation**, **Stability**, and **Debt**.

---

## 🏁 Phase 0: The Core (Stability & Debt)
**Goal**: Solid foundation, high reliability, and clean code.

- [x] **[Debt] Testing**: Coverage > 80% (Current: >95%).
- [x] **[Debt] CI/CD**: Linting (ruff), Type Checking.
- [x] **[Debt] Documentation**: Comprehensive README (Gold Standard V3).
- [x] **[Debt] Refactoring**: Pay down critical technical debt (Service Modules Refactored).

---

## 🚀 Phase 1: The Standard (Feature Parity)
**Goal**: Competitiveness and superior User Experience.
*Risk*: Low

- [x] **[Feat] UX**: Interactive Setup Wizard (CLI improvements).
- [x] **[Feat] Config**: Environment variable validation and management.
- [ ] **[Feat] Config**: `tds.toml` configuration file support. (Size: M)
- [ ] **[Feat] Performance**: Async I/O for non-blocking operations. (Size: L)
- [ ] **[Feat] Performance**: Caching mechanism for frequent checks. (Size: S)
- [ ] **[Feat] UX**: Unified Logging System. (Size: M)
- [ ] **[Feat] UX**: System Health Checks (`tds doctor`). (Size: M)

---

## 🔌 Phase 2: The Ecosystem (Integration)
**Goal**: Interoperability and Extensibility.
*Risk*: Medium (Requires API design freeze)
*Dependencies*: Requires Phase 1

- [ ] **[Feat] API**: Local REST API for tool integration. (Size: L)
- [ ] **[Feat] Plugins**: Extension system for community plugins. (Size: XL)
- [ ] **[Feat] Integration**: Support for additional databases (MySQL, SQLite). (Size: M)
- [ ] **[Feat] Integration**: Dotfiles sync integration. (Size: S)

---

## 🔮 Phase 3: The Vision (Innovation)
**Goal**: Market Leader and Future-Proofing.
*Risk*: High (R&D)
*Dependencies*: Requires Phase 2

- [ ] **[Feat] AI**: LLM Integration for config tuning and debugging. (Size: XL)
- [ ] **[Feat] Cloud**: Cloud-Native Integration (Kubernetes/Docker export). (Size: L)
- [ ] **[Feat] Innovation**: Remote Tunnels for exposing services. (Size: M)
- [ ] **[Feat] Innovation**: Self-healing services daemon. (Size: L)

---

### Prioritization Strategy
1.  **Stability First**: Phase 0 is the prerequisite for all future development.
2.  **Value vs. Effort**: High value, low effort tasks in Phase 1 are prioritized next.
3.  **Risk Management**: High risk items (Phase 3) are deferred until the core is solid.
