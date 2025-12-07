#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(tidyverse)
})

#' Generate stacked total drawer-open time bars per badge, stacked by participant.
#'
#' Data source:
#'   - stimulus_badge_participant_metrics.csv
#'     (one row per stimulus × participant × badge with drawer/time metrics)
#'
#' For each stimulus:
#'   - y-axis: badge label
#'   - x-axis: totalDrawerOpenTime (sum across participants)
#'   - fill: participant (readable id when available)
#'
#' @param data_dir Directory where the CSV files live.
#' @param out_dir  Output directory for charts (created if missing).
generate_badge_drawer_time_participant_plot <- function(
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
    "totalDrawerOpenTime"
  )
  if (!all(required_cols %in% names(df))) {
    warning(
      "Missing required columns in badge participant metrics. Expected: ",
      paste(required_cols, collapse = ", ")
    )
    return(invisible(NULL))
  }

  # Keep only rows with non-zero total drawer open time
  df <- df %>%
    dplyr::mutate(
      totalDrawerOpenTime = as.numeric(totalDrawerOpenTime)
    ) %>%
    dplyr::filter(!is.na(totalDrawerOpenTime), totalDrawerOpenTime > 0)

  if (nrow(df) == 0) {
    warning("No rows with totalDrawerOpenTime > 0; nothing to plot.")
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

  # Order badges within each stimulus by total drawer time (descending)
  badge_order_df <- df %>%
    dplyr::group_by(stimulus_label, badgeLabelDisplay) %>%
    dplyr::summarise(
      totalTime = sum(totalDrawerOpenTime, na.rm = TRUE),
      .groups = "drop"
    ) %>%
    dplyr::group_by(stimulus_label) %>%
    dplyr::arrange(dplyr::desc(totalTime), .by_group = TRUE) %>%
    dplyr::mutate(
      badgeLabelOrder = factor(badgeLabelDisplay, levels = badgeLabelDisplay)
    ) %>%
    dplyr::ungroup()

  max_total_time <- max(badge_order_df$totalTime, na.rm = TRUE)

  badge_order_df <- badge_order_df %>%
    dplyr::select(stimulus_label, badgeLabelDisplay, badgeLabelOrder)

  df <- df %>%
    dplyr::left_join(badge_order_df, by = c("stimulus_label", "badgeLabelDisplay"))

  # Participant colours/order are kept consistent across all charts by using
  # a single global (alphabetical) ordering.
  participant_order <- df %>%
    dplyr::distinct(participantDisplay) %>%
    dplyr::arrange(participantDisplay) %>%
    dplyr::pull(participantDisplay)

  df <- df %>%
    dplyr::mutate(
      badgeLabelOrder    = forcats::fct_rev(badgeLabelOrder),
      participantDisplay = factor(participantDisplay, levels = participant_order)
    )

  if (!is.finite(max_total_time) || max_total_time < 0) {
    max_total_time <- 0
  }
  max_even  <- ceiling(max_total_time / 2) * 2
  max_break <- max_even + if (max_total_time > 0) 2 else 0
  break_step <- dplyr::case_when(
    max_total_time <= 10 ~ 2,
    max_total_time <= 30 ~ 5,
    max_total_time <= 60 ~ 10,
    TRUE ~ 20
  )

  output_path <- file.path(out_dir, "badge_drawer_time_participant_stacked.png")
  message("Writing Badge Drawer Time Participant stacked plot to: ", output_path)

  p <- ggplot(
    df,
    aes(
      x    = totalDrawerOpenTime,
      y    = badgeLabelOrder,
      fill = participantDisplay
    )
  ) +
    geom_col(
      width    = 0.7,
      position = position_stack(reverse = TRUE)
    ) +
    geom_text(
      aes(label = ifelse(totalDrawerOpenTime >= 2, round(totalDrawerOpenTime, 1), "")),
      position = position_stack(vjust = 0.5, reverse = TRUE),
      color    = "black",
      size     = 2.5
    ) +
    facet_wrap(
      ~ stimulus_label,
      ncol   = 1,
      scales = "free_y"
    ) +
    scale_x_continuous(
      breaks = seq(0, max_break, by = break_step),
      limits = c(0, max_break)
    ) +
    scale_fill_brewer(palette = "Set3") +
    labs(
      title = NULL,
      x     = "Total drawer open time (s)",
      y     = NULL,
      fill  = "Participant"
    ) +
    theme_minimal(base_size = 12) +
    theme(
      legend.position       = "bottom",
      axis.text.y           = element_text(size = 10),
      axis.text.x           = element_text(size = 10),
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

if (identical(environment(), globalenv())) {
  args <- commandArgs(trailingOnly = TRUE)
  data_dir <- if (length(args) >= 1) args[[1]] else "data"
  out_dir  <- if (length(args) >= 2) args[[2]] else "r_output"
  generate_badge_drawer_time_participant_plot(data_dir = data_dir, out_dir = out_dir)
}


