#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(tidyverse)
  library(paletteer)
})

#' Generate stacked hover-count bars per badge, stacked by participant.
#'
#' Data source:
#'   - stimulus_badge_participant_metrics.csv
#'     (one row per stimulus × participant × badge with hoverCount, etc.)
#'
#' For each stimulus:
#'   - y-axis: badge label
#'   - x-axis: hoverCount (sum across participants)
#'   - fill: participant (readable id when available)
#'
#' @param data_dir Directory where the CSV files live.
#' @param out_dir  Output directory for charts (created if missing).
generate_badge_hover_participant_counts_plot <- function(
  data_dir = "data",
  out_dir  = "r_output",
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
    "hoverCount"
  )
  if (!all(required_cols %in% names(df))) {
    warning(
      "Missing required columns in badge participant metrics. Expected: ",
      paste(required_cols, collapse = ", ")
    )
    return(invisible(NULL))
  }

  # Keep only rows with non-zero hover counts so stacks represent actual activity
  df <- df %>%
    dplyr::mutate(
      hoverCount = as.numeric(hoverCount)
    ) %>%
    dplyr::filter(!is.na(hoverCount), hoverCount > 0)

  if (nrow(df) == 0) {
    warning("No rows with hoverCount > 0; nothing to plot.")
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

  # Order badges within each stimulus by total hover count (descending),
  # so the most-interacted badges appear at the top, and compute total
  # hover counts per badge for axis scaling.
  badge_order_df <- df %>%
    dplyr::group_by(stimulus_label, badgeLabelDisplay) %>%
    dplyr::summarise(
      totalHover = sum(hoverCount, na.rm = TRUE),
      .groups = "drop"
    ) %>%
    dplyr::group_by(stimulus_label) %>%
    dplyr::arrange(dplyr::desc(totalHover), .by_group = TRUE) %>%
    dplyr::mutate(
      badgeLabelOrder = factor(badgeLabelDisplay, levels = badgeLabelDisplay)
    ) %>%
    dplyr::ungroup()

  # Global max over *stacked* hover counts per badge (not per participant)
  max_total_hover <- max(badge_order_df$totalHover, na.rm = TRUE)

  # Data frame for total-per-badge labels at the end of each bar
  total_labels <- badge_order_df %>%
    dplyr::select(stimulus_label, badgeLabelOrder, totalHover)

  badge_order_df <- badge_order_df %>%
    dplyr::select(stimulus_label, badgeLabelDisplay, badgeLabelOrder)

  df <- df %>%
    dplyr::left_join(badge_order_df, by = c("stimulus_label", "badgeLabelDisplay"))

  # Build a soft monochrome (blue-grey) palette with one distinct shade per
  # participant. This keeps everything in a single calm hue while still
  # differentiating people without harsh contrasts.
  participant_levels <- sort(unique(df$participantDisplay))
  n_participants     <- length(participant_levels)
  participant_colors <- stats::setNames(
    grDevices::colorRampPalette(c("#e3e8f0", "#4c6a8a"))(n_participants),
    participant_levels
  )

  # Single chart: both stimuli in one figure, faceted vertically.
  # Axis is based on stacked hover counts per badge so the bar lengths
  # and x-axis labels match.
  if (!is.finite(max_total_hover) || max_total_hover < 0) {
    max_total_hover <- 0
  }
  # Even-integer axis that always extends at least one full step beyond the max.
  # Example: max 9 -> ticks up to 12; max 21 -> ticks up to 24.
  max_even  <- ceiling(max_total_hover / 2) * 2
  max_break <- max_even + if (max_total_hover > 0) 2 else 0

  output_path <- file.path(out_dir, "badge_hover_participant_counts_stacked.png")
  message("Writing Badge Hover Participant Counts stacked plot to: ", output_path)

  p <- ggplot(
    df,
    aes(
      x    = hoverCount,
      y    = badgeLabelOrder,
      fill = participantDisplay
    )
  ) +
    geom_col(width = 0.7) +
    # Add per-participant hover counts as labels centered in each stacked segment
    geom_text(
      aes(label = hoverCount),
      position = position_stack(vjust = 0.5),
      color    = "black",
      size     = 3,
      fontface = "bold"
    ) +
    # Add total hover count per badge at the end of each full bar
    geom_text(
      data = total_labels,
      inherit.aes = FALSE,
      aes(
        x     = totalHover,
        y     = badgeLabelOrder,
        label = totalHover
      ),
      # Place the total label a bit further to the right of the bar end
      hjust    = -0.4,
      color    = "black",
      size     = 3,
      fontface = "bold"
    ) +
    facet_wrap(
      ~ stimulus_label,
      ncol   = 1,
      scales = "free_y"
    ) +
    scale_x_continuous(
      breaks = seq(0, max_break, by = 2),
      limits = c(0, max_break)
    ) +
    # Soft monochrome blue-grey palette for participants
    scale_fill_manual(values = participant_colors) +
    labs(
      title = "Hover counts per badge, stacked by participant",
      x     = "Hover count",
      y     = NULL,
      fill  = "Participant"
    ) +
    theme_minimal(base_size = 12) +
    theme(
      legend.position       = "bottom",
      axis.text.y           = element_text(size = 10),
      # Hide x-axis tick labels and ticks since values are now shown via labels
      axis.text.x           = element_blank(),
      axis.ticks.x          = element_blank(),
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
  generate_badge_hover_participant_counts_plot(data_dir = data_dir, out_dir = out_dir)
}


