# NilePhytoDock 0.6.1 verification

62 automated tests passed. New summary tests check identity aliases, shared oil membership, separate sites/protocols, failed runs, cutoff ties, source zeros/missing values versus explicit trace, unavailable contacts and optional van der Waals participation.

The actual preserved 3PTB study has five selected botanical profiles, four contributing profiles and twenty distinct eligible structures. Native Qt checks exercise the oil-first result page, functional group summary, independent maximized 3D window, F11/Esc restoration and layouts at 1366/1920 widths. No new synthetic docking results are inserted into research data.

The final frozen EXE separately executes actual P2Rank and three fresh Smina jobs, checks transferred boxes, reports, offline Plotly, verified 3D coordinates and the new result/group/fullscreen windows. The scientific seed is unchanged from 0.6.0. The repository and Windows download were checked without authentication after the owner requested public visibility.

Reproduce automated tests with `python -m pytest -q`. For native installation checks use a fresh NILEPHYTODOCK_DATA and output folder with `NilePhytoDock.exe --verify-installation OUTPUT tests/fixtures/3PTB.pdb`. For result-layout QA, extract the case-data release ZIP under data/validation and run `python -m tools.validate_result_ux`; it uses a private SQLite copy and relocates moved calculation paths. See the external Results_and_3D_Guide_EN.md for the user workflow. The retained 0.6.0 documents/evidence describe the scientific baseline.
