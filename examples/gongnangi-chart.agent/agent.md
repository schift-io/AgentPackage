# Gongnangi Chart Skill

Create consulting-style charts, Instagram card-news pages, and animated chart
artifacts from user-approved content. The package preserves the upstream
Claude Code skill as a portable AgentPackage skill; the selected Runtime owns
model access, filesystem isolation, rendering tools, and artifact collection.

Before generating code, ask the questions required by `SKILL.md` and present a
plan for user approval. Keep source lines and user-provided data provenance in
the resulting artifact. Never install dependencies, write outside the package
workspace, or use direct network access from the package.

The package includes HTML source examples under `examples/`. PNG/GIF/MP4
outputs are run artifacts and are intentionally not part of this source
package.
