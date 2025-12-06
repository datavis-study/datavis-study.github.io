#!/usr/bin/env Rscript

# Main R wrapper for chart creation
# ---------------------------------
# This script is intended to be the single entry point. Internally it
# delegates work to one script per chart under analysis/r_scripts/.
#
# For now, it only calls a single Likert-based chart script.
#
# Usage:
#   - From repo root:
#       Rscript analysis/r_charts.R
#       Rscript analysis/r_charts.R analysis/data analysis/r_output
#   - From inside analysis/:
#       Rscript r_charts.R
#       Rscript r_charts.R data r_output


library(tidyverse)

args <- commandArgs(trailingOnly = TRUE)

# Defaults assume the working directory is the repo root
data_dir <- if (length(args) >= 1) args[[1]] else "data"
out_dir  <- if (length(args) >= 2) args[[2]] else "r_output"

if (!dir.exists(data_dir)) {
  stop("Data directory does not exist: ", data_dir)
}

message("Using data directory: ", data_dir)
message("Writing charts to:    ", out_dir)

# Locate per-chart scripts, robust to working directory
script_candidates <- c(
  file.path("analysis", "r_scripts", "likert_mean_chart.R"), # when run from repo root
  file.path("r_scripts", "likert_mean_chart.R")              # when run from analysis/
)

likert_script <- NULL
for (cand in script_candidates) {
  if (file.exists(cand)) {
    likert_script <- cand
    break
  }
}

if (is.null(likert_script)) {
  stop(
    "Likert chart script not found. Tried: ",
    paste(script_candidates, collapse = " ; ")
  )
}

message("Sourcing Likert chart script: ", likert_script)
source(likert_script, local = TRUE)

# Call the per-chart generator (defined in likert_mean_chart.R)
generate_likert_mean_chart(data_dir = data_dir, out_dir = out_dir)

message("R wrapper finished.")

