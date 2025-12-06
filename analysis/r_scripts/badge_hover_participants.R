#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(tidyverse)
  library(paletteer)
})

#' Generate horizontal stacked bars of participant hover activity per badge.
#'
#' Each bar is a badge (on the y-axis), stacked by number of participants who
#' hovered that badge at least once vs. those who did not, for each stimulus.
#'
#' This uses:
#'   - `stimulus_badge_metrics.csv` for `hoverParticipantCount` per badge
#'   - `participants.csv` to estimate the total number of participants who saw
#'     each stimulus (firstStimulus/secondStimulus)
#'
#' @param data_dir          Directory where the CSV files live.
#' @param out_dir           Output directory for charts (created if missing).
#' @param metrics_file      Badge metrics CSV (default: stimulus_badge_metrics.csv).
#' @param participants_file Participants CSV (default: participants.csv).
generate_badge_hover_participant_plot <- function(
  data_dir          = "data",
  out_dir           = "r_output",
  metrics_file      = "stimulus_badge_metrics.csv",
  participants_file = "participants.csv"
) {
  metrics_path      <- file.path(data_dir, metrics_file)
  participants_path <- file.path(data_dir, participants_file)

  if (!file.exists(metrics_path)) {
    warning("Badge metrics input file not found: ", metrics_path)
    return(invisible(NULL))
  }

  if (!file.exists(participants_path)) {
    warning("Participants file not found: ", participants_path)
    return(invisible(NULL))
  }

  if (!dir.exists(out_dir)) {
    dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  }

  message("Reading Badge metrics from: ", metrics_path)
  metrics <- readr::read_csv(metrics_path, show_col_types = FALSE)

  message("Reading participants from: ", participants_path)
  participants <- readr::read_csv(participants_path, show_col_types = FALSE)

  # Ensure expected columns exist
  required_metrics_cols <- c("stimulusId", "badgeLabel", "hoverParticipantCount")
  if (!all(required_metrics_cols %in% names(metrics))) {
    warning(
      "Missing required columns in metrics file. Expected: ",
      paste(required_metrics_cols, collapse = ", ")
    )
    return(invisible(NULL))
  }

  required_participant_cols <- c("participantId", "completed", "firstStimulus", "secondStimulus")
  if (!all(required_participant_cols %in% names(participants))) {
    warning(
      "Missing required columns in participants file. Expected: ",
      paste(required_participant_cols, collapse = ", ")
    )
    return(invisible(NULL))
  }

  # Restrict to completed participants (to match analysis exports)
  participants <- participants %>%
    dplyr::filter(is.na(completed) | completed == TRUE)

  # For each stimulus, count how many unique participants saw it (first or second)
  participants_long <- participants %>%
    dplyr::select(participantId, firstStimulus, secondStimulus) %>%
    tidyr::pivot_longer(
      cols      = c(firstStimulus, secondStimulus),
      names_to  = "order",
      values_to = "stimulusId"
    ) %>%
    dplyr::filter(!is.na(stimulusId))

  stimulus_totals <- participants_long %>%
    dplyr::group_by(stimulusId) %>%
    dplyr::summarise(
      totalParticipants = dplyr::n_distinct(participantId),
      .groups = "drop"
    )

  if (nrow(stimulus_totals) == 0) {
    warning("No stimulus totals could be computed from participants.")
    return(invisible(NULL))
  }

  # Merge totals into metrics
  df <- metrics %>%
    dplyr::left_join(stimulus_totals, by = "stimulusId") %>%
    dplyr::filter(!is.na(totalParticipants))

  if (nrow(df) == 0) {
    warning("No overlapping stimuli between metrics and participants.")
    return(invisible(NULL))
  }

  # Clamp counts to sensible ranges
  df <- df %>%
    dplyr::mutate(
      hoverParticipantCount = pmax(
        pmin(hoverParticipantCount, totalParticipants),
        0
      ),
      nonHoverParticipantCount = pmax(
        totalParticipants - hoverParticipantCount,
        0
      )
    )

  # Display label per badge, normalising any CO₂-like text to plain ASCII "CO2"
  df <- df %>%
    dplyr::mutate(
      badgeLabelDisplay = dplyr::if_else(
        !is.na(badgeLabel) & trimws(badgeLabel) != "",
        trimws(badgeLabel),
        badgeLabel
      ),
      badgeLabelDisplay = stringr::str_replace_all(
        badgeLabelDisplay,
        pattern = "\u2082",
        replacement = "2"
      )
    )

  df <- df %>%
    dplyr::filter(!is.na(badgeLabelDisplay), badgeLabelDisplay != "")

  if (nrow(df) == 0) {
    warning("No badges with valid labels after cleaning.")
    return(invisible(NULL))
  }

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

  # Long format for stacked bars
  df_long <- df %>%
    dplyr::select(
      stimulusId,
      stimulus_label,
      badgeLabelDisplay,
      hoverParticipantCount,
      nonHoverParticipantCount
    ) %>%
    tidyr::pivot_longer(
      cols      = c(hoverParticipantCount, nonHoverParticipantCount),
      names_to  = "hover_status",
      values_to = "count"
    ) %>%
    dplyr::mutate(
      hover_status = factor(
        hover_status,
        levels = c("nonHoverParticipantCount", "hoverParticipantCount"),
        labels = c("Did not hover", "Hovered")
      )
    )

  if (nrow(df_long) == 0) {
    warning("No data available for plotting after reshaping.")
    return(invisible(NULL))
  }

  # Order badges by number of hovering participants (descending) within stimulus
  df_long <- df_long %>%
    dplyr::group_by(stimulus_label, badgeLabelDisplay) %>%
    dplyr::mutate(
      hoverers = max(dplyr::if_else(hover_status == "Hovered", count, 0))
    ) %>%
    dplyr::ungroup()

  badge_order <- df_long %>%
    dplyr::distinct(stimulus_label, badgeLabelDisplay, hoverers) %>%
    dplyr::arrange(stimulus_label, dplyr::desc(hoverers)) %>%
    dplyr::group_by(stimulus_label) %>%
    dplyr::mutate(
      badgeLabelOrder = factor(
        badgeLabelDisplay,
        levels = badgeLabelDisplay
      )
    ) %>%
    dplyr::ungroup() %>%
    dplyr::select(stimulus_label, badgeLabelDisplay, badgeLabelOrder)

  df_long <- df_long %>%
    dplyr::left_join(badge_order, by = c("stimulus_label", "badgeLabelDisplay"))

  # One chart per stimulus so each stimulus gets its own PNG
  stimulus_ids <- df_long %>%
    dplyr::distinct(stimulusId, stimulus_label)

  for (i in seq_len(nrow(stimulus_ids))) {
    stim_id    <- stimulus_ids$stimulusId[[i]]
    stim_label <- stimulus_ids$stimulus_label[[i]]

    df_stim <- df_long %>%
      dplyr::filter(stimulusId == stim_id)

    if (nrow(df_stim) == 0) {
      next
    }

    slug <- gsub("[^A-Za-z0-9_-]+", "_", stim_id)
    output_path <- file.path(
      out_dir,
      paste0("badge_hover_participant_stacked_", slug, ".png")
    )
    message("Writing Participant Hover stacked plot for ", stim_id, " to: ", output_path)

    max_count <- max(df_stim$count, na.rm = TRUE)
    if (!is.finite(max_count) || max_count < 0) {
      max_count <- 0
    }
    # Simple integer axis: 0,1,2,3,...
    max_break <- ceiling(max_count)

    p <- ggplot(
      df_stim,
      aes(
        x    = count,
        y    = badgeLabelOrder,
        fill = hover_status
      )
    ) +
      geom_col(width = 0.7) +
      scale_x_continuous(
        breaks = seq(0, max_break, by = 1),
        limits = c(0, max_break)
      ) +
      # Clean, neutral two-color palette via paletteer
      paletteer::scale_fill_paletteer_d("RColorBrewer::Set2") +
      labs(
        title = paste0("Participant hover activity by badge — ", stim_label),
        x     = "Number of participants",
        y     = NULL,
        fill  = "Hover status"
      ) +
      theme_minimal(base_size = 12) +
      theme(
        legend.position       = "bottom",
        axis.text.y           = element_text(size = 10),
        axis.text.x           = element_text(size = 10),
        panel.grid.major.y    = element_blank(),
        # Only keep one vertical gridline per integer tick (no minor x-grid)
        panel.grid.minor.x    = element_blank()
      )

    grDevices::png(output_path, width = 1600, height = 1200, res = 200)
    print(p)
    grDevices::dev.off()
  }

  invisible(NULL)
}

# Allow running this script directly:
if (identical(environment(), globalenv())) {
  args <- commandArgs(trailingOnly = TRUE)
  data_dir <- if (length(args) >= 1) args[[1]] else "data"
  out_dir  <- if (length(args) >= 2) args[[2]] else "r_output"
  generate_badge_hover_participant_plot(data_dir = data_dir, out_dir = out_dir)
}


