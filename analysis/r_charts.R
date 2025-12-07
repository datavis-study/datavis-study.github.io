#!/usr/bin/env Rscript

# Main R wrapper for chart creation
# ---------------------------------
# This script is intended to be the single entry point. Internally it
# delegates work to one script per chart under analysis/r_scripts/.
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


# Helper to resolve an R script under analysis/r_scripts/ or r_scripts/
resolve_script <- function(name) {
  candidates <- c(
    file.path("analysis", "r_scripts", name), # when run from repo root
    file.path("r_scripts", name)              # when run from analysis/
  )
  for (cand in candidates) {
    if (file.exists(cand)) {
      return(cand)
    }
  }
  warning(
    "Chart script not found: ", name,
    " (looked in: ", paste(candidates, collapse = " ; "), ")"
  )
  return(NULL)
}

likert_barplot_script <- resolve_script("likert_barplot.R")
if (!is.null(likert_barplot_script)) {
  message("Sourcing Likert barplot script: ", likert_barplot_script)
  source(likert_barplot_script, local = TRUE)
  if (exists("generate_likert_barplot")) {
    message("Generating Likert barplot for questionnaire items …")
    generate_likert_barplot(data_dir = data_dir, out_dir = out_dir)
  } else {
    warning("Function generate_likert_barplot() not found after sourcing ", likert_barplot_script)
  }
}

badge_hover_participant_counts_script <- resolve_script("badge_hover_participant_counts.R")
if (!is.null(badge_hover_participant_counts_script)) {
  message("Sourcing Badge Hover Participant Counts script: ", badge_hover_participant_counts_script)
  source(badge_hover_participant_counts_script, local = TRUE)
  if (exists("generate_badge_hover_participant_counts_plot")) {
    message("Generating Badge Hover Participant Counts stacked plot …")
    generate_badge_hover_participant_counts_plot(data_dir = data_dir, out_dir = out_dir)
  } else {
    warning("Function generate_badge_hover_participant_counts_plot() not found after sourcing ", badge_hover_participant_counts_script)
  }
}

badge_click_participant_counts_script <- resolve_script("badge_click_participant_counts.R")
if (!is.null(badge_click_participant_counts_script)) {
  message("Sourcing Badge Click Participant Counts script: ", badge_click_participant_counts_script)
  source(badge_click_participant_counts_script, local = TRUE)
  if (exists("generate_badge_click_participant_counts_plot")) {
    message("Generating Badge Click Participant Counts stacked plot …")
    generate_badge_click_participant_counts_plot(data_dir = data_dir, out_dir = out_dir)
  } else {
    warning("Function generate_badge_click_participant_counts_plot() not found after sourcing ", badge_click_participant_counts_script)
  }
}

badge_hover_time_participant_counts_script <- resolve_script("badge_hover_time_participant_counts.R")
if (!is.null(badge_hover_time_participant_counts_script)) {
  message("Sourcing Badge Hover Time Participant script: ", badge_hover_time_participant_counts_script)
  source(badge_hover_time_participant_counts_script, local = TRUE)
  if (exists("generate_badge_hover_time_participant_plot")) {
    message("Generating Badge Hover Time Participant stacked plot …")
    generate_badge_hover_time_participant_plot(data_dir = data_dir, out_dir = out_dir)
  } else {
    warning("Function generate_badge_hover_time_participant_plot() not found after sourcing ", badge_hover_time_participant_counts_script)
  }
}

badge_drawer_time_participant_counts_script <- resolve_script("badge_drawer_time_participant_counts.R")
if (!is.null(badge_drawer_time_participant_counts_script)) {
  message("Sourcing Badge Drawer Time Participant script: ", badge_drawer_time_participant_counts_script)
  source(badge_drawer_time_participant_counts_script, local = TRUE)
  if (exists("generate_badge_drawer_time_participant_plot")) {
    message("Generating Badge Drawer Time Participant stacked plot …")
    generate_badge_drawer_time_participant_plot(data_dir = data_dir, out_dir = out_dir)
  } else {
    warning("Function generate_badge_drawer_time_participant_plot() not found after sourcing ", badge_drawer_time_participant_counts_script)
  }
}

badge_interactions_overview_script <- resolve_script("badge_interactions_overview.R")
if (!is.null(badge_interactions_overview_script)) {
  message("Sourcing Badge Interactions Overview script: ", badge_interactions_overview_script)
  source(badge_interactions_overview_script, local = TRUE)
  if (exists("generate_badge_interactions_overview_plot")) {
    message("Generating Badge Interactions overview plot …")
    generate_badge_interactions_overview_plot(data_dir = data_dir, out_dir = out_dir)
  } else {
    warning("Function generate_badge_interactions_overview_plot() not found after sourcing ", badge_interactions_overview_script)
  }
}

message("R wrapper finished.")

