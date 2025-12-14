#!/usr/bin/env Rscript

# s1b-specific R wrapper for chart creation
# -----------------------------------------
# This script is the entry point for generating R figures for the s1b follow-up
# study only. It mirrors the style of `analysis/r_charts.R` but is scoped to:
#   - analysis/data/s1b/*.csv
#   - analysis/s1b/r_output/*.png
#
# Usage:
#   - From repo root:
#       Rscript analysis/s1b/r_charts.R
#       Rscript analysis/s1b/r_charts.R analysis/data/s1b analysis/s1b/r_output
#   - From inside analysis/:
#       Rscript s1b/r_charts.R
#       Rscript s1b/r_charts.R data/s1b s1b/r_output

suppressPackageStartupMessages({
  library(tidyverse)
})

args <- commandArgs(trailingOnly = TRUE)

# Defaults assume the working directory is the repo root
# (when called as `Rscript analysis/s1b/r_charts.R`) or the analysis directory
# (when called as `Rscript s1b/r_charts.R`).
data_dir <- if (length(args) >= 1) args[[1]] else file.path("data", "s1b")
out_dir  <- if (length(args) >= 2) args[[2]] else file.path("s1b", "r_output")

if (!dir.exists(data_dir)) {
  stop("s1b data directory does not exist: ", data_dir)
}

if (!dir.exists(out_dir)) {
  dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
}

message("Using s1b data directory: ", data_dir)
message("Writing s1b charts to:   ", out_dir)


# Helper to resolve an R script under analysis/s1b/r_scripts or s1b/r_scripts
resolve_script <- function(name) {
  candidates <- c(
    file.path("analysis", "s1b", "r_scripts", name), # when run from repo root
    file.path("s1b", "r_scripts", name)               # when run from analysis/
  )
  for (cand in candidates) {
    if (file.exists(cand)) {
      return(cand)
    }
  }
  warning(
    "s1b chart script not found: ", name,
    " (looked in: ", paste(candidates, collapse = " ; "), ")"
  )
  return(NULL)
}


## ---------------------------------------------------------------------------
## s1b follow-up study charts (Likert, preferences, quick reminder)
## ---------------------------------------------------------------------------

s1b_likert_barplot_script <- resolve_script("s1b_likert_barplot.R")
if (!is.null(s1b_likert_barplot_script)) {
  message("Sourcing s1b Likert barplot script: ", s1b_likert_barplot_script)
  source(s1b_likert_barplot_script, local = TRUE)
  if (exists("generate_s1b_likert_barplot")) {
    message("Generating s1b Likert barplot (Badges vs Footnotes) …")
    generate_s1b_likert_barplot(data_dir = data_dir, out_dir = out_dir)
  } else {
    warning("Function generate_s1b_likert_barplot() not found after sourcing ", s1b_likert_barplot_script)
  }
}

s1b_preferences_script <- resolve_script("s1b_preferences_barcharts.R")
if (!is.null(s1b_preferences_script)) {
  message("Sourcing s1b preferences barcharts script: ", s1b_preferences_script)
  source(s1b_preferences_script, local = TRUE)
  if (exists("generate_s1b_preferences_barcharts")) {
    message("Generating s1b preferences overview chart …")
    generate_s1b_preferences_barcharts(data_dir = data_dir, out_dir = out_dir)
  } else {
    warning("Function generate_s1b_preferences_barcharts() not found after sourcing ", s1b_preferences_script)
  }
}

s1b_quick_reminder_script <- resolve_script("s1b_quick_reminder_barcharts.R")
if (!is.null(s1b_quick_reminder_script)) {
  message("Sourcing s1b quick reminder barcharts script: ", s1b_quick_reminder_script)
  source(s1b_quick_reminder_script, local = TRUE)
  if (exists("generate_s1b_quick_reminder_barcharts")) {
    message("Generating s1b quick reminder by-group chart …")
    generate_s1b_quick_reminder_barcharts(data_dir = data_dir, out_dir = out_dir)
  } else {
    warning("Function generate_s1b_quick_reminder_barcharts() not found after sourcing ", s1b_quick_reminder_script)
  }
}

message("s1b R wrapper finished.")
