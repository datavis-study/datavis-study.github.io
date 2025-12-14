#!/usr/bin/env Rscript

# Preference summaries for s1b follow-up study
# --------------------------------------------
# This script reads `analysis/data/s1b/preferences.csv` and produces a compact
# overview of how often participants preferred badges vs footnotes (or had no
# clear preference) across four scenarios:
#   - Overall understanding
#   - Presenting to others (overall)
#   - CO2 emissions stimulus
#   - Global warming projection stimulus

suppressPackageStartupMessages({
  library(tidyverse)
})

#' Generate stacked percentage bars for s1b preference questions.
#'
#' @param data_dir   Directory where the s1b CSV lives (default: "data/s1b").
#' @param out_dir    Output directory for charts (created if missing).
#' @param input_file CSV file name inside `data_dir` (default: "preferences.csv").
generate_s1b_preferences_barcharts <- function(
  data_dir   = file.path("data", "s1b"),
  out_dir    = file.path("s1b", "r_output"),
  input_file = "preferences.csv"
) {
  input_path <- file.path(data_dir, input_file)

  if (!file.exists(input_path)) {
    stop("s1b preferences input file not found: ", input_path)
  }

  if (!dir.exists(out_dir)) {
    dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  }

  message("Reading s1b preference data from: ", input_path)
  df <- readr::read_csv(input_path, show_col_types = FALSE)

  choice_cols <- c(
    "global_understanding_choice",
    "global_presenting_choice",
    "co2_understanding_choice",
    "co2_presenting_choice"
  )

  missing_cols <- setdiff(choice_cols, names(df))
  if (length(missing_cols) > 0) {
    stop(
      "Missing expected preference choice columns: ",
      paste(missing_cols, collapse = ", ")
    )
  }

  # Long format: participant × question × choice
  df_long <- df %>%
    tidyr::pivot_longer(
      cols      = tidyselect::all_of(choice_cols),
      names_to  = "question",
      values_to = "choice"
    ) %>%
    dplyr::filter(!is.na(choice), trimws(choice) != "")

  if (nrow(df_long) == 0) {
    stop("No non-empty s1b preference responses found in: ", input_path)
  }

  # Friendly labels
  question_labels <- c(
    global_understanding_choice = "Overall: easier to understand",
    global_presenting_choice    = "Overall: better for presenting",
    co2_understanding_choice    = "CO2 chart: easier to understand",
    co2_presenting_choice       = "CO2 chart: better for presenting"
  )

  choice_labels <- c(
    badges        = "Badges",
    footnotes     = "Footnotes",
    no_preference = "No clear preference"
  )

  df_long <- df_long %>%
    dplyr::mutate(
      question_label = dplyr::recode(question, !!!question_labels, .default = question),
      choice_clean   = tolower(trimws(choice)),
      choice_label   = dplyr::recode(choice_clean, !!!choice_labels, .default = stringr::str_to_title(choice_clean))
    )

  # Aggregate to percentages per question
  summary_df <- df_long %>%
    dplyr::group_by(question_label, choice_label) %>%
    dplyr::summarise(
      n = dplyr::n(),
      .groups = "drop_last"
    ) %>%
    dplyr::mutate(
      total_n = sum(n),
      prop    = n / total_n
    ) %>%
    dplyr::ungroup()

  output_path <- file.path(out_dir, "s1b_preferences_overall.png")
  message("Writing s1b preferences overview plot to: ", output_path)

  palette_choices <- c(
    "Badges"            = "#4575b4",
    "Footnotes"         = "#d73027",
    "No clear preference" = "#aaaaaa"
  )

  p <- ggplot(
    summary_df,
    aes(
      x    = question_label,
      y    = prop * 100,
      fill = choice_label
    )
  ) +
    geom_col(width = 0.7, color = NA) +
    geom_text(
      aes(label = paste0(round(prop * 100), "%")),
      position = position_stack(vjust = 0.5),
      color    = "black",
      size     = 3
    ) +
    scale_fill_manual(values = palette_choices, name = "Preferred format") +
    scale_y_continuous(
      labels = function(x) paste0(x, "%"),
      expand = expansion(mult = c(0, 0.05))
    ) +
    labs(
      x = NULL,
      y = "Share of participants",
      title = NULL
    ) +
    theme_minimal(base_size = 11) +
    theme(
      axis.text.x      = element_text(angle = 20, hjust = 1),
      legend.position  = "bottom",
      legend.key.size  = unit(0.4, "lines"),
      panel.grid.major = element_line(colour = "grey93"),
      panel.grid.minor = element_blank()
    )

  grDevices::png(output_path, width = 1600, height = 800, res = 200)
  print(p)
  grDevices::dev.off()

  invisible(output_path)
}


# Allow running this script directly for quick checks (only when this file is
# the entry point, not when sourced from another script such as r_charts.R).
if (sys.nframe() == 1) {
  args <- commandArgs(trailingOnly = TRUE)
  data_dir <- if (length(args) >= 1) args[[1]] else file.path("data", "s1b")
  out_dir  <- if (length(args) >= 2) args[[2]] else file.path("s1b", "r_output")
  generate_s1b_preferences_barcharts(data_dir = data_dir, out_dir = out_dir)
}
