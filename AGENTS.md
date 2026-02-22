# AGENTS.md
Guidance for autonomous coding agents in this repository.

## Current Repository Reality
- The repository is currently empty (no source files, tests, or tool configs).
- No build/lint/test command can be inferred from project files yet.
- No package manager lockfile is present.
- No CI workflow was found.
- No Cursor/Copilot instruction files were found during this scan.

Until real project files are added, follow the default contract below.

## Discovery Checklist (Run First)
Before making changes, detect tooling from files rather than assumptions.

1. Identify language and package manager files.
2. Identify formatter and linter configuration.
3. Identify test framework and test layout.
4. Identify CI-defined commands.
5. Identify Cursor/Copilot instruction files.

Useful probes:
```bash
ls -la
glob "**/*"
```

If project-specific commands exist, they override this document.

## Build, Lint, and Test Commands
No canonical commands are currently available because no project files exist.

### Command Selection Rules
- Prefer commands from `README.md`, `Makefile`, `justfile`, or CI.
- In Node repos, prefer `package.json` scripts over raw tool binaries.
- Prefer the command used in CI if there is disagreement.
- Do not introduce a new runner/toolchain unless asked.

### Typical Command Sources by Ecosystem
- JS/TS: `package.json` scripts.
- Python: `pyproject.toml`, `tox.ini`, `noxfile.py`, `Makefile`.
- Go: `go test`, `golangci-lint`, `Makefile` wrappers.
- Rust: `cargo test`, `cargo clippy`, `cargo fmt`.

### Single-Test Commands (Use Narrowest Selector)
When a framework is known, prefer the most specific command possible.

Pytest:
```bash
pytest tests/path/test_file.py::test_name
pytest -k "test_name" -q
```

unittest:
```bash
python -m unittest tests.test_module.TestClass.test_method
```

Jest:
```bash
npm test -- tests/path/file.test.ts -t "test name"
pnpm test -- tests/path/file.test.ts -t "test name"
```

Vitest:
```bash
pnpm vitest run tests/path/file.test.ts -t "test name"
```

Go:
```bash
go test ./path/to/pkg -run TestName
```

Rust:
```bash
cargo test module::tests::test_name
```

### Minimum Validation Before Handoff
- Run formatter checks (or format and verify intentional diffs only).
- Run linter for changed files (or full lint if scoped lint is unavailable).
- Run targeted tests for changed behavior; include one single-test run when possible.
- Run broader/full tests before handoff for high-risk changes.

## Code Style Guidelines
Apply these defaults until project-specific standards appear.

### General
- Keep diffs focused; avoid unrelated cleanup.
- Preserve existing behavior unless task explicitly changes it.
- Prefer explicit code over clever shortcuts.
- Keep modules cohesive and functions single-purpose.

### Formatting
- Use repository formatter if present; otherwise follow language idioms.
- Target readable line lengths (about 100 chars unless ecosystem differs).
- Use consistent indentation and avoid trailing whitespace.
- Avoid churn-only reformatting in unrelated files.

### Imports and Dependencies
- Order imports: standard library, third-party, local.
- Keep import ordering formatter-compatible.
- Remove unused imports and dead dependencies.
- Prefer explicit imports over wildcard imports.
- Avoid circular dependencies and hidden side effects on import.

### Types and Interfaces
- Use explicit types at public boundaries.
- Prefer stricter typing; avoid `any` unless unavoidable and justified.
- Model optional/null states deliberately.
- Encode invariants in types where practical.
- Keep external API contracts stable unless task requires changes.

### Naming
- Use descriptive names; avoid unclear abbreviations.
- JS/TS: `camelCase` for values/functions, `PascalCase` for types/classes.
- Python: `snake_case` for functions/variables, `PascalCase` for classes.
- Constants: `UPPER_SNAKE_CASE` only for true constants.
- Tests: name for behavior and expected outcome.

### Error Handling
- Validate inputs at boundaries and fail fast on invalid state.
- Never swallow errors silently.
- Add context when rethrowing/wrapping errors.
- Return structured, actionable errors where patterns exist.
- Avoid leaking secrets in logs, errors, or telemetry.

### Testing
- Add or update tests for behavior changes.
- Keep tests deterministic and isolated.
- Mock only true external boundaries.
- Assert outcomes, not implementation internals.
- Keep fixtures minimal and local.

### Documentation and Comments
- Update docs when workflow or externally visible behavior changes.
- Comment intent/constraints, not obvious mechanics.
- Record assumptions near complex logic.

### Git and Change Hygiene
- Do not revert unrelated user-authored changes.
- Keep commits atomic when asked to commit.
- Exclude secrets and machine-local artifacts.
- Avoid destructive git operations unless explicitly requested.

## Cursor and Copilot Rules
No instruction files were found in this scan:
- `.cursor/rules/`
- `.cursorrules`
- `.github/copilot-instructions.md`

If any of these files appear later, treat them as high-priority instructions and update this AGENTS.md accordingly.

## Maintenance Notes for Future Agents
- Re-scan the repository when new files/configs appear.
- Replace placeholders with concrete, project-native commands.
- Keep this document concise, accurate, and operational.
