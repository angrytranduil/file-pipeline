# Project provenance

This repository began as a historical learning project created before Git was
initialized for it. The baseline contains a mixture of the learner's own work,
work completed with guidance, and AI-assisted mechanical changes. Importing the
project into Git does not claim that every existing line was written or proved
independently by the learner.

The project was copied from its previous local location, which was nested under
a Python virtual-environment directory. The original directory was left
unchanged and was not deleted. Source files were compared with SHA-256 hashes
after copying; all 38 copied files matched.

No application code, tests, dependencies, or architecture were changed during
the relocation. Generated outputs, caches, editor settings, logs, temporary
files, and secrets were excluded.

## Imported baseline

The imported baseline was checked with Python 3.14.7:

- pytest: 116 passed;
- Ruff for `src`: passed;
- mypy for `src`: passed with explicit package bases;
- Ruff for the complete project: 17 pre-existing findings in study and test
  files.

The 17 full-project Ruff findings are intentionally preserved for a separate
cleanup change. Snapshot integration and dependency cleanup are also outside
the relocation commit.
