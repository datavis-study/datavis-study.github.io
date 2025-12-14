#!/usr/bin/env Rscript

# s1b Likert chart wrapper
# ------------------------
# - Reads `analysis/data/s1b/likert.csv` (one row per participant, separate
#   *_badges and *_footnotes columns).
# - Reshapes it into the wide format expected by `generate_likert_barplot()`
#   from `analysis/r_scripts/likert_barplot.R`.
# - Calls that helper so the figure is styled identically to the main report's
#   Likert chart, but uses s1b data.

suppressPackageStartupMessages({
  library(tidyverse)
})

#' Generate the s1b Likert chart using the main Likert helper.
#'
#' @param data_dir_s1b Directory where s1b `likert.csv` lives (default: "data/s1b").
#' @param out_dir      Output directory for charts (created if missing).
#' @param output_file  PNG file name inside `out_dir` for the s1b copy.
generate_s1b_likert_barplot <- function(
  data_dir_s1b = file.path("data", "s1b"),
  out_dir      = file.path("s1b", "r_output"),
  output_file  = "s1b_likert_barplot_by_group.png"
) {
  # ---------------------------------------------------------------------------
  # 1. Read s1b likert.csv and reshape to main-helper format
  # ---------------------------------------------------------------------------
  s1b_input <- file.path(data_dir_s1b, "likert.csv")
  if (!file.exists(s1b_input)) {
    stop("s1b Likert CSV not found: ", s1b_input)
  }

  message("Reading s1b Likert CSV from: ", s1b_input)
  df_raw <- readr::read_csv(s1b_input, show_col_types = FALSE)

  item_bases <- c(
    "saliency",
    "clutter",
    "interpretability",
    "usefulness",
    "trust",
    "standardization"
  )

  expected_cols <- c(
    paste0(item_bases, "_badges"),
    paste0(item_bases, "_footnotes")
  )
  missing_cols <- setdiff(expected_cols, names(df_raw))
  if (length(missing_cols) > 0) {
    stop(
      "Missing expected s1b Likert columns in likert.csv: ",
      paste(missing_cols, collapse = ", ")
    )
  }

  # Long: participant × item × format (badges/footnotes)
  df_long <- df_raw %>%
    dplyr::select(
      dplyr::any_of(c("participantId")),
      dplyr::all_of(expected_cols)
    ) %>%
    tidyr::pivot_longer(
      cols      = tidyselect::all_of(expected_cols),
      names_to  = c("item", "format"),
      names_sep = "_",
      values_to = "value"
    ) %>%
    dplyr::mutate(
      format = factor(format, levels = c("badges", "footnotes"))
    )

  if (nrow(df_long) == 0) {
    stop("No non-missing s1b Likert responses found in: ", s1b_input)
  }

  # Wide: one row per participant × format, with a group column encoding format
  df_for_likert <- df_long %>%
    dplyr::mutate(
      group = dplyr::case_when(
        format == "badges"    ~ "Badges",
        format == "footnotes" ~ "Footnotes",
        TRUE                   ~ as.character(format)
      )
    ) %>%
    dplyr::select(
      participantId,
      group,
      item,
      value
    ) %>%
    tidyr::pivot_wider(
      names_from  = item,
      values_from = value
    )

  # Write a temporary CSV that matches the main helper's expectations.
  # Use the R session's temporary directory so nothing clutters the repo.
  helper_dir <- file.path(tempdir(), "s1b_likert_helper")
  if (!dir.exists(helper_dir)) {
    dir.create(helper_dir, recursive = TRUE, showWarnings = FALSE)
  }
  tmp_input_file <- "likert_s1b_for_helper.csv"
  tmp_input_path <- file.path(helper_dir, tmp_input_file)

  message("Writing reshaped s1b Likert data for helper to: ", tmp_input_path)
  readr::write_csv(df_for_likert, tmp_input_path, na = "")

  # ---------------------------------------------------------------------------
  # 2. Resolve and source the main Likert helper, then call it
  # ---------------------------------------------------------------------------
  likert_script_candidates <- c(
    file.path("analysis", "r_scripts", "likert_barplot.R"), # from repo root
    file.path("r_scripts", "likert_barplot.R")              # from analysis/
  )

  likert_script <- NULL
  for (cand in likert_script_candidates) {
    if (file.exists(cand)) {
      likert_script <- cand
      break
    }
  }

  if (is.null(likert_script)) {
    stop(
      "Could not find likert_barplot.R. Looked in: ",
      paste(likert_script_candidates, collapse = " ; ")
    )
  }

  message("Sourcing main Likert helper from: ", likert_script)
  source(likert_script, local = TRUE)

  if (!exists("generate_likert_barplot")) {
    stop("generate_likert_barplot() not found after sourcing ", likert_script)
  }

  if (!dir.exists(out_dir)) {
    dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  }

  message(
    "Generating s1b Likert chart via generate_likert_barplot() using reshaped s1b data."
  )

  generate_likert_barplot(
    data_dir    = helper_dir,
    out_dir     = out_dir,
    input_file  = tmp_input_file,
    output_file = output_file
  )
}


# Allow running this script directly for quick checks (only when this file is
# the entry point, not when sourced from another script such as r_charts.R).
if (sys.nframe() == 1) {
  args <- commandArgs(trailingOnly = TRUE)
  data_dir_s1b <- if (length(args) >= 1) args[[1]] else file.path("data", "s1b")
  out_dir      <- if (length(args) >= 2) args[[2]] else file.path("s1b", "r_output")
  generate_s1b_likert_barplot(data_dir_s1b = data_dir_s1b, out_dir = out_dir)
}
