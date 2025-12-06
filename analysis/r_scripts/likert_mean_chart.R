#!/usr/bin/env Rscript

# Single-chart script: Likert mean scores by group and dimension

# Helper to join paths
likert_path_join <- function(...) {
  file.path(..., fsep = .Platform$file.sep)
}

generate_likert_mean_chart <- function(data_dir, out_dir) {
  likert_path <- likert_path_join(data_dir, "questionnaire_likert_scores.csv")

  if (!file.exists(likert_path)) {
    message("Likert scores CSV not found; skipping Likert chart: ", likert_path)
    return(invisible(NULL))
  }

  message("Reading Likert scores from: ", likert_path)

  likert <- readr::read_csv(likert_path, show_col_types = FALSE)

  # Expect columns: group, saliency, clutter, interpretability,
  # usefulness, trust, standardization
  dimension_cols <- c(
    "saliency", "clutter", "interpretability",
    "usefulness", "trust", "standardization"
  )

  missing_dims <- setdiff(dimension_cols, names(likert))
  if (length(missing_dims) > 0) {
    warning(
      "Skipping Likert chart because these dimensions are missing: ",
      paste(missing_dims, collapse = ", ")
    )
    return(invisible(NULL))
  }

  if (!"group" %in% names(likert)) {
    warning("Skipping Likert chart because `group` column is missing.")
    return(invisible(NULL))
  }

  likert_long <- likert |>
    tidyr::pivot_longer(
      cols = dplyr::all_of(dimension_cols),
      names_to = "dimension",
      values_to = "score"
    )

  likert_summary <- likert_long |>
    dplyr::group_by(group, dimension) |>
    dplyr::summarise(
      mean_score = mean(score, na.rm = TRUE),
      .groups = "drop"
    )

  p_likert <- ggplot(likert_summary, aes(
    x = dimension,
    y = mean_score,
    fill = group
  )) +
    geom_col(position = position_dodge(width = 0.8)) +
    coord_cartesian(ylim = c(1, 5)) +
    labs(
      title = "Likert mean scores by group and dimension",
      x = "Dimension",
      y = "Mean score (1–5)",
      fill = "Group"
    ) +
    theme_minimal(base_size = 12) +
    theme(
      axis.text.x = element_text(angle = 45, hjust = 1)
    )

  if (!dir.exists(out_dir)) {
    dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  }

  out_file <- likert_path_join(out_dir, "likert_mean_scores_by_group.png")
  ggsave(out_file, p_likert, width = 8, height = 5, dpi = 300)
  message("Saved Likert chart to: ", out_file)

  invisible(out_file)
}


