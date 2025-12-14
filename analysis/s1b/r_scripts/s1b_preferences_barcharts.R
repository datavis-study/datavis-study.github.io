#!/usr/bin/env Rscript

# Preference grid for s1b follow-up study
# ---------------------------------------
# This script implements the "preference grid" you sketched:
# - Left: individual participant choices (one square per task × participant)
# - Right: total counts (one square = one person)
# for the four preference tasks in `preferences.csv`.

suppressPackageStartupMessages({
  library(tidyverse)
  library(stringr)
})

#' Generate preference grid plot for the s1b follow-up study.
#'
#' @param data_dir   Directory where the s1b CSV lives (default: "data/s1b").
#' @param out_dir    Output directory for charts (created if missing).
#' @param input_file CSV file name inside `data_dir` (default: "preferences.csv").
#' @param output_file PNG file name inside `out_dir`.
generate_s1b_preferences_barcharts <- function(
  data_dir    = file.path("data", "s1b"),
  out_dir     = file.path("s1b", "r_output"),
  input_file  = "preferences.csv",
  output_file = "s1b_preferences_overall.png"
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

  # 1. Tasks and participant ordering ----------------------------------------
  tasks <- c("global_understanding", "global_presenting", "co2_understanding", "co2_presenting")

  # Ensure a stable group ordering: badges -> footnotes
  df <- df %>%
    mutate(group = factor(group, levels = c("badges", "footnotes")))

  # Helper to score choices so that sorting by this score yields a smooth
  # left-to-right colour gradient (badges > no_preference > footnotes).
  score_choice <- function(x) {
    dplyr::case_when(
      x == "badges"        ~ 2L,
      x == "no_preference" ~ 1L,
      x == "footnotes"     ~ 0L,
      TRUE                 ~ 1L
    )
  }

  df_sorted <- df %>%
    mutate(
      s_global_understanding = score_choice(global_understanding_choice),
      s_global_presenting    = score_choice(global_presenting_choice),
      s_co2_understanding    = score_choice(co2_understanding_choice),
      s_co2_presenting       = score_choice(co2_presenting_choice)
    ) %>%
    arrange(
      group,
      desc(s_global_understanding),
      desc(s_global_presenting),
      desc(s_co2_understanding),
      desc(s_co2_presenting)
    ) %>%
    mutate(participant_rank = row_number()) %>%
    select(-starts_with("s_"))

  # X-offset per group to leave a visual gap
  df_positions <- df_sorted %>%
    mutate(
      x_offset = if_else(group == levels(group)[1], 0, 0.8),
      x_main   = participant_rank + x_offset
    ) %>%
    select(participantId, group, participant_rank, x_main)

  # 2. Main grid (individual choices) ----------------------------------------
  main_grid <- df_sorted %>%
    select(participantId, group, participant_rank, ends_with("choice")) %>%
    left_join(df_positions, by = c("participantId", "group", "participant_rank")) %>%
    pivot_longer(cols = ends_with("choice"), names_to = "task_raw", values_to = "choice") %>%
    mutate(
      task_name = str_remove(task_raw, "_choice"),
      # y rows (reverse so first task is at top)
      y = match(task_name, rev(tasks)),
      x = x_main
    )

  # 3. Summary grid (totals on the right) ------------------------------------
  # Start summary squares a bit to the right of the main grid
  max_main_x <- max(main_grid$x, na.rm = TRUE)
  start_summary_x <- max_main_x + 3

  summary_grid <- main_grid %>%
    group_by(y, task_name, choice) %>%
    summarise(count = n(), .groups = "drop") %>%
    group_by(y, task_name) %>%
    mutate(
      # Order choices so that on the x-axis we see
      # all orange (badges), then grey (no preference), then blue (footnotes)
      choice = factor(choice, levels = c("badges", "no_preference", "footnotes"))
    ) %>%
    arrange(choice) %>%
    tidyr::uncount(count, .id = "id") %>%
    group_by(y) %>%
    mutate(
      x = start_summary_x + (row_number() - 1) * 1.1
    ) %>%
    ungroup() %>%
    mutate(type = "summary")

  plot_data <- bind_rows(
    main_grid %>% mutate(type = "main"),
    summary_grid
  )

  # 4. Colors and group label positions --------------------------------------
  colors <- c(
    "badges"        = "#F28E2B",  # orange
    "no_preference" = "#B0B0B0",  # grey
    "footnotes"     = "#4E79A7"   # blue
  )

  group_labels <- main_grid %>%
    distinct(participantId, group, participant_rank, x) %>%
    group_by(group) %>%
    summarise(avg_x = mean(x), .groups = "drop")

  badges_x    <- group_labels$avg_x[group_labels$group == "badges"]
  footnotes_x <- group_labels$avg_x[group_labels$group == "footnotes"]

  split_x <- if (length(badges_x) == 1 && length(footnotes_x) == 1) {
    (badges_x + footnotes_x) / 2
  } else {
    max_main_x / 2
  }

  # 5. Build plot (compact, clean, \"scientific\") -----------------------------
  y_max <- length(tasks)
  max_blocks_per_row <- summary_grid %>%
    count(y, name = "blocks") %>%
    summarise(max(blocks), .groups = "drop") %>%
    pull()

  end_summary_x <- start_summary_x + (max_blocks_per_row - 1) * 1.1
  x_min <- -3
  x_max <- end_summary_x + 3

  p <- ggplot(plot_data, aes(x = x, y = y)) +
    # Squares
    geom_tile(aes(fill = choice), width = 0.85, height = 0.85) +
    scale_fill_manual(
      values = colors,
      breaks = c("badges", "no_preference", "footnotes"),
      labels = c("Badges", "No preference", "Footnotes"),
      drop   = FALSE
    ) +

    # Row labels (tasks) on the left
    geom_text(
      data = distinct(plot_data, y, task_name),
      aes(
        x     = x_min + 0.4,
        label = dplyr::case_when(
          task_name == "global_understanding" ~ "Stimuli 1\nUnderstanding",
          task_name == "global_presenting"    ~ "Stimuli 1\nPresenting",
          task_name == "co2_understanding"    ~ "Stimuli 2\nUnderstanding",
          task_name == "co2_presenting"       ~ "Stimuli 2\nPresenting",
          TRUE                                ~ str_to_title(str_replace(task_name, "_", "\n"))
        )
      ),
      hjust    = 1,
      vjust    = 0.5,
      fontface = "plain",
      size     = 3.0,
      color    = "#333333"
    ) +

    # Group labels (top)
    { if (!is.na(badges_x)) annotate("text", x = badges_x, y = y_max + 0.6,
                                     label = "Assigned badges", fontface = "plain",
                                     size = 3.0, color = "#555555") } +
    { if (!is.na(footnotes_x)) annotate("text", x = footnotes_x, y = y_max + 0.6,
                                        label = "Assigned footnotes", fontface = "plain",
                                        size = 3.0, color = "#555555") } +

    # Split line between groups
    annotate("segment",
             x = split_x, xend = split_x,
             y = 0.5,    yend = y_max + 0.5,
             linetype = "dotted", color = "grey70") +

    coord_fixed() +
    theme_void() +
    theme(
      legend.position = "bottom",
      legend.title    = element_blank(),
      legend.text     = element_text(size = 7),
      plot.title      = element_text(face = "plain", size = 10, hjust = 0.5),
      plot.margin     = margin(8, 8, 8, 8)
    ) +
    scale_y_continuous(limits = c(0, y_max + 1.5), breaks = 1:y_max) +
    scale_x_continuous(limits = c(x_min, x_max)) +
    labs(title = NULL)

  message("Writing s1b preferences grid to: ", output_path)
  grDevices::png(output_path, width = 1800, height = 1000, res = 200)
  print(p)
  grDevices::dev.off()

  invisible(output_path)
}


# Allow running this script directly for quick checks.
if (sys.nframe() == 1) {
  args <- commandArgs(trailingOnly = TRUE)
  data_dir <- if (length(args) >= 1) args[[1]] else file.path("data", "s1b")
  out_dir  <- if (length(args) >= 2) args[[2]] else file.path("s1b", "r_output")
  generate_s1b_preferences_barcharts(data_dir = data_dir, out_dir = out_dir)
}
