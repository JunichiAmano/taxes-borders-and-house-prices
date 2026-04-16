# AGENTS.md for Labor Supply Paper (R Edition)
## Project Structure
- This is an R Project. Use `here::here()` for all file paths. Do NOT use `setwd()`.
- Data: `data/raw/` (immutable), `data/clean/` (generated).
- Code: `R/` for functions, `analysis/` for scripts.
- Output: `output/figures/`, `output/tables/`.

## Codex Execution Rules
- When running R code, execute via `Rscript` from the project root.
- Before generating a new analysis script, check `renv.lock` to ensure package suggestions are compatible.
- All plots must be saved via `ggsave(here::here("output/figures", "plot_name.png"))`.