---
name: vue-conventions
description: Use when creating, modifying, refactoring, or reviewing Vue 3, Vuetify, TypeScript, and Tailwind frontend code. Enforces SFC block layout, script splitting, no exports from .vue files, Props/Emits interfaces, script setup ordering, refs over let, explicit checks (no ??), if over ternary calls, no void, EasyToolTip, loading states, error handling, and styling rules.
---

# Vue 3, Vuetify & TypeScript Frontend Conventions

Strict conventions for frontend development using Vue 3 (Composition API), Vuetify, TypeScript, and Tailwind CSS. Follow these rules whenever creating, modifying, or reviewing frontend code.

---

## 1. Component Architecture & Sizing

- **Small, Focused Components**: Prefer small, focused components over monolithic ones. Break complex views into small, reusable subcomponents.
- **Dialog Decomposition (`v-dialog`)**:
  - **Never** make `v-dialog` the root element of a component.
  - Create the dialog's content as a standalone modal/card component.
  - Wrap it in `v-dialog` at the call site / parent view. This keeps the modal content independently reusable, testable, and embeddable.
- **No redundant conditions**: never repeat a condition that a parent already guarantees. For example, content inside `<v-dialog :model-value="isDialogOpen">` only shows while the dialog is open, so it must not also have `v-if="isDialogOpen"`. If the content must start fresh each time it opens (e.g. a form that initialises from its props), give it a `:key` that the parent changes every time it opens the dialog, instead of a duplicate `v-if`. A new key remounts the content even when the props didn't change, e.g. opening "Add" twice in a row.
- **Shared Code Extraction**:
  - Any logic, helper functions, or TypeScript interfaces used in more than one place **must** be extracted into `src/utils/` or `src/models/`.
- **No exports from `.vue` files**: a `.vue` file never exports anything (no `export`, `export type`, or `export { ... }` in either script block). Anything another file needs (a type, a constant, a helper) belongs in `src/utils/`, `src/models/`, or the module it's really about, and both the component and the other file import it from there.

---

## 2. Single File Component (SFC) Structure

Every Vue SFC must follow this exact top-to-bottom block order:

1. `<template>`
2. `<script>` (both static and setup scripts)
3. `<style>` (only if necessary)

### Script Tag Splitting

Separate static type declarations from reactive runtime logic using two `<script>` tags:

1. `<script lang="ts">`: Contains component-specific interfaces (including the component's `Props` and `Emits` interfaces), types, enums, and pure constants. Nothing in it is exported (see §1).
2. `<script setup lang="ts">`: Contains component runtime logic and reactive state.

```vue
<template>
  <div class="flex flex-col gap-4">
    <!-- Component UI -->
  </div>
</template>

<script lang="ts">
interface UserCardItem {
  id: string
  name: string
  role: string
}

interface Props {
  user: UserCardItem
  initialStatus: boolean
}

// Emits: updated user ID and selection flag
interface Emits {
  'update': [string, boolean]
  'close': []
}

const DEFAULT_AVATAR_FALLBACK = '/assets/default-avatar.png'
</script>

<script setup lang="ts">
// Component runtime logic (strictly ordered)
</script>

<style scoped>
/* Only if Tailwind or Vuetify cannot express the style */
</style>
```

---

## 3. Strict `<script setup>` Internal Ordering

The contents of `<script setup lang="ts">` must follow this exact sequence, with single empty lines separating each section:

1. **Constants**: Component-local constants (timeout intervals, debounce delays, magic numbers, large strings).
   *(empty line)*
2. **`defineEmits` & `defineProps`**:
   *(empty line)*
3. **`ref`s / reactive state**:
   *(empty line)*
4. **`computed` properties**:
   *(empty line)*
5. **Const functions**: `const fn = () => {}`.
   *(empty line)*
6. **Function declarations**: `function fn() {}`.
   *(empty line)*
7. **Watchers (`watch`, `watchEffect`)**:
   *(empty line)*
8. **Lifecycle hooks (`onBeforeMount`, `onMounted`, `onUnmounted`, ...)**:

Every item sits in its own section: never declare a ref after a function, or a computed after a watcher.

### Example `<script setup>` Layout

```vue
<script setup lang="ts">
const DEBOUNCE_DELAY_MS = 300
const MAX_SELECTION_COUNT = 5

// Emits & Props (interfaces are declared in the <script lang="ts"> block)
const emit = defineEmits<Emits>()

const props = defineProps<Props>()

// Refs
const isActionLoading = ref<boolean>(false)
const searchFilter = ref<string>('')

// Computed
const hasActiveFilter = computed<boolean>(() => searchFilter.value.trim().length > 0)

// Const functions
const executeUserUpdate = async () => {
  isActionLoading.value = true
  try {
    // async work
    emit('update', props.user.id, true)
  } catch (error: unknown) {
    handleNetworkError(error)
  } finally {
    isActionLoading.value = false
  }
}

// Function declarations
function clearSearchFilter() {
  searchFilter.value = ''
}

// Watchers
watch(searchFilter, () => {
  debouncedSearch()
})

// Lifecycle
onMounted(() => {
  loadInitialData()
})
</script>
```

---

## 4. Props & Emits Rules

- **Always use interfaces named `Props` and `Emits`**: declare them in the `<script lang="ts">` block, not exported, and pass them: `defineProps<Props>()`, `defineEmits<Emits>()`. The file already says which component they belong to, so never prefix them (no `UserCardProps`, `ActiveEntitySelectEmits`).
  - **Never** write the type inline inside the macro: no `defineProps<{ ... }>()` and no `defineEmits<{ ... }>()`.
  - A component with no props or no emits doesn't call that macro at all.
- **`defineEmits` Parameter Naming**:
  - In `defineEmits`, do **NOT** name tuple parameters; specify types only.
  - BAD: `'update': [userId: string, isSelected: boolean]`
  - GOOD: `'update': [string, boolean]`
  - If parameter meanings are not obvious from their types, add a descriptive comment directly above the emit declaration.

---

## 5. UI Elements & Layout Patterns

### Template Formatting

When an element or component has **more than one attribute** (props, directives, events, `data-testid`, ...), put each part on its own line: the opening tag name, each attribute, the closing `>`, the text content, and the closing tag. An element with at most one attribute may stay on one line when it's short.

```vue
<!-- GOOD: -->
<v-btn
  variant="text"
  data-testid="retry-asset-types-button"
  @click="loadPage"
>
  Retry
</v-btn>

<!-- BAD: -->
<v-btn variant="text" data-testid="retry-asset-types-button" @click="loadPage">Retry</v-btn>
```

The same applies to self-closing components: each attribute on its own line, and `/>` on its own line.

### Tooltips (`EasyToolTip`)

- **Always use `EasyToolTip`**: Never use raw `v-tooltip`.
- **Complex UI Headers & Dialogs**: Whenever presenting complex titles, modals, dialogs, or intricate configuration controls, include an `EasyToolTip` featuring an `mdi-information` icon to provide hover explanation context to the user.

### Loading States & Async Handling

- **Visual Loading Indicators**: Always indicate loading state during asynchronous operations (e.g. `:loading="isActionLoading"` on buttons, progress bars, or skeletons). Never leave users without visual feedback during network operations.
- **Debounced Loading**: Always debounce search and filter-driven loading functions. All debounce timeout values must be declared as named constants (e.g. `const SEARCH_DEBOUNCE_MS = 300`).
- **Loadable Resources**: Use generic loadable resources (built on `v-infinite-scroll`) for paginated lists, feeds, and lazy-loaded datasets.
- **Error Handling**: Always use `handleNetworkError` for catching and presenting network/API errors to users.

### Alignment & Typography

- **Centering**: Center important titles and primary action buttons.

---

## 6. Styling, Themes & CSS

- **Never Hardcode Colors**: Always use Vuetify themes (`rgb(var(--v-theme-primary))`, `text-primary`, `bg-surface`, etc.).
- **Semantic Theme Keys**:
  - Never reuse existing theme colors for differing semantic intentions.
  - If a new semantic UI state is introduced, define a new semantic theme key in the theme configuration, even if its initial hex color value matches an existing theme key.
- **No Pixel (`px`) Sizing for Layouts**:
  - Never use `px` for layout dimensions or container sizing.
  - Use flexbox (`flex`, `flex-1`, `flex-grow`, `justify-between`, `gap-*`).
  - If explicit sizing is strictly necessary, use relative viewport or font units: `vh`, `rem`, `vw`.
- **Tailwind CSS First**:
  - Prefer Tailwind CSS utility classes over scoped CSS.
  - Use scoped `<style>` only for reusable custom component classes or CSS that cannot be expressed via Tailwind / Vuetify utilities.

---

## 7. General Clean Code Standards

- **Full & Explicit Checks (No Loose Falsy Checks)**:
  - Always perform full, explicit condition checks instead of loose truthy/falsy checks.
  - **Never** write `if (!test)` or `if (test)` on objects, strings, numbers, arrays, or nullable/optional variables.
  - Fully check what you actually want to evaluate:
    - Null / Undefined: `if (test === null || test === undefined)` or `if (test !== null && test !== undefined)`
    - Empty string: **Always check with `.trim()`** (e.g. `if (test.trim().length === 0)` or `if (test.trim() === '')`). **Never** check raw `=== ''` (which fails on whitespace-only strings) and **never** use loose `if (!test)`.
    - Empty array / collection: `if (test.length === 0)`
    - Numeric check: `if (test === 0)` or `if (test < 0)`
  - **Boolean Exception**: Only when a variable is strictly of type `boolean` (`true` or `false`), you may use `if (test)` or `if (!test)`.
- **No `??`**: never use the nullish coalescing operator (`??` or `??=`). Write the explicit check instead, so the reader sees exactly which values are handled:
  ```ts
  // GOOD:
  let siteName = 'Unknown site'
  if (site !== null && site !== undefined) {
    siteName = site.name
  }

  // BAD:
  const siteName = site?.name ?? 'Unknown site'
  ```
- **`if` over ternary for calls**: when the choice is which function to call (or whether to call one), use a full `if` / `else`, never a ternary (`isEditing ? updateAsset() : createAsset()`).
  ```ts
  // GOOD:
  if (isEditing.value) {
    await updateAsset(assetForm.value)
  } else {
    await createAsset(assetForm.value)
  }

  // BAD:
  await (isEditing.value ? updateAsset(assetForm.value) : createAsset(assetForm.value))
  ```
- **No `void` before calls**: call the function as it is (`loadPage()`), or `await` it when the order matters. Never write `void loadPage()`.
- **Prefer `ref` over `let`**: component state in `<script setup>` is a `ref` (`const selectedSiteId = ref<number | null>(null)`), not a reassigned `let`. A `let` isn't reactive, so the template and watchers never see its changes.
- **Extract Constants**: Never leave magic numbers scattered in template or script bodies; extract them into named constants.
- **Strings**: **large strings** (long messages, long URLs paths, multi-line text) become named constants. **Short strings** (labels, keys, short messages, single words) stay inline where they're used: moving them into constants only hides them and makes quick text changes slower.
- **Configuration in `.env`**: API base URLs, links to other systems, ports, keys, and every other environment-specific value live in the app's `.env` files (`VITE_*`) and are read through `import.meta.env` in one config module. Never hardcode them.
- **Exports at the bottom**: in `.ts` files, never export at the declaration (`export const`, `export function`, `export interface`, `export type`, `export enum`, `export class`). Declare everything first, then end the file with one export section (`.vue` files export nothing, see §1):
  ```ts
  const fetchEntities = async (): Promise<Entity[]> => { /* ... */ }
  interface Entity { id: number; name: string }

  export type { Entity }
  export { fetchEntities }
  ```
  The only exception is `export default`, where a tool requires it (e.g. `vite.config.ts`, `vitest.config.ts`, `playwright.config.ts`); keep it as the file's last statement.
- **Indicative Variable Naming**: Use clear, descriptive variable and function names (e.g., `isUserDeletionPending`, `loadUserProfileDetails`), never generic names like `data`, `item`, or `load`.
- **Minimal Docstrings**: Use docstrings very sparingly in frontend code — only when explaining complex mathematical logic or non-obvious third-party integrations. Clean, typed, well-named code is self-documenting.
- **No Trailing `return`**: Functions that return nothing must not end with a bare `return`. Use `return` only for an early exit. Never write `return undefined` or `return null` to mean "nothing".

---

## 8. Testing

Frontend tests follow the **`vitest-conventions`** skill (component tests with Vue Test Utils, integration tests with MSW) and the **`browser-test-conventions`** skill (Playwright with a mocked backend). Frontend tests cover **only core behavior**: shared code (used by more than one component) and important flows. There's no frontend coverage target (see `vitest-conventions`, "What Gets a Frontend Test"). Give interactive and asserted elements a stable `data-testid` (`<what>-<kind>`, e.g. `save-entity-button`) and accessible names (labels on inputs, text on buttons). Both kinds of test rely on them. Reviewers use `references/checklist.md`.
