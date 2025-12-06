#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(tidyverse)
  library(paletteer)
})

#' Generate stacked click-count bars per badge, stacked by participant.
#'
#' Data source:
#'   - stimulus_badge_participant_metrics.csv
#'     (one row per stimulus × participant × badge with clickCount, etc.)
#'
#' For each stimulus:
#'   - y-axis: badge label
#'   - x-axis: clickCount (sum across participants)
#'   - fill: participant (readable id when available)
#'
#' @param data_dir Directory where the CSV files live.
#' @param out_dir  Output directory for charts (created if missing).
generate_badge_click_participant_counts_plot <- function(
  data_dir  = "data",
  out_dir   = "r_output",
  input_file = "stimulus_badge_participant_metrics.csv"
) {
  input_path <- file.path(data_dir, input_file)

  if (!file.exists(input_path)) {
    warning("Badge participant metrics input file not found: ", input_path)
    return(invisible(NULL))
  }

  if (!dir.exists(out_dir)) {
    dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  }

  message("Reading Badge participant metrics from: ", input_path)
  df <- readr::read_csv(input_path, show_col_types = FALSE)

  required_cols <- c(
    "stimulusId",
    "participantId",
    "participantReadableId",
    "badgeId",
    "badgeLabel",
    "clickCount"
  )
  if (!all(required_cols %in% names(df))) {
    warning(
      "Missing required columns in badge participant metrics. Expected: ",
      paste(required_cols, collapse = ", ")
    )
    return(invisible(NULL))
  }

  # Keep only rows with non-zero click counts so stacks represent actual activity
  df <- df %>%
    dplyr::mutate(
      clickCount = as.numeric(clickCount)
    ) %>%
    dplyr::filter(!is.na(clickCount), clickCount > 0)

  if (nrow(df) == 0) {
    warning("No rows with clickCount > 0; nothing to plot.")
    return(invisible(NULL))
  }

  # Display label per badge: prefer badgeLabel, fall back to badgeId
  df <- df %>%
    dplyr::mutate(
      badgeLabelDisplay = dplyr::if_else(
        !is.na(badgeLabel) & trimws(badgeLabel) != "",
        trimws(badgeLabel),
        trimws(badgeId)
      ),
      # Normalise any CO₂-like text to plain ASCII "CO2" so it renders everywhere
      badgeLabelDisplay = stringr::str_replace_all(
        badgeLabelDisplay,
        pattern = "\u2082",
        replacement = "2"
      )
    ) %>%
    dplyr::filter(!is.na(badgeLabelDisplay), badgeLabelDisplay != "")

  if (nrow(df) == 0) {
    warning("No badges with valid labels after cleaning.")
    return(invisible(NULL))
  }

  # Participant display: use readable id when available, otherwise raw id
  df <- df %>%
    dplyr::mutate(
      participantDisplay = dplyr::if_else(
        !is.na(participantReadableId) & trimws(participantReadableId) != "",
        trimws(participantReadableId),
        trimws(participantId)
      )
    )

  # Nice human-readable stimulus labels using plain ASCII for "CO2"
  pretty_stimulus <- function(id) {
    dplyr::case_when(
      id == "co2-emissions" ~ "CO2 Emissions",
      id == "global-warming-projection" ~ "Global Warming Projection",
      TRUE ~ as.character(id)
    )
  }

  df <- df %>%
    dplyr::mutate(
      stimulus_label = pretty_stimulus(stimulusId)
    )

  # Order badges within each stimulus by total click count (descending),
  # so the most-interacted badges appear at the top, and compute total
  # click counts per badge for axis scaling.
  badge_order_df <- df %>%
    dplyr::group_by(stimulus_label, badgeLabelDisplay) %>%
    dplyr::summarise(
      totalClick = sum(clickCount, na.rm = TRUE),
      .groups = "drop"
    ) %>%
    dplyr::group_by(stimulus_label) %>%
    dplyr::arrange(dplyr::desc(totalClick), .by_group = TRUE) %>%
    dplyr::mutate(
      badgeLabelOrder = factor(badgeLabelDisplay, levels = badgeLabelDisplay)
    ) %>%
    dplyr::ungroup()

  # Global max over *stacked* click counts per badge (not per participant)
  max_total_click <- max(badge_order_df$totalClick, na.rm = TRUE)

  badge_order_df <- badge_order_df %>%
    dplyr::select(stimulus_label, badgeLabelDisplay, badgeLabelOrder)

  df <- df %>%
    dplyr::left_join(badge_order_df, by = c("stimulus_label", "badgeLabelDisplay"))

  # Single chart: both stimuli in one figure, faceted vertically.
  # Axis is based on stacked click counts per badge so the bar lengths
  # and x-axis labels match.
  if (!is.finite(max_total_click) || max_total_click < 0) {
    max_total_click <- 0
  }
  # Even-integer axis that always extends at least one full step beyond the max.
  # Example: max 9 -> ticks up to 12; max 21 -> ticks up to 24.
  max_even  <- ceiling(max_total_click / 2) * 2
  max_break <- max_even + if (max_total_click > 0) 2 else 0

  output_path <- file.path(out_dir, "badge_click_participant_counts_stacked.png")
  message("Writing Badge Click Participant Counts stacked plot to: ", output_path)

  p <- ggplot(
    df,
    aes(
      x    = clickCount,
      y    = badgeLabelOrder,
      fill = participantDisplay
    )
  ) +
    geom_col(width = 0.7) +
    facet_wrap(
      ~ stimulus_label,
      ncol   = 1,
      scales = "free_y"
    ) +
    scale_x_continuous(
      breaks = seq(0, max_break, by = 2),
      limits = c(0, max_break)
    ) +
    # Use a clean qualitative palette from paletteer (many distinct colors)
    paletteer::scale_fill_paletteer_d("ggthemes::Tableau_20") +
    labs(
      title = "Click counts per badge, stacked by participant",
      x     = "Click count",
      y     = NULL,
      fill  = "Participant"
    ) +
    theme_minimal(base_size = 12) +
    theme(
      legend.position       = "bottom",
      axis.text.y           = element_text(size = 10),
      axis.text.x           = element_text(size = 10),
      panel.grid.major.y    = element_blank()
    )

  grDevices::png(output_path, width = 1800, height = 1200, res = 200)
  print(p)
  grDevices::dev.off()

  invisible(output_path)
}

# Allow running this script directly for quick checks.
if (identical(environment(), globalenv())) {
  args <- commandArgs(trailingOnly = TRUE)
  data_dir <- if (length(args) >= 1) args[[1]] else "data"
  out_dir  <- if (length(args) >= 2) args[[2]] else "r_output"
  generate_badge_click_participant_counts_plot(data_dir = data_dir, out_dir = out_dir)
}


