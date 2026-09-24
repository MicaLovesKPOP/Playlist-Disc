# Static library site

Draft 0.2 can turn the validated source catalog into a complete dependency-free HTML library.

## Build

```bash
pdv1 build-site catalog --output build/site
pdv1 verify-site build/site
```

The generated directory contains:

```text
site/
  index.html
  library.json
  assets/
    site.css
    site.js
  discs/
    999901.html
    ...
  packs/
    draft-0-2-test-vectors.html
```

## Design goals

The site deliberately has no web framework, package-manager build, remote fonts, analytics, account system, or external JavaScript dependency.

`index.html` contains all catalog cards in ordinary HTML. A tiny JavaScript file adds client-side text/status/type/portability filtering; with JavaScript disabled, the complete library and all links remain readable.

Every disc has a stable detail-page path based only on its six-digit public ID. Packs likewise use their validated slug. The generated `library.json` is the same provider-neutral machine-readable snapshot available through `pdv1 export-library`.

## Verification

`pdv1 verify-site` checks:

- the index, machine-readable library, stylesheet, and script exist;
- `library.json` is a schema-version-1 `PDv1-library` object with array-shaped entry/pack collections and unique page keys;
- every library entry has exactly one detail page;
- every pack has exactly one pack page;
- every relative HTML link or local asset reference stays inside the generated site and resolves to an existing file.

Malformed or tampered machine-readable snapshots are reported as verification errors rather than causing the verifier itself to crash.

The builder runs the verifier before replacing the requested output directory.

## Determinism

Given the same validated source catalog and toolkit version, generation is deterministic. Tests build the site twice and compare every generated file hash.

This matters for review, mirroring, archival snapshots, and eventual Pages deployment.

## GitHub Pages

The repository intentionally does not auto-deploy Pages yet. Hosting configuration is repository/account state rather than part of PDv1, and a deployment workflow should not make ordinary CI fail merely because Pages has not been enabled.

When public catalog entries exist and the owner wants hosted browsing, a Pages workflow can simply:

1. check out the repository;
2. install the `playlist-disc` package;
3. run `pdv1 build-site catalog --output <artifact directory>`;
4. run `pdv1 verify-site`;
5. upload/deploy that directory through GitHub Pages.

No separate frontend build chain is required.

## Boundary

The static browser is a view over catalog data. It does not log into streaming services, resolve market availability, expose private/local libraries, or claim physical compatibility.
