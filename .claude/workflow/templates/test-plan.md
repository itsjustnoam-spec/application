# Test Plan: <feature name>

| ID | Layer | Test name | File path | What it tests | Expected result | Covers |
|----|-------|-----------|-----------|---------------|-----------------|--------|
| T-1 | be-integration | `test_read_entity_by_id_missing_id_raises_entity_not_found_error` | `tests/entities/test_read_entity.py` | Reading an entity id that doesn't exist | Raises `EntityNotFoundError` with "Entity 7 was not found." | REQ-1, EC-1 |
| T-2 | be-api | `test_get_entity_missing_id_returns_404` | `tests/entities/test_read_entity.py` | GET /entities/7 when it doesn't exist | 404, body `{"detail": "Entity 7 was not found."}` | REQ-1, EC-1 |
| T-3 | fe-component | `emits confirm with the entity id when deletion is confirmed` | `tests/unit/components/ConfirmDeleteDialog.spec.ts` | The shared ConfirmDeleteDialog (used by several views) | `confirm` emitted once with `7` | REQ-3 |
| T-5 | fe-integration | `lists the created entity after the create dialog is submitted` | `tests/integration/entities/create-entity.spec.ts` | EntitiesView + store + router + create dialog, MSW network | The table contains "Pump" after submit | REQ-2 |
| T-6 | fe-integration | `keeps the dialog open with the error when saving an entity fails` | `tests/integration/entities/create-entity.spec.ts` | POST /api/entities returns 503 | The dialog stays open, the typed values are kept, and the error is shown | REQ-4 |
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
- Frontend (Vitest): <passed/failed counts>
- Browser (Playwright): <passed/failed counts>
