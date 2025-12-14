#!/usr/bin/env Rscript

# Likert-style comparison for s1b follow-up study
# -----------------------------------------------
# This script reads the s1b Likert CSV (one row per participant, columns such
# as `saliency_badges`, `saliency_footnotes`, …) and produces a clean Likert
# barplot comparing *Badges* vs *Footnotes* for each item.
#
# Layout:
#   - One horizontal bar per question (saliency, clutter, …)
#   - Stacked responses from Strongly Disagree to Strongly Agree
#   - Grouped by response *format* ("Badges", "Footnotes")
#
# Usage (from repo root):
#   Rscript analysis/s1b/r_scripts/s1b_likert_barplot.R analysis/data/s1b analysis/s1b/r_output
# or (from inside analysis/):
#   Rscript s1b/r_scripts/s1b_likert_barplot.R data/s1b s1b/r_output

suppressPackageStartupMessages({
  library(tidyverse)
  library(likert)
})

#' Generate a Likert-type horizontal stacked barplot for the s1b follow-up.
#'
#' Each participant rated *both* visualization formats (badges and footnotes)
#' on the same set of items. We reshape the data so that each row represents a
#' participant × format, with a `group` column indicating "Badges" vs
#' "Footnotes", and one column per item (saliency, clutter, …).
#'
#' @param data_dir   Directory where the s1b CSV lives (default: "data/s1b").
#' @param out_dir    Output directory for charts (created if missing).
#' @param input_file CSV file name inside `data_dir` (default: "likert.csv").
#' @param output_file PNG file name inside `out_dir`.
generate_s1b_likert_barplot <- function(
  data_dir    = file.path("data", "s1b"),
  out_dir     = file.path("s1b", "r_output"),
  input_file  = "likert.csv",
  output_file = "s1b_likert_barplot_by_format.png"
) {
  input_path  <- file.path(data_dir, input_file)
  output_path <- file.path(out_dir, output_file)

  if (!file.exists(input_path)) {
    stop("s1b Likert input file not found: ", input_path)
  }

  if (!dir.exists(out_dir)) {
    dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  }

  message("Reading s1b Likert data from: ", input_path)

  df_raw <- readr::read_csv(input_path, show_col_types = FALSE)

  # Core item base names we care about; these should exist as
  # "<item>_badges" and "<item>_footnotes" in the CSV.
  item_bases <- c(
    "saliency",
    "clutter",
    "interpretability",
    "usefulness",
    "trust",
    "standardization"
  )

  # Check that at least one expected pair of columns exists
  expected_cols <- c(
    paste0(item_bases, "_badges"),
    paste0(item_bases, "_footnotes")
  )
  available_cols <- intersect(expected_cols, names(df_raw))
  if (length(available_cols) == 0) {
    stop(
      "No expected s1b Likert item columns found in ",
      input_path,
      ". Expected some of: ",
      paste(expected_cols, collapse = ", ")
    )
  }

  # Long format: participant × item × format (badges/footnotes)
  df_long <- df_raw %>%
    dplyr::select(
      dplyr::any_of(c("participantId", "participantIndex", "group")),
      dplyr::all_of(available_cols)
    ) %>%
    tidyr::pivot_longer(
      cols      = tidyselect::all_of(available_cols),
      names_to  = c("item", "format"),
      names_sep = "_",
      values_to = "value"
    )

  # Keep only rows with non-missing numeric responses
  df_long <- df_long %>%
    dplyr::mutate(
      value_num = as.integer(value),
      format    = factor(
        format,
        levels = c("badges", "footnotes"),
        labels = c("Badges", "Footnotes")
      )
    ) %>%
    dplyr::filter(!is.na(value_num))

  if (nrow(df_long) == 0) {
    stop("No valid (non-missing) s1b Likert responses found in: ", input_path)
  }

  # Wide format for likert::likert:
  #   - one row per participant × format
  #   - `group` column: "Badges" vs "Footnotes"
  #   - one column per item base name (saliency, clutter, …)
  df_wide <- df_long %>%
    dplyr::mutate(
      group = format
    ) %>%
    dplyr::select(
      dplyr::any_of(c("participantId", "participantIndex")),
      group,
      item,
      value_num
    ) %>%
    tidyr::pivot_wider(
      names_from  = item,
      values_from = value_num
    )

  # Identify id and item columns
  id_cols   <- intersect(c("group", "participantId", "participantIndex"), names(df_wide))
  item_cols <- setdiff(names(df_wide), id_cols)

  if (length(item_cols) == 0) {
    stop(
      "No s1b Likert item columns found after reshaping. ",
      "Expected at least one of: ", paste(item_bases, collapse = ", ")
    )
  }

  # Human-readable question text for each item (used as axis labels / headers)
  item_label_map <- c(
    saliency        = "Easy to spot.",
    clutter         = "Cluttered or distracted from the visualization.",
    interpretability = "Clear and easy to interpret.",
    usefulness      = "Information was useful for understanding the visualization.",
    trust           = "Increased my trust in the information and methodology.",
    standardization = "Should be widely used alongside visualizations."
  )

  # Standardise all item columns to the same ordered factor levels (required by likert::likert)
  likert_labels <- c(
    "Strongly Disagree",
    "Disagree",
    "Neither Agree nor Disagree",
    "Agree",
    "Strongly Agree"
  )

  items_df <- df_wide %>%
    dplyr::select(dplyr::all_of(item_cols))

  items_df <- as.data.frame(
    lapply(
      items_df,
      function(col) {
        codes <- as.integer(as.character(col))
        factor(
          codes,
          levels  = 1:5,
          labels  = likert_labels,
          ordered = TRUE
        )
      }
    ),
    stringsAsFactors = FALSE
  )

  # Apply long-form question labels where we have a mapping
  original_names <- colnames(items_df)
  colnames(items_df) <- ifelse(
    original_names %in% names(item_label_map),
    item_label_map[original_names],
    original_names
  )

  grouping <- df_wide$group

  likert_obj <- likert::likert(items = items_df, grouping = grouping)

  # Color palette for 5-point Likert scale (negative → positive)
  palette_5 <- c(
    "#d73027", # Strongly Disagree
    "#fc8d59", # Disagree
    "#fee090", # Neither...
    "#91bfdb", # Agree
    "#4575b4"  # Strongly Agree
  )

  message("Writing s1b Likert barplot to: ", output_path)

  grDevices::png(output_path, width = 1600, height = 1200, res = 200)
  on.exit(grDevices::dev.off(), add = TRUE)

  p <- plot(
    likert_obj,
    type              = "bar",
    centered          = 3,
    wrap              = 200,
    plot.percent.low  = FALSE,
    plot.percent.neutral = FALSE,
    plot.percent.high = FALSE,
    colors            = palette_5
  ) +
    ggplot2::scale_y_continuous(
      labels = function(x) paste0(abs(x), "%")
    ) +
    ggplot2::scale_fill_manual(
      values = palette_5,
      name   = NULL,
      breaks = likert_labels,
      labels = likert_labels
    ) +
    ggplot2::labs(
      x = NULL,
      y = NULL
    ) +
    ggplot2::theme_minimal(base_size = 10) +
    ggplot2::theme(
      legend.position  = "bottom",
      axis.text.y      = ggplot2::element_text(size = 10),
      strip.text.y     = ggplot2::element_text(size = 10, face = "bold"),
      strip.background = ggplot2::element_rect(fill = "grey95", color = NA)
    )

  print(p)

  invisible(output_path)
}


# Allow running this script directly for quick checks (only when this file is
# the entry point, not when sourced from another script such as r_charts.R).
if (sys.nframe() == 1) {
  args <- commandArgs(trailingOnly = TRUE)
  data_dir <- if (length(args) >= 1) args[[1]] else file.path("data", "s1b")
  out_dir  <- if (length(args) >= 2) args[[2]] else file.path("s1b", "r_output")
  generate_s1b_likert_barplot(data_dir = data_dir, out_dir = out_dir)
}
