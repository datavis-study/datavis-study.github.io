#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(tidyverse)
  library(paletteer)
})

#' Generate stacked hover & click count bars per badge, stacked by participant.
#'
#' Data source:
#'   - stimulus_badge_participant_metrics.csv
#'     (one row per stimulus × participant × badge with hoverCount / clickCount, etc.)
#'
#' Output:
#'   - One PNG with both interaction types side by side:
#'       badge_hover_click_participant_counts_stacked.png
#'   - Faceted by stimulus (rows) and interaction type (columns: Hovers, Clicks)
#'
#' @param data_dir Directory where the CSV files live.
#' @param out_dir  Output directory for charts (created if missing).
generate_badge_hover_click_participant_counts_plot <- function(
  data_dir   = "data",
  out_dir    = "r_output",
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
    "hoverCount",
    "clickCount"
  )
  if (!all(required_cols %in% names(df))) {
    warning(
      "Missing required columns in badge participant metrics. Expected: ",
      paste(required_cols, collapse = ", ")
    )
    return(invisible(NULL))
  }

  # Convert counts to numeric
  df <- df %>%
    dplyr::mutate(
      hoverCount = as.numeric(hoverCount),
      clickCount = as.numeric(clickCount)
    )

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

  # Long format for interaction type (Hover vs Click)
  df_long <- df %>%
    dplyr::select(
      stimulusId,
      stimulus_label,
      badgeLabelDisplay,
      participantDisplay,
      hoverCount,
      clickCount
    ) %>%
    tidyr::pivot_longer(
      cols      = c(hoverCount, clickCount),
      names_to  = "interaction_type",
      values_to = "count"
    ) %>%
    dplyr::filter(!is.na(count), count > 0) %>%
    dplyr::mutate(
      interaction_type = factor(
        interaction_type,
        levels = c("hoverCount", "clickCount"),
        labels = c("Hovers", "Clicks")
      )
    )

  if (nrow(df_long) == 0) {
    warning("No hover or click counts > 0; nothing to plot.")
    return(invisible(NULL))
  }

  # Order badges within each stimulus by total interactions (hover + click),
  # so the most-interacted badges appear at the top.
  badge_order_df <- df_long %>%
    dplyr::group_by(stimulus_label, badgeLabelDisplay) %>%
    dplyr::summarise(
      totalCount = sum(count, na.rm = TRUE),
      .groups = "drop"
    ) %>%
    dplyr::group_by(stimulus_label) %>%
    dplyr::arrange(dplyr::desc(totalCount), .by_group = TRUE) %>%
    dplyr::mutate(
      badgeLabelOrder = factor(badgeLabelDisplay, levels = badgeLabelDisplay)
    ) %>%
    dplyr::ungroup()

  badge_order_df <- badge_order_df %>%
    dplyr::select(stimulus_label, badgeLabelDisplay, badgeLabelOrder)

  df_long <- df_long %>%
    dplyr::left_join(badge_order_df, by = c("stimulus_label", "badgeLabelDisplay"))

  output_path <- file.path(out_dir, "badge_hover_click_participant_counts_stacked.png")
  message("Writing Badge Hover & Click Participant Counts stacked plot to: ", output_path)

  p <- ggplot(
    df_long,
    aes(
      x    = count,
      y    = badgeLabelOrder,
      fill = participantDisplay
    )
  ) +
    geom_col(width = 0.7) +
    facet_grid(
      rows  = vars(stimulus_label),
      cols  = vars(interaction_type),
      # Allow both x and y scales to differ between panels so that:
      # - each stimulus only shows its own badges on the y-axis
      # - Hovers and Clicks can have their own x-axis ranges
      scales = "free"
    ) +
    # Use a clean qualitative palette from paletteer (many distinct colors)
    paletteer::scale_fill_paletteer_d("ggthemes::Tableau_20") +
    labs(
      title = "Hover and click counts per badge, stacked by participant",
      x     = "Count",
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

  grDevices::png(output_path, width = 2200, height = 1400, res = 200)
  print(p)
  grDevices::dev.off()

  invisible(output_path)
}

# Allow running this script directly for quick checks.
if (identical(environment(), globalenv())) {
  args <- commandArgs(trailingOnly = TRUE)
  data_dir <- if (length(args) >= 1) args[[1]] else "data"
  out_dir  <- if (length(args) >= 2) args[[2]] else "r_output"
  generate_badge_hover_click_participant_counts_plot(data_dir = data_dir, out_dir = out_dir)
}


