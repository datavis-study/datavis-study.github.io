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
  # Desired Y order (top → bottom):
  #   Stimuli 1 – Understanding
  #   Stimuli 2 – Understanding
  #   Stimuli 1 – Presenting
  #   Stimuli 2 – Presenting
  tasks <- c(
    "global_understanding",
    "co2_understanding",
    "global_presenting",
    "co2_presenting"
  )

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

  # Precompute group sizes for clean separation between assigned groups
  n_badges    <- sum(df_sorted$group == "badges")
  n_footnotes <- sum(df_sorted$group == "footnotes")
  gap_between_groups <- 1.5
  # Shift both groups further to the right to make more room for long row labels
  start_badges       <- 6
  start_footnotes    <- start_badges + n_badges + gap_between_groups

  # 2. Main grid (individual choices) ----------------------------------------
  main_grid <- df_sorted %>%
    select(participantId, group, participant_rank, ends_with("choice")) %>%
    pivot_longer(
      cols      = ends_with("choice"),
      names_to  = "task_raw",
      values_to = "choice"
    ) %>%
    mutate(
      task_name = str_remove(task_raw, "_choice"),
      # Add a small visual gap between "Understanding" and "Presenting" rows
      # by shifting the "Presenting" rows slightly downward.
      gap_understanding_presenting_y = 0.25,
      # y rows follow the explicit `tasks` vector (top → bottom)
      # Note: ggplot's y-axis increases upwards, so we invert the index so the
      # first entry in `tasks` appears at the top row.
      y = length(tasks) - match(task_name, tasks) + 1,
      y = y - dplyr::if_else(
        task_name %in% c("global_presenting", "co2_presenting"),
        gap_understanding_presenting_y,
        0
      ),
      choice = tolower(trimws(choice)),
      choice = dplyr::case_when(
        choice == "badges"        ~ "badges",
        choice == "footnotes"     ~ "footnotes",
        TRUE                      ~ "no_preference"
      ),
      choice = factor(choice, levels = c("badges", "no_preference", "footnotes"))
    ) %>%
    group_by(group, y) %>%
    arrange(choice, .by_group = TRUE) %>%
    mutate(
      x = dplyr::if_else(
        group == "badges",
        start_badges + row_number() - 1,
        start_footnotes + row_number() - 1
      )
    ) %>%
    ungroup()

  # 3. Summary grid (totals on the right) ------------------------------------
  # Start summary squares a bit to the right of the main grid
  max_main_x <- max(main_grid$x, na.rm = TRUE)
  start_summary_x <- max_main_x + 3

  # Tile sizing:
  # - Main grid: keep a small gap between participants for readability.
  # - Summary (aggregate) grid: reduce *horizontal* whitespace only (keep the
  #   same vertical spacing as the main grid).
  tile_size_main           <- 0.92
  tile_size_summary_width  <- 0.97
  tile_size_summary_height <- tile_size_main
  summary_step_x           <- 1.0

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
      x = start_summary_x + (row_number() - 1) * summary_step_x
    ) %>%
    ungroup() %>%
    mutate(type = "summary")

  plot_data <- bind_rows(
    main_grid %>% mutate(type = "main"),
    summary_grid
  )

  y_min <- min(plot_data$y, na.rm = TRUE)

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

  # Position of separator between individual grids and aggregate grid
  sep_x <- max_main_x + 1.5

  # 5. Build plot (compact, clean, \"scientific\") -----------------------------
  y_max <- length(tasks)
  max_blocks_per_row <- summary_grid %>%
    count(y, name = "blocks") %>%
    summarise(max(blocks), .groups = "drop") %>%
    pull()

  end_summary_x <- start_summary_x + (max_blocks_per_row - 1) * summary_step_x

  # Place task labels close to the waffles, but keep enough room so they never clip.
  # Since hjust = 1, the text extends to the LEFT of `label_x`.
  label_x <- start_badges - 1.4
  x_min   <- label_x - 9
  x_max   <- end_summary_x + 1.2

  p <- ggplot(plot_data, aes(x = x, y = y)) +
    # Squares (draw main and aggregate grids separately so the aggregate tiles
    # can be denser / less gappy for a clean visual distinction).
    geom_tile(
      data = dplyr::filter(plot_data, type == "main"),
      aes(fill = choice),
      width = tile_size_main,
      height = tile_size_main
    ) +
    geom_tile(
      data = dplyr::filter(plot_data, type == "summary"),
      aes(fill = choice),
      width = tile_size_summary_width,
      height = tile_size_summary_height
    ) +
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
        x     = label_x,
        label = dplyr::case_when(
          task_name == "global_understanding" ~ "Stimuli 1 - Understanding",
          task_name == "global_presenting"    ~ "Stimuli 1 - Presenting",
          task_name == "co2_understanding"    ~ "Stimuli 2 - Understanding",
          task_name == "co2_presenting"       ~ "Stimuli 2 - Presenting",
          TRUE                                ~ str_to_title(str_replace(task_name, "_", "\n"))
        )
      ),
      hjust    = 1,
      vjust    = 0.5,
      fontface = "plain",
      size     = 3.0,
      color    = "#333333"
    ) +

    # Group labels (top, above individual grids)
    { if (!is.na(badges_x)) annotate("text", x = badges_x, y = y_max + 1.35,
                                     label = "Group badges", fontface = "plain",
                                     size = 3.0, color = "#555555") } +
    { if (!is.na(footnotes_x)) annotate("text", x = footnotes_x, y = y_max + 1.35,
                                        label = "Group footnotes", fontface = "plain",
                                        size = 3.0, color = "#555555") } +

    # Header and separator for aggregate grid on the right
    annotate("text",
             x = (start_summary_x + end_summary_x) / 2,
             y = y_max + 1.35,
             label = "Total count",
             hjust = 0.5,
             size  = 3.0,
             colour = "#333333") +
    annotate("segment",
             x = sep_x, xend = sep_x,
             y = 0.4,  yend = y_max + 2.15,
             linetype = "dashed", colour = "grey75") +

    coord_fixed(clip = "off") +
    theme_void() +
    theme(
      legend.position = "bottom",
      legend.title    = element_blank(),
      legend.text     = element_text(size = 8),
      # Square legend keys (avoid rectangular swatches)
      legend.key.width  = unit(0.55, "lines"),
      legend.key.height = unit(0.55, "lines"),
      plot.margin     = margin(8, 6, 4, 10)
    ) +
    # Lower limit must be <= 1 - (tile_height / 2) to avoid clipping bottom row.
    scale_y_continuous(
      limits = c(y_min - (tile_size_main / 2) - 0.02, y_max + 2.25),
      breaks = 1:y_max
    ) +
    scale_x_continuous(limits = c(x_min, x_max)) +
    labs(title = NULL)

  message("Writing s1b preferences grid to: ", output_path)
  # Use an aspect ratio close to y_range/x_range to avoid excessive white space.
  grDevices::png(output_path, width = 1700, height = 520, res = 200)
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
