#!/usr/bin/env Rscript

# Simple, clean Likert barplot using the 'likert' package
# -------------------------------------------------------
# - Expects a wide CSV with one row per participant and one column per Likert item.
# - For this project, it defaults to `questionnaire_likert_scores.csv` created by the
#   Python data prep scripts, with:
#     * group          (e.g. "badge", "footnote")
#     * participantId
#     * saliency, clutter, interpretability, usefulness, trust, standardization
# - Produces a horizontal stacked bar chart for each item, optionally grouped by `group`.

suppressPackageStartupMessages({
  library(tidyverse)
  library(likert)
})

#' Generate a Likert-type horizontal stacked barplot for questionnaire items.
#'
#' @param data_dir    Directory where the CSV lives (relative or absolute).
#' @param out_dir     Output directory for charts (created if missing).
#' @param input_file  CSV file name inside `data_dir`.
#' @param output_file PNG file name inside `out_dir`.
generate_likert_barplot <- function(
  data_dir    = "data",
  out_dir     = "r_output",
  input_file  = "questionnaire_likert_scores.csv",
  output_file = "likert_barplot_by_group.png"
) {
  # Resolve paths
  input_path  <- file.path(data_dir, input_file)
  output_path <- file.path(out_dir, output_file)

  if (!file.exists(input_path)) {
    stop("Likert input file not found: ", input_path)
  }

  if (!dir.exists(out_dir)) {
    dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  }

  message("Reading Likert data from: ", input_path)

  df <- readr::read_csv(input_path, show_col_types = FALSE)

  # By default we treat all non-id columns as Likert items.
  id_cols <- intersect(c("group", "participantId"), names(df))
  item_cols <- setdiff(names(df), id_cols)

  # Human-readable question text for each item (used as axis labels / headers)
  item_label_map <- c(
    saliency        = "Footnotes/Badges were easy to spot.",
    clutter         = "Footnotes/Badges cluttered or distracted from the visualization.",
    interpretability = "Footnotes/Badges were clear and easy to interpret.",
    usefulness      = "Information in the Footnotes/Badges was useful for understanding the visualization.",
    trust           = "Footnotes/Badges increased my trust in the information and methodology.",
    standardization = "Footnotes/Badges like these should be widely used alongside visualizations."
  )

  if (length(item_cols) == 0) {
    stop(
      "No Likert item columns found in ", input_path,
      ". Expected at least one column beyond: ", paste(id_cols, collapse = ", ")
    )
  }

  # Standardise all item columns to the same ordered factor levels (required by likert::likert)
  # We map numeric codes 1–5 to the actual response labels used in the report:
  # 1 = Strongly Disagree, 5 = Strongly Agree
  likert_codes  <- as.character(1:5)
  likert_labels <- c(
    "Strongly Disagree",
    "Disagree",
    "Neither Agree nor Disagree",
    "Agree",
    "Strongly Agree"
  )

  items_df <- df %>%
    dplyr::select(dplyr::all_of(item_cols))

  # Coerce via base R to avoid any tibble/list-column surprises,
  # and apply shared ordered factor levels with human-readable labels.
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

  # Apply the long-form question text as column names where we have a mapping
  original_names <- colnames(items_df)
  colnames(items_df) <- ifelse(
    original_names %in% names(item_label_map),
    item_label_map[original_names],
    original_names
  )

  # Optional grouping (e.g. "badge" vs "footnote")
  grouping <- if ("group" %in% names(df)) df$group else NULL

  likert_obj <- if (!is.null(grouping)) {
    likert::likert(items = items_df, grouping = grouping)
  } else {
    likert::likert(items = items_df)
  }

  # Color palette for a 5-point Likert scale: from negative to positive
  # Ensure colors map correctly to levels 1..5
  palette_5 <- c(
    "#d73027", # 1: Strongly Disagree
    "#fc8d59", # 2: Disagree
    "#fee090", # 3: Neither...
    "#91bfdb", # 4: Agree
    "#4575b4"  # 5: Strongly Agree
  )

  message("Writing Likert barplot to: ", output_path)

  grDevices::png(output_path, width = 1500, height = 1200, res = 200)
  on.exit(grDevices::dev.off(), add = TRUE)

  p <- plot(
    likert_obj,
    type          = "bar",   # stacked bar representation
    centered      = 3,       # center on the neutral point (for 1–5 scale)
    wrap          = 200,     # Prevent wrapping of long labels
    plot.percent.low = FALSE,
    plot.percent.neutral = FALSE,
    plot.percent.high = FALSE,
    colors        = palette_5 # Pass colors directly to plot.likert
  ) +
    ggplot2::scale_y_continuous(
      labels = function(x) paste0(abs(x), "%")
    ) + # Make negative values positive on the axis and add % sign
    ggplot2::scale_fill_manual(
      values = palette_5,
      name   = "Response",
      breaks = likert_labels,
      labels = likert_labels
    ) +
   ggplot2::labs(
      x = NULL,
      y = NULL
    ) +
    ggplot2::theme_minimal(base_size = 10) +
    ggplot2::theme(
      legend.position = "bottom",
      axis.text.y     = ggplot2::element_text(size = 10),
      strip.text.y    = ggplot2::element_text(size = 10, face = "bold"),
      strip.background = ggplot2::element_rect(fill = "grey95", color = NA)
    )

  # Ensure plot is drawn into the device
  print(p)

  invisible(output_path)
}


