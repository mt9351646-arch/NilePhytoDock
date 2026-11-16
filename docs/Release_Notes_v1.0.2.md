# NilePhytoDock Studio v1.0.2

Developed by Ahmed G Soliman and Malak Taha.

This maintenance release packages the improvements made after v1.0.1.

- Load molecular views on demand and suspend hidden viewers.
- Reuse one molecular scene in the separate 3D window.
- Limit background concurrency, numerical thread pools, native process priority and CPU affinity.
- Bound Java memory and surface-rendering workers.
- Query detailed results and rankings asynchronously, avoiding repeated hidden-page updates.
- Cancel owned process trees and finish closing after a single close request.
- Identify fresh calculations, verified cache reuse and resumed results in progress messages.
- Export the four supported chart types without automatically generating obsolete charts.

The existing calculation algorithms, database contents, search-effort defaults and user output-directory handling are retained. No new scientific or experimental features are introduced.

Download `NilePhytoDock-v1.0.2-Setup.exe`. Windows 10/11 x64 is required. Runtime dependencies are included. The installer is unsigned; use the release checksum to verify the download.

Application source is GPL-3.0-or-later. Mandatory notices and publicly accessible corresponding source remain available at https://github.com/ahmedGSoliman99/NilePhytoDock-Source. The first official release remains v1.0.0; historical records are unchanged.
