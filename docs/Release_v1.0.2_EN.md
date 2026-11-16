# NilePhytoDock Studio v1.0.2 — Installation and startup

Developers: **Ahmed G Soliman** and **Malak Taha**.

1. Close the previous version of the application.
2. Download and run `NilePhytoDock-v1.0.2-Setup.exe` from the official release page: https://github.com/ahmedGSoliman99/NilePhytoDock-Studio/releases/tag/v1.0.2.
3. Choose a dedicated writable installation directory. Python, Qt, the scientific libraries, Java, P2Rank and Smina are installed automatically.
4. Start NilePhytoDock Studio from the Start menu and wait for **Engines available**.
5. Open a saved project or choose your study output directory. The working database and preferences remain under `%LOCALAPPDATA%\NilePhytoDock`.

Windows 10/11 x64, 8 GB RAM, 4 GB free installation space, and a 1366 × 768 or larger display with working graphics drivers are recommended. Research outputs require additional space. Internet access is needed for optional online retrieval.

Documentation is installed in the external `Documentation` folder. The hidden `_internal` directory contains required runtime files and must be retained. The installer is unsigned.

## Responsiveness

Background jobs run sequentially. Native calculations use below-normal Windows priority and at most two cores, with bounded numerical-library threads and Java memory. These resource budgets preserve the existing algorithms and search-effort defaults. Resource errors remain visible rather than silently truncating a calculation.

Unused molecular renderers are loaded on demand. Hidden viewers stop animation and suspend their browser page. The separate 3D window reuses the same scene. Surface calculation uses one worker per surface and coalesces repeated control changes. Camera controls, geometry and exports are retained.

Detailed results and rankings load in a background worker only when needed. The detailed grid displays up to 2,000 poses; full exports retain all records. The four chart types remain Bubble Plot, Docking Heatmap, Interaction Matrix and Docking Network. Only the selected chart renders on the charts page.

## Cancellation and closing

**Cancel** stops active work and removes queued tasks. Closing once hides the interface, requests cancellation and automatically finishes closing after cleanup. Native process trees are scoped to their owning job. A noninterruptible library call may finish its current step before observing cancellation.

The progress log distinguishes fresh calculations, verified cache reuse and completed results retained on resume. The fixed seed remains intentional. Disable **Reuse verified matching calculations** in a new study to require fresh runs; changing a recorded seed requests an independent search. Matching inputs can legitimately produce matching scores.

## Files and licensing

Retain complete study folders when moving or reopening results. Outputs and reports stay in the user-selected directory. Updates preserve the working database and existing studies. Setup retains a recognized previous installation in a timestamped folder; these are installation backups, separate from research outputs.

NilePhytoDock source is GPL-3.0-or-later, without warranty. Third-party components retain their own terms and mandatory notices. Corresponding source and rebuild instructions are publicly accessible at https://github.com/ahmedGSoliman99/NilePhytoDock-Source. Qt libraries remain separately replaceable for LGPL compliance. See `SOURCE_ACCESS.md`, `LICENSES.md` and `THIRD_PARTY_SOURCES.json` beside this guide.
