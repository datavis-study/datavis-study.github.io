#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(tidyverse)
  library(paletteer)
})

#' Generate a single overview PNG with all badge interactions.
#'
#' Layout:
#'   - Columns: one per stimulus (e.g., CO2 vs Global Warming Projection)
#'   - Rows:    one per interaction metric:
#'                * Click count
#'                * Hover count
#'                * Total drawer open time
#'                * Total hover time
#'
#' Each panel shows stacked bars per badge, coloured by participant, matching
#' the style of the individual interaction charts.
#'
#' @param data_dir  Directory where the CSV files live.
#' @param out_dir   Output directory for charts (created if missing).
#' @param input_file Name of the participant-level metrics CSV.
generate_badge_interactions_overview_plot <- function(
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

  message("Reading Badge participant metrics for overview from: ", input_path)
  df_raw <- readr::read_csv(input_path, show_col_types = FALSE)

  required_base <- c(
    "stimulusId",
    "participantId",
    "participantReadableId",
    "badgeId",
    "badgeLabel"
  )

  if (!all(required_base %in% names(df_raw))) {
    warning(
      "Missing required base columns in badge participant metrics. Expected: ",
      paste(required_base, collapse = ", ")
    )
    return(invisible(NULL))
  }

  # Helper for pretty stimulus labels using plain ASCII for CO2.
  pretty_stimulus <- function(id) {
    dplyr::case_when(
      id == "co2-emissions" ~ "Stimuli: CO2 Emissions",
      id == "global-warming-projection" ~ "Stimuli: Global Warming Projection",
      TRUE ~ as.character(id)
    )
  }

  # Common cleaning shared by all interaction metrics.
  df_base <- df_raw %>%
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
      ),
      participantDisplay = dplyr::if_else(
        !is.na(participantReadableId) & trimws(participantReadableId) != "",
        trimws(participantReadableId),
        trimws(participantId)
      ),
      stimulus_label = pretty_stimulus(stimulusId)
    ) %>%
    dplyr::filter(!is.na(badgeLabelDisplay), badgeLabelDisplay != "")

  if (nrow(df_base) == 0) {
    warning("No badges with valid labels after cleaning in overview.")
    return(invisible(NULL))
  }

  # Global participant ordering so colours are consistent across all panels.
  participant_order <- df_base %>%
    dplyr::distinct(participantDisplay) %>%
    dplyr::arrange(participantDisplay) %>%
    dplyr::pull(participantDisplay)

  df_base <- df_base %>%
    dplyr::mutate(
      participantDisplay = factor(participantDisplay, levels = participant_order)
    )

  metric_dfs <- list()

  # Helper to build a metric-specific long data frame
  build_metric_df <- function(df, value_col, metric_label) {
    if (!value_col %in% names(df)) {
      return(NULL)
    }
    out <- df %>%
      dplyr::mutate(
        value = as.numeric(.data[[value_col]])
      ) %>%
      dplyr::filter(!is.na(value), value > 0)

    # Keep only badges that appear in more than one stimulus so that
    # the overview focuses on badges that are comparable across stimuli.
    shared_badges <- out %>%
      dplyr::distinct(badgeLabelDisplay, stimulus_label) %>%
      dplyr::count(badgeLabelDisplay, name = "n_stimuli") %>%
      dplyr::filter(n_stimuli > 1) %>%
      dplyr::pull(badgeLabelDisplay)

    out <- out %>%
      dplyr::filter(badgeLabelDisplay %in% shared_badges)

    if (nrow(out) == 0) {
      return(NULL)
    }

    # Order badges within each stimulus by total value (descending),
    # so the most-interacted badges appear at the top.
    badge_order_df <- out %>%
      dplyr::group_by(stimulus_label, badgeLabelDisplay) %>%
      dplyr::summarise(
        totalValue = sum(value, na.rm = TRUE),
        .groups = "drop"
      ) %>%
      dplyr::group_by(stimulus_label) %>%
      dplyr::arrange(dplyr::desc(totalValue), .by_group = TRUE) %>%
      dplyr::mutate(
        badgeLabelOrder = factor(badgeLabelDisplay, levels = badgeLabelDisplay)
      ) %>%
      dplyr::ungroup() %>%
      dplyr::select(stimulus_label, badgeLabelDisplay, badgeLabelOrder)

    out <- out %>%
      dplyr::left_join(badge_order_df, by = c("stimulus_label", "badgeLabelDisplay")) %>%
      dplyr::mutate(
        badgeLabelOrder = forcats::fct_rev(badgeLabelOrder),
        metric          = metric_label
      )

    out
  }

  metric_dfs[["clicks"]] <- build_metric_df(
    df_base,
    value_col   = "clickCount",
    metric_label = "Click count"
  )

  metric_dfs[["hovers"]] <- build_metric_df(
    df_base,
    value_col   = "hoverCount",
    metric_label = "Hover count"
  )

  metric_dfs[["drawer_time"]] <- build_metric_df(
    df_base,
    value_col   = "totalDrawerOpenTime",
    metric_label = "Drawer open time (s)"
  )

  metric_dfs[["hover_time"]] <- build_metric_df(
    df_base,
    value_col   = "totalHoverTime",
    metric_label = "Hover time (s)"
  )

  metric_dfs <- purrr::compact(metric_dfs)

  if (length(metric_dfs) == 0) {
    warning("No interaction metrics with non-zero values found for overview.")
    return(invisible(NULL))
  }

  plot_df <- dplyr::bind_rows(metric_dfs) %>%
    dplyr::mutate(
      metric = factor(
        metric,
        levels = c(
          "Click count",
          "Hover count",
          "Drawer open time (s)",
          "Hover time (s)"
        )
      )
    )

  # Labels inside the stacks: counts as integers, times with one decimal
  plot_df <- plot_df %>%
    dplyr::mutate(
      is_time_metric = metric %in% c("Drawer open time (s)", "Hover time (s)"),
      label_value = dplyr::case_when(
        !is_time_metric               ~ as.character(round(value, 0)),
        is_time_metric & value >= 2   ~ sprintf("%.1f", value),
        TRUE                          ~ ""
      )
    )

  output_path <- file.path(out_dir, "badge_interactions_overview.png")
  message("Writing Badge Interactions overview plot to: ", output_path)

  p <- ggplot(
    plot_df,
    aes(
      x    = value,
      y    = badgeLabelOrder,
      fill = participantDisplay
    )
  ) +
    geom_col(
      width    = 0.7,
      position = position_stack(reverse = TRUE)
    ) +
    geom_text(
      aes(label = label_value),
      position = position_stack(vjust = 0.5, reverse = TRUE),
      color    = "black",
      size     = 2.5
    ) +
    facet_grid(
      rows = vars(metric),
      cols = vars(stimulus_label),
      # Give each panel its own x-axis range appropriate to the metric,
      # and its own y-axis levels per stimulus.
      scales = "free"
    ) +
    scale_fill_paletteer_d("ggthemes::Tableau_20") +
    labs(
      title = NULL,
      x     = "Interaction value (count / seconds)",
      y     = NULL,
      fill  = "Participant"
    ) +
    theme_minimal(base_size = 11) +
    theme(
      legend.position       = "bottom",
      legend.key.size       = unit(0.4, "lines"),
      strip.text.x          = element_text(size = 10),
      strip.text.y          = element_text(size = 10),
      axis.text.y           = element_text(size = 8),
      axis.text.x           = element_text(size = 8),
      panel.grid.major.y    = element_blank(),
      panel.grid.minor.y    = element_blank(),
      panel.grid.major.x    = element_line(colour = "grey95"),
      panel.grid.minor.x    = element_blank()
    ) +
    guides(
      fill = guide_legend(nrow = 1, byrow = TRUE)
    )

  grDevices::png(output_path, width = 2000, height = 1600, res = 200)
  print(p)
  grDevices::dev.off()

  invisible(output_path)
}


# Allow running this script directly for quick checks.
if (identical(environment(), globalenv())) {
  args <- commandArgs(trailingOnly = TRUE)
  data_dir <- if (length(args) >= 1) args[[1]] else "data"
  out_dir  <- if (length(args) >= 2) args[[2]] else "r_output"
  generate_badge_interactions_overview_plot(data_dir = data_dir, out_dir = out_dir)
}

