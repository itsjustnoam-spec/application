# Test Plan: <feature name>

| ID | Layer | Test name | File path | What it tests | Expected result | Covers |
|----|-------|-----------|-----------|---------------|-----------------|--------|
| T-1 | be-integration | `test_read_entity_by_id_missing_id_raises_entity_not_found_error` | `tests/entities/test_read_entity.py` | Reading an entity id that doesn't exist | Raises `EntityNotFoundError` with "Entity 7 was not found." | REQ-1, EC-1 |
| T-2 | be-api | `test_get_entity_missing_id_returns_404` | `tests/entities/test_entities_api.py` | GET /entities/7 when it doesn't exist | 404, body `{"detail": "Entity 7 was not found."}` | REQ-1, EC-1 |
| T-3 | fe-component | `emits select with the entity id when an entity row is clicked` | `tests/unit/components/entities/EntityList.spec.ts` | Clicking a row in EntityList | `select` emitted once with `7` | REQ-3 |
| T-4 | fe-component | `shows an empty state when there are no entities` | `tests/unit/components/entities/EntityList.spec.ts` | EntityList with an empty API result | The empty-state element is visible | EC-2 |
| T-5 | fe-integration | `lists the created entity after the create dialog is submitted` | `tests/integration/entities/create-entity.spec.ts` | EntitiesView + store + router + create dialog, MSW network | The table contains "Pump" after submit | REQ-2 |
| T-6 | fe-integration | `shows the backend error when loading entities fails` | `tests/integration/entities/list-entities.spec.ts` | GET /api/entities returns 503 | The error element shows "Database unavailable" | REQ-4 |
| T-7 | browser | `user creates an entity and sees it in the list` | `tests/e2e/entities/create-entity.spec.ts` | The full create journey in Chromium, mocked API | A row with "Pump" is visible | REQ-2 |

## Exempt
- <pure proxy route>: pass-through without business logic

## Coverage map
| ID | Tests |
|----|-------|
| REQ-1 | T-1, T-2 |
| REQ-2 | T-5, T-7 |
| EC-1 | T-1, T-2 |

## Results
- Backend: <passed/failed counts> · changed-lines coverage: <n>%
- Frontend (Vitest): <passed/failed counts> · changed-lines coverage: <n>%
- Browser (Playwright): <passed/failed counts>
