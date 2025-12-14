#!/usr/bin/env Rscript

# Quick reminder summaries for s1b follow-up study
# ------------------------------------------------
# This script reads `analysis/data/s1b/quick_reminder.csv` and visualises how
# many participants in each original group (badges vs footnotes) remembered:
#   - taking part in the original study, and
#   - the stimuli themselves.

suppressPackageStartupMessages({
  library(tidyverse)
})

#' Generate grouped bars for s1b quick reminder questions by original group.
#'
#' @param data_dir   Directory where the s1b CSV lives (default: "data/s1b").
#' @param out_dir    Output directory for charts (created if missing).
#' @param input_file CSV file name inside `data_dir` (default: "quick_reminder.csv").
generate_s1b_quick_reminder_barcharts <- function(
  data_dir   = file.path("data", "s1b"),
  out_dir    = file.path("s1b", "r_output"),
  input_file = "quick_reminder.csv"
) {
  input_path <- file.path(data_dir, input_file)

  if (!file.exists(input_path)) {
    stop("s1b quick_reminder input file not found: ", input_path)
  }

  if (!dir.exists(out_dir)) {
    dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  }

  message("Reading s1b quick reminder data from: ", input_path)
  df <- readr::read_csv(input_path, show_col_types = FALSE)

  required_cols <- c("group", "rememberStudy", "rememberStimuli")
  missing_cols  <- setdiff(required_cols, names(df))
  if (length(missing_cols) > 0) {
    stop(
      "Missing expected quick_reminder columns: ",
      paste(missing_cols, collapse = ", ")
    )
  }

  df_long <- df %>%
    tidyr::pivot_longer(
      cols      = tidyselect::all_of(c("rememberStudy", "rememberStimuli")),
      names_to  = "question",
      values_to = "response"
    ) %>%
    dplyr::filter(!is.na(response), trimws(response) != "")

  if (nrow(df_long) == 0) {
    stop("No non-empty s1b quick_reminder responses found in: ", input_path)
  }

  question_labels <- c(
    rememberStudy   = "Remembered taking part in the study",
    rememberStimuli = "Remembered the stimuli"
  )

  df_long <- df_long %>%
    dplyr::mutate(
      group_label    = dplyr::recode(group,
                                     badges    = "Original group: Badges",
                                     footnotes = "Original group: Footnotes",
                                     .default  = group),
      question_label = dplyr::recode(question, !!!question_labels, .default = question),
      response_clean = stringr::str_to_title(trimws(response))
    )

  summary_df <- df_long %>%
    dplyr::group_by(question_label, group_label, response_clean) %>%
    dplyr::summarise(
      n = dplyr::n(),
      .groups = "drop_last"
    ) %>%
    dplyr::mutate(
      total_n = sum(n),
      prop    = n / total_n
    ) %>%
    dplyr::ungroup()

  output_path <- file.path(out_dir, "s1b_quick_reminder_by_group.png")
  message("Writing s1b quick reminder plot to: ", output_path)

  palette_resp <- c(
    "Yes" = "#4575b4",
    "No"  = "#d73027"
  )

  p <- ggplot(
    summary_df,
    aes(
      x    = group_label,
      y    = prop * 100,
      fill = response_clean
    )
  ) +
    geom_col(width = 0.7, position = position_dodge(width = 0.7), color = NA) +
    geom_text(
      aes(label = paste0(round(prop * 100), "%")),
      position = position_dodge(width = 0.7),
      vjust    = -0.3,
      size     = 3
    ) +
    facet_wrap(~ question_label) +
    scale_fill_manual(
      values = palette_resp,
      name   = "Response"
    ) +
    scale_y_continuous(
      labels = function(x) paste0(x, "%"),
      expand = expansion(mult = c(0, 0.15))
    ) +
    labs(
      x = NULL,
      y = "Share of participants",
      title = NULL
    ) +
    theme_minimal(base_size = 11) +
    theme(
      legend.position  = "bottom",
      legend.key.size  = unit(0.4, "lines"),
      axis.text.x      = element_text(angle = 15, hjust = 1),
      panel.grid.major = element_line(colour = "grey93"),
      panel.grid.minor = element_blank()
    )

  grDevices::png(output_path, width = 1400, height = 900, res = 200)
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
  generate_s1b_quick_reminder_barcharts(data_dir = data_dir, out_dir = out_dir)
}
