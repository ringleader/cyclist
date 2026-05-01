# HACS Integration & Publishing Knowledge Base

This document outlines the mandatory steps and common pitfalls for publishing a Home Assistant integration to the HACS (Home Assistant Community Store) default list.

## 1. Repository Structure
HACS is strict about the location of metadata files.
- **`hacs.json`**: Must be in the **root** directory (not inside `custom_components`).
- **`LICENSE`**: Must be in the root directory.
- **`manifest.json`**: Must be inside `custom_components/your_domain/`.
- **Brand Assets**: Must be in `custom_components/your_domain/brand/` as `icon.png` and `logo.png`.

## 2. Manifest.json Requirements
The `manifest.json` is the most common cause of "hassfest" CI failure.
- **Key Sorting**: Keys MUST be ordered: `domain`, `name`, then all other keys in **alphabetical order**.
- **Issue Tracker**: The `issue_tracker` key is mandatory for HACS inclusion.
- **Valid Keys**: Do NOT include `icon` or `logo` keys in `manifest.json`; these are invalid and will fail the Home Assistant internal validator.

## 3. Continuous Integration (CI)
You must have two workflows in `.github/workflows/`:
1. **`hassfest.yaml`**: Validates the integration structure for Home Assistant.
2. **`hacs.yaml`**: Validates the integration against HACS-specific rules.

## 4. The Release Workflow
HACS bots check the **Latest Release** version.
- **Sequence**: 
  1. Push code changes.
  2. Wait for CI (GitHub Actions) to pass (Green checkmark).
  3. Create the GitHub Release (Tag).
- **Matching**: The version tag (e.g., `v1.0.2`) and the `version` string in `manifest.json` must match exactly.

## 5. Submitting the Pull Request (PR)
When submitting to [hacs/default](https://github.com/hacs/default):
- **Branching**: **NEVER** submit from your `master` or `main` branch. Always create a feature branch (e.g., `add-my-integration`) on your fork.
- **PR Template**: You must use the exact checklist provided in the HACS PR template.
- **Required Links**: The PR description must include three explicit links:
  1. Repository URL.
  2. Latest Release URL.
  3. CI Action Runs URL.

## 6. Community Etiquette
- **No Manual Interaction**: Once the PR is open, do not comment on it unless a maintainer asks a question.
- **Patience**: HACS is maintained by volunteers; PRs are reviewed in the order they were received.

---
*Created on 2026-03-25 for the Cyclist Integration Project.*
