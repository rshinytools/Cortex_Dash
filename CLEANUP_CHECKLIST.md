# Codebase Cleanup Checklist

Purpose: reduce clutter, unused parts, and redundancy without changing behavior. Scope: organization, consistency, and hygiene.

## Widget System
- [ ] Consolidate renderers: pick either the registry-based system (`components/widgets/widget-renderer.tsx` + `dashboard-renderer.tsx`) or the capital `WidgetRenderer` path used by study pages, and deprecate the other.
- [ ] Unify naming: avoid two `WidgetRenderer` implementations with different behavior; keep one or rename clearly (e.g., `WidgetRendererLive` vs `WidgetRendererRegistry`).
- [ ] Remove commented registration in `components/widgets/index.ts` or fully enable a real registry; don’t keep large commented blocks.
- [ ] Standardize metric components: choose one between `MetricsCard` and `MetricWidget`; centralize formatting/trend logic.

## Hooks & Data
- [ ] De-duplicate widget data hooks: keep a single canonical hook (either `hooks/useWidgetData.ts` or `hooks/use-widget-data.ts`) and update imports everywhere.
- [ ] Clarify widget data contract: ensure widgets receive either live definitions + `data_requirements` (view mode) or sample data (preview mode); avoid mixed ID/code paths.
- [ ] Prefer React Query: use React Query instead of raw axios for admin metrics and any server state to unify caching/retry behavior.

## Types & API
- [ ] Single source of truth for `Study`: merge duplicate `Study` definitions (in `types/index.ts` and `lib/api/studies.ts`) into one shared type and import consistently.
- [ ] Centralize endpoints: remove hardcoded `http://localhost:8000/...` calls; use `apiClient` with `NEXT_PUBLIC_API_URL` configured in one place.
- [ ] Prune unused imports/exports: run a repo-wide check and remove dead code and unused symbols.

## UI & Tailwind
- [ ] Dynamic class safety: replace `className={\`col-span-${w}\`}` (prone to purge) with inline `gridColumn: 'span N'` or safelist `col-span-1..12` in `tailwind.config.ts`.
- [ ] Story files: move `*.stories.tsx` into `/stories` or a dedicated folder and exclude from production build if unused.
- [ ] Consolidate similar components: audit duplicates (e.g., breadcrumbs vs ui/breadcrumbs) and keep a single implementation.

## Files & Artifacts
- [ ] Remove build artifacts: delete `frontend/.next`, `frontend/frontend.log`, `frontend/build.log`, PID files; add to `.gitignore`.
- [ ] Delete stray/zero-byte files: remove `C:UsersamulyOneDriveAetherClinicalCortex_Dashfrontendsrccomponentsuialert-dialog.tsx` and any `nul` artifacts.
- [ ] Prune backups: delete `.bak` / `.original` files (e.g., under `studies/[studyId]/dashboard/`) if no longer referenced.

## Structure & Clarity
- [ ] Mock vs runtime config: move mock menu/template in the study dashboard behind a feature flag or separate preview route; default study views to runtime APIs (`getStudyMenu` / `getStudyDashboardConfig`) to avoid dual sources of truth.
- [ ] Parameter manager modularization: split `dashboard-parameters.tsx` into reducer/actions/selectors/provider modules for readability.
- [ ] Naming conventions: standardize file/component naming (PascalCase components; pick kebab-case or consistent convention for files) and enforce `@/` path aliases uniformly.

## Tooling & Hygiene
- [ ] TypeScript strictness: enable `strict`, `noUnusedLocals`, `noUnusedParameters` in `tsconfig.json`.
- [ ] Lint rules: ensure ESLint flags unused imports/vars; configure `eslint --fix` on staged files.
- [ ] Pre-commit hooks: add `lint-staged` + Husky to run `eslint --fix` and `tsc --noEmit`.
- [ ] CI checks: add CI steps for `tsc`, `eslint`, and a minimal build to catch regressions early.

## Optional (if moving to live data)
- [ ] Resolve widget codes to definitions: fetch `/admin/widgets`, map widget `type` to a numeric `id`, and pass `widgetData` + `data_requirements` into the unified `WidgetRenderer`.
- [ ] Replace preview with view: set `mode="view"` for study dashboard pages once definitions are provided and APIs return real data.
- [ ] Single renderer path: remove the unused widget system after migration to avoid maintenance overhead.

