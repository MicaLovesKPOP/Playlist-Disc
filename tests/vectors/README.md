# Golden vectors

These vectors are intentionally in the `999900-999999` test namespace. They become compatibility fixtures and must not be reused as public music identities.

Initial vectors:

| ID | Check | Purpose |
| --- | ---: | --- |
| PD1-999901 | 7 | TOC lattice smoke test |
| PD1-999902 | 5 | Audio-beacon smoke test |
| PD1-999903 | 0 | CD-TEXT smoke test |
| PD1-123456 | 3 | Human-readable algorithm example only; not allocated |

## Generated physical-test variants

`pdv1 build-test-kit` uses the permanent development vectors above to produce controlled mastering variants. `PD1-999901-7` is generated both with and without optional CD-TEXT so compatibility testing can change metadata presence without changing the canonical TOC identity. `PD1-999902-5` is generated without CD-TEXT for beacon-focused testing, and `PD1-999903-0` retains CD-TEXT for display/metadata testing.
