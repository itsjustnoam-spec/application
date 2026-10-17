# Vue Conventions Checklist

Run this per changed `.vue` / `.ts` file. Every item must be answered ✅, ❌ (with `file:line`), or N/A.

## Architecture
- [ ] VU-01 Components are small and focused, and large views are split into subcomponents
- [ ] VU-02 No component has `v-dialog` as its root. Dialog content is its own card component, wrapped in `v-dialog` by the parent.
- [ ] VU-03 Logic, helpers, and interfaces used in more than one place are in `src/utils/` or `src/models/`

## SFC structure
- [ ] VU-04 Block order is `<template>`, then `<script lang="ts">`, then `<script setup lang="ts">`, then `<style>` (only if needed)
- [ ] VU-05 Interfaces, types, enums, and pure constants are in `<script lang="ts">`, and runtime logic is in `<script setup>`
- [ ] VU-06 `<script setup>` order is constants, then emits/props, then refs, then computed, then functions, then watchers, then lifecycle hooks, with single blank lines between sections

## Props & emits
- [ ] VU-07 `defineEmits` tuples are types only (`[string, boolean]`), with no parameter names
- [ ] VU-27 Props and emits are named interfaces (`<Component>Props` / `<Component>Emits`) in `<script lang="ts">`, used as `defineProps<XProps>()` / `defineEmits<XEmits>()`. No inline type literals in the macros.
- [ ] VU-08 A comment above the emit declaration explains non-obvious emit parameters

## UI
- [ ] VU-09 `EasyToolTip` is used, never raw `v-tooltip`
- [ ] VU-10 Complex titles, dialogs, and config controls have an `EasyToolTip` with `mdi-information`
- [ ] VU-11 Every async operation shows a loading state (`:loading`, progress, skeleton)
- [ ] VU-12 Search and filter loading is debounced, with the delay as a named constant
- [ ] VU-13 Paginated or lazy lists use the generic loadable resource (`v-infinite-scroll`)
- [ ] VU-14 Network errors go through `handleNetworkError`
- [ ] VU-15 Important titles and primary actions are centered

## Styling
- [ ] VU-16 No hardcoded colors. Uses Vuetify theme colors.
- [ ] VU-17 New semantic states get a new theme key (existing keys aren't reused for a different meaning)
- [ ] VU-18 No `px` for layout sizing. Uses flex, or `rem`/`vh`/`vw` when sizing is required.
- [ ] VU-19 Tailwind utilities are preferred, and scoped CSS appears only when Tailwind/Vuetify can't express the style

## Clean code
- [ ] VU-20 No loose truthy/falsy checks on non-booleans (explicit `=== null`/`=== undefined`, `.length === 0`, `=== 0`)
- [ ] VU-21 Empty-string checks use `.trim()` (`x.trim().length === 0`)
- [ ] VU-22 No magic numbers in template or script; large strings are named constants, short strings stay inline
- [ ] VU-23 Names are descriptive (no `data`, `item`, `load`)
- [ ] VU-24 Docstrings only for complex math or non-obvious integrations
- [ ] VU-25 No trailing `return` in functions that return nothing, and no `return undefined`/`return null` to mean "nothing"
- [ ] VU-28 No export at the declaration (`export const/function/interface/type/enum/class`). One export section at the bottom of the file or `<script lang="ts">` block (`export default` only where a tool requires it).
- [ ] VU-29 URLs, links, ports, and keys come from `.env` (`VITE_*` via `import.meta.env`), never hardcoded. New keys are in `.env.example`.

## Tests
- [ ] VU-26 New logic and components are covered by Vitest tests per `vitest-conventions`
