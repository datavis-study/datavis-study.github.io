#!/usr/bin/env Rscript

# Preference slope chart for s1b follow-up study
# ----------------------------------------------
# - Uses `analysis/data/s1b/preferences.csv`.
# - Shows, for each stimulus (Global vs CO2) and each task
#   (Understanding vs Presenting), how the share of participants choosing
#   badges / footnotes / no preference shifts.

suppressPackageStartupMessages({
  library(tidyverse)
})

#' Generate a slope chart of s1b preferences across tasks and stimuli.
#'
#' @param data_dir   Directory where the s1b CSV lives (default: "data/s1b").
#' @param out_dir    Output directory for charts (created if missing).
#' @param input_file CSV file name inside `data_dir` (default: "preferences.csv").
#' @param output_file PNG file name inside `out_dir`.
generate_s1b_preferences_slope <- function(
  data_dir    = file.path("data", "s1b"),
  out_dir     = file.path("s1b", "r_output"),
  input_file  = "preferences.csv",
  output_file = "s1b_preferences_slope.png"
) {
  input_path  <- file.path(data_dir, input_file)
  output_path <- file.path(out_dir, output_file)

  if (!file.exists(input_path)) {
    stop("s1b preferences input file not found: ", input_path)
  }

  if (!dir.exists(out_dir)) {
    dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  }

  message("Reading s1b preference data from: ", input_path)
  df <- readr::read_csv(input_path, show_col_types = FALSE)

  # Map columns to stimulus and task
  tasks_map <- tibble::tibble(
    question = c(
      "global_understanding_choice",
      "global_presenting_choice",
      "co2_understanding_choice",
      "co2_presenting_choice"
    ),
    stimulus = c("Stimuli 1", "Stimuli 1", "Stimuli 2", "Stimuli 2"),
    task     = c("Understanding", "Presenting", "Understanding", "Presenting")
  )

  # Long format with stimulus and task information
  df_long <- df %>%
    tidyr::pivot_longer(
      cols      = tidyselect::all_of(tasks_map$question),
      names_to  = "question",
      values_to = "choice"
    ) %>%
    dplyr::left_join(tasks_map, by = "question") %>%
    dplyr::filter(!is.na(choice), trimws(choice) != "") %>%
    dplyr::mutate(
      choice = tolower(trimws(choice)),
      choice = dplyr::case_when(
        choice == "badges"        ~ "badges",
        choice == "footnotes"     ~ "footnotes",
        TRUE                       ~ "no_preference"
      ),
      choice = factor(
        choice,
        levels = c("badges", "no_preference", "footnotes")
      ),
      task = factor(
        task,
        levels = c("Understanding", "Presenting")
      )
    )

  if (nrow(df_long) == 0) {
    stop("No non-empty s1b preference responses found in: ", input_path)
  }

  # Aggregate to percentages per stimulus × task × choice.
  # Ensure that all (stimulus, task, choice) combinations exist so that also
  # \"no_preference\" has an explicit 0 → growth line when it first appears.
  df_slope <- df_long %>%
    dplyr::count(stimulus, task, choice, name = "n") %>%
    tidyr::complete(
      stimulus,
      task,
      choice,
      fill = list(n = 0)
    ) %>%
    dplyr::group_by(stimulus, task) %>%
    dplyr::mutate(
      total_n   = sum(n),
      percentage = ifelse(total_n > 0, n / total_n, 0)
    ) %>%
    dplyr::ungroup() %>%
    dplyr::select(-total_n)

  # Color mapping (match preference grid): badges = orange, footnotes = blue,
  # no preference = sand/off-white (not grey)
  colors <- c(
    "badges"        = "#B85C00",  # orange
    "no_preference" = "#E9DFD2",  # sand
    "footnotes"     = "#2B6EA5"   # blue
  )

  message("Writing s1b preference slope chart to: ", output_path)

  grDevices::png(output_path, width = 1600, height = 900, res = 200)
  on.exit(grDevices::dev.off(), add = TRUE)

  p <- ggplot(
    df_slope,
    aes(x = task, y = percentage, group = choice, color = choice)
  ) +
    geom_line(linewidth = 1.5) +
    geom_point(size = 3) +
    facet_wrap(~ stimulus) +
    scale_y_continuous(
      labels = function(x) paste0(round(x * 100), "%"),
      limits = c(0, 1)
    ) +
    # Use full x-axis labels for paper readability
    scale_x_discrete(
      labels = c(
        "Understanding" = "Understanding",
        "Presenting"    = "Presentation"
      )
    ) +
    scale_color_manual(
      values = colors,
      breaks = c("badges", "no_preference", "footnotes"),
      labels = c("Prefer Badges", "No preference", "Prefer Footnotes"),
      name   = NULL
    ) +
    labs(title = NULL, x = NULL, y = NULL) +
    theme_minimal(base_size = 10) +
    theme(
      legend.position      = "bottom",
      legend.key.width     = unit(0.8, "lines"),
      legend.key.height    = unit(0.4, "lines"),
      legend.text          = element_text(size = 6),
      panel.grid.major.x   = element_blank(),
      strip.text           = element_text(size = 10, face = "bold"),
      axis.text.x          = element_text(size = 7, margin = margin(t = 2)),
      axis.text.y          = element_text(size = 8)
    )

  print(p)

  invisible(output_path)
}


# Allow running this script directly for quick checks.
if (sys.nframe() == 1) {
  args <- commandArgs(trailingOnly = TRUE)
  data_dir <- if (length(args) >= 1) args[[1]] else file.path("data", "s1b")
  out_dir  <- if (length(args) >= 2) args[[2]] else file.path("s1b", "r_output")
  generate_s1b_preferences_slope(data_dir = data_dir, out_dir = out_dir)
}
