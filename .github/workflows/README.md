# GitHub Actions Workflows

## Disabled Workflows

### widget-testing.yml.disabled
This workflow has been disabled to prevent unnecessary GitHub Actions charges. 

**Why it was disabled:**
- Runs on every push/PR (excessive triggering)
- Spins up multiple database services
- Runs 5+ parallel jobs with extensive testing
- Includes performance and security scanning
- Was causing unexpected billing

**To re-enable:**
Rename `widget-testing.yml.disabled` back to `widget-testing.yml` after:
1. Limiting triggers (only on PR, not every push)
2. Reducing test scope
3. Using GitHub Actions more efficiently

## Active Workflows
(Currently none)

## Recommendations
- Only run CI/CD on pull requests, not every push
- Use manual triggers for expensive operations
- Consider using self-hosted runners for frequent builds
- Cache dependencies aggressively
- Limit matrix builds