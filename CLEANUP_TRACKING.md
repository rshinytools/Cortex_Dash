# Codebase Cleanup Tracking

## Status: Starting Cleanup
**Last Updated**: 2025-08-19
**Dashboard Status**: ✅ Working (commit e15e3a9)

---

## Widget System
- [ ] Consolidate renderers: pick either registry-based or capital WidgetRenderer
- [ ] Remove duplicate WidgetRenderer implementations
- [ ] Remove commented registration in components/widgets/index.ts
- [ ] Standardize metric components (MetricsCard vs MetricWidget)

## Hooks & Data
- [ ] De-duplicate widget data hooks (useWidgetData.ts vs use-widget-data.ts)
- [ ] Clarify widget data contract
- [ ] Convert admin metrics to React Query

## Types & API
- [ ] Merge duplicate Study type definitions
- [ ] Centralize API endpoints (remove hardcoded localhost:8000)
- [ ] Prune unused imports/exports

## UI & Tailwind
- [ ] Fix dynamic Tailwind classes (col-span-${w})
- [ ] Move/remove story files
- [ ] Consolidate duplicate UI components

## Files & Artifacts
- [ ] Remove build artifacts (.next, logs, PIDs)
- [ ] Delete stray/zero-byte files
- [ ] Remove .bak/.original files
- [x] Clean up test scripts in root (✅ Removed all test_*.py, check_*.py, fix_*.py, verify_*.py)
- [x] Remove HTML/JSON artifacts (✅ Removed dashboard_page.html, template files, token files)
- [x] Clean up test .bat files (✅ Removed test_study_init.bat, kept fresh/dev .bat files)

## Structure & Clarity
- [ ] Separate mock vs runtime config
- [ ] Modularize parameter manager
- [ ] Standardize file naming conventions

## Tooling & Hygiene
- [ ] Enable TypeScript strict mode
- [ ] Configure ESLint for unused imports
- [ ] Add pre-commit hooks
- [ ] Remove console.log statements

---

## Cleanup Order (Recommended)
1. **Files & Artifacts** - Quick wins, no code changes
2. **Widget System** - Most impactful, establishes foundation
3. **Hooks & Data** - Depends on widget consolidation
4. **Types & API** - Improves type safety
5. **UI & Tailwind** - Visual/build improvements
6. **Structure & Clarity** - Refactoring
7. **Tooling & Hygiene** - Development workflow

---

## Notes
- Test dashboard after each major change
- Keep backup branch for each section
- Update USER_MANUAL.md after significant changes