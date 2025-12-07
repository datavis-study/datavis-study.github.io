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
      id == "co2-emissions" ~ "Stimuli: CO2 Emissions",
      id == "global-warming-projection" ~ "Stimuli: Global Warming Projection",
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

  badge_order_df <- badge_order_df %>%
    dplyr::select(stimulus_label, badgeLabelDisplay, badgeLabelOrder)

  df <- df %>%
    dplyr::left_join(badge_order_df, by = c("stimulus_label", "badgeLabelDisplay"))

  # Ensure the badges with the largest total hover counts appear at the *top*
  # of each facet, and participants with the largest overall contribution are
  # stacked first along the x‑axis for easier visual comparison.
  participant_order <- df %>%
    dplyr::group_by(participantDisplay) %>%
    dplyr::summarise(
      totalHover = sum(hoverCount, na.rm = TRUE),
      .groups = "drop"
    ) %>%
    dplyr::arrange(dplyr::desc(totalHover)) %>%
    dplyr::pull(participantDisplay)

  df <- df %>%
    dplyr::mutate(
      badgeLabelOrder   = forcats::fct_rev(badgeLabelOrder),
      participantDisplay = factor(participantDisplay, levels = participant_order)
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
    geom_col(
      width    = 0.7,
      position = position_stack(reverse = TRUE)
    ) +
    geom_text(
      aes(label = hoverCount),
      position = position_stack(vjust = 0.5, reverse = TRUE),
      color    = "black",
      size     = 3
    ) +
    facet_grid(
      rows   = vars(stimulus_label),
      scales = "free_y",
      space  = "free_y"
    ) +
    scale_x_continuous(
      breaks = seq(0, max_break, by = 2),
      limits = c(0, max_break)
    ) +
    # Use a light qualitative palette so labels remain readable inside bars
    scale_fill_brewer(palette = "Set2") +
    labs(
      x    = "Hover count",
      y    = NULL,
      fill = "Participant"
    ) +
    theme_minimal(base_size = 12) +
    theme(
      legend.position       = "bottom",
      axis.text.y           = element_text(size = 10),
      axis.text.x           = element_text(size = 10),
      # Horizontal grid lines off; vertical grid lines on starting at x = 0
      panel.grid.major.y    = element_blank(),
      panel.grid.minor.y    = element_blank(),
      panel.grid.major.x    = element_line(colour = "grey95"),
      panel.grid.minor.x    = element_blank()
    ) +
    guides(
      fill = guide_legend(nrow = 1, byrow = TRUE)
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


