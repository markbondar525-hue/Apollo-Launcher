Apollo 4.4 — desktop source, NOT an installer.
Windows / macOS / Linux: GitHub Actions can attempt builds without local Terminal.
Create a GitHub repository, upload this project including .github/workflows/build.yml,
then open Actions > Build Apollo desktop > Run workflow. Download the resulting artifact if successful.
macOS package is unsigned; no Apple notarization. Preserve the whole application folder.
Java launch uses installed Minecraft files and Java runtime, local single-player nickname.
No Microsoft token integration, no download of Minecraft, no online authentication.
Installed Fabric/Forge/NeoForge versions may work if their metadata and libraries are complete.
The official login button opens a website only. Other games are informational tabs.
Android and iOS builds are not included. No mobile game runtime is implemented.
Local development: pip install -r requirements.txt; python main.py.
Syntax checked only; dependencies and runtime not tested.
