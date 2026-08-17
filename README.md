<!--
  github.com/lowcache — sheet set LC-000 … LC-900.

  Every image here is build output. Do not hand-edit assets/*.svg; edit
  scripts/build_sheets.py and run `make sheets`. See scripts/drawset.py.

  Each sheet ships in two editions. The wide one is authored at 880px; the
  narrow one at 460px with its own single-column layout and larger type, because
  scaling the wide sheet down to a phone takes its 9.5px sheet labels below 4px
  -- present but unreadable. <source media> switches between them, which was
  checked against GitHub's markdown pipeline: the sanitizer keeps width-based
  media queries, not just the well-known prefers-color-scheme one.

  No markdown headings on purpose: the sheets carry their own typography, and
  GitHub's h1/h2 styling would cut across it. No external images or badges
  either, so nothing here can break when someone else's service goes down.
-->

<div align="center">

<picture>
  <source media="(max-width: 800px)" srcset="assets/sheet-lc000-narrow.svg">
  <img src="assets/sheet-lc000.svg" width="100%" alt="Sheet LC-000, general arrangement. Lowcache — Jarred Robinson, self-taught, ten-plus years on Linux, currently freelance. An exploded isometric drawing of the workstation in five layers: agents tooling, Nix, a tmpfs root marked in redline as the volatile layer, /persist durable state, and the hardware chassis. A datum line across the drawing reads volatile above, re-derived every boot.">
</picture>

<picture>
  <source media="(max-width: 800px)" srcset="assets/sheet-lc100-narrow.svg">
  <img src="assets/sheet-lc100.svg" width="100%" alt="Sheet LC-100, repository index. Five repositories: volnixos, a NixOS workstation with a tmpfs root; mcp-box, isolated Linux containers for MCP servers; memd, project memory for coding agents; volinit, a shell-init sysinfo fetch in Nim; and noctalia-claude-plugin, a Claude Code plugin for the Noctalia desktop shell.">
</picture>

</div>

<p align="center">
  <a href="https://github.com/lowcache/volnixos">volnixos</a> ·
  <a href="https://github.com/lowcache/mcp-box">mcp-box</a> ·
  <a href="https://github.com/lowcache/memd">memd</a> ·
  <a href="https://github.com/lowcache/volinit">volinit</a> ·
  <a href="https://github.com/lowcache/noctalia-claude-plugin">noctalia-claude-plugin</a>
</p>

<div align="center">

<picture>
  <source media="(max-width: 800px)" srcset="assets/sheet-lc200-narrow.svg">
  <img src="assets/sheet-lc200.svg" width="100%" alt="Sheet LC-200, survey. Eleven source repositories, five stars, six languages, on GitHub since 2022. Language distribution by weight across all public repositories, led by Python at 48 percent, then Nix, Luau, Shell, HTML and Nim.">
</picture>

<picture>
  <source media="(max-width: 800px)" srcset="assets/sheet-lc900-narrow.svg">
  <img src="assets/sheet-lc900.svg" width="100%" alt="Sheet LC-900, title block. Titled Lowcache — general arrangement, drawn by lowcache, sheets LC-000 through LC-900, revision 2026-08-17, scale not to scale.">
</picture>

</div>

<p align="center">
  <a href="https://infernalcode.com">infernalcode.com</a> ·
  <a href="https://wiki.infernalcode.com">wiki.infernalcode.com</a> ·
  <a href="https://buymeacoffee.com/lowcache">buymeacoffee.com/lowcache</a>
</p>
