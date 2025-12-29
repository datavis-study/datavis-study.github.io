#!/usr/bin/env Rscript

# Simple, clean Likert barplot using the 'likert' package
# -------------------------------------------------------
# - Expects a wide CSV with one row per participant and one column per Likert item.
# - For this project, it defaults to `questionnaire_likert_scores.csv` created by the
#   Python data prep scripts, with:
#     * group          (e.g. "badge", "footnote")
#     * participantId
#     * saliency, clutter, interpretability, usefulness, trust, standardization
# - Produces a horizontal stacked bar chart for each item, optionally grouped by `group`.

suppressPackageStartupMessages({
  library(tidyverse)
  library(likert)
  library(ggpattern)
})

draw_key_half_stripe_overlay <- function(data, params, size) {
  # Legend key: left half = plain fill, right half = same fill with a light stripe overlay.
  # This makes the legend "correct" when the plot uses a pattern overlay for one condition.
  if (!requireNamespace("grid", quietly = TRUE)) {
    return(ggplot2::draw_key_rect(data, params, size))
  }

  alpha <- data$alpha %||% 1

  base <- grid::rectGrob(
    gp = grid::gpar(
      col  = NA,
      fill = scales::alpha(data$fill %||% "grey80", alpha)
    )
  )

  stripe_vp <- grid::viewport(
    x = 0.75, y = 0.5,
    width = 0.5, height = 1,
    just = c("center", "center"),
    clip = "on"
  )

  spacing <- 0.14
  offs <- seq(-1, 1 + spacing, by = spacing)
  stripes <- grid::segmentsGrob(
    x0 = offs, y0 = 0,
    x1 = offs + 1, y1 = 1,
    gp = grid::gpar(
      # Slightly stronger than the in-plot stripes so the split remains readable at legend-key size,
      # and still visible on the darker end of the greyscale ramp.
      col = scales::alpha("white", 0.6),
      lwd = 1.1,
      lineend = "butt"
    ),
    vp = stripe_vp
  )

  split_line <- grid::segmentsGrob(
    x0 = 0.5, y0 = 0,
    x1 = 0.5, y1 = 1,
    gp = grid::gpar(col = scales::alpha("grey80", 0.7), lwd = 0.8)
  )

  grid::grobTree(base, stripes, split_line)
}

generate_likert_plot_print_friendly <- function(likert_plot_data, palette_5) {
  # `likert::plot()` already provides signed percentages in `likert_plot_data$value`
  # (negative = disagree side, positive = agree side).
  # We replot it with ggpattern so the Badge group can be hatched cleanly.
  dfp <- likert_plot_data %>%
    dplyr::mutate(
      # Normalise group labels so the axis is consistent across datasets.
      Group = dplyr::case_when(
        tolower(as.character(Group)) %in% c("footnote", "footnotes") ~ "Footnotes",
        tolower(as.character(Group)) %in% c("badge", "badges") ~ "Badges",
        TRUE ~ as.character(Group)
      ),
      Group = factor(Group, levels = c("Footnotes", "Badges")),
      # Pattern is only used to differentiate groups (Badges vs Footnotes)
      pattern = dplyr::if_else(.data$Group == "Badges", "stripe", "none")
    ) %>%
    dplyr::filter(!is.na(Group))

  # Split into positive / negative halves so we can control stacking order per side.
  # Goal: Strongest responses should be furthest from 0 (Strongly Agree rightmost, Strongly Disagree leftmost).
  df_pos <- dfp %>%
    dplyr::filter(.data$value >= 0) %>%
    dplyr::mutate(
      variable = factor(
        .data$variable,
        levels = c(
          "Neither Agree nor Disagree",
          "Agree",
          "Strongly Agree",
          "Disagree",
          "Strongly Disagree"
        )
      )
    )

  df_neg <- dfp %>%
    dplyr::filter(.data$value < 0) %>%
    dplyr::mutate(
      variable = factor(
        .data$variable,
        levels = c(
          "Neither Agree nor Disagree",
          "Disagree",
          "Strongly Disagree",
          "Agree",
          "Strongly Agree"
        )
      )
    )

  base <- ggplot2::ggplot() +
    ggplot2::facet_wrap(~Item, ncol = 1, strip.position = "top") +
    ggplot2::coord_flip() +
    ggplot2::scale_y_continuous(labels = function(x) paste0(abs(x), "%")) +
    ggplot2::scale_fill_manual(
      # Use *named* values so the darkest colour always maps to Strongly Agree.
      values = palette_5,
      name = NULL,
      breaks = names(palette_5),
      labels = names(palette_5)
    ) +
    ggpattern::scale_pattern_manual(values = c(none = "none", stripe = "stripe"), guide = "none") +
    ggplot2::guides(fill = ggplot2::guide_legend()) +
    ggplot2::labs(x = NULL, y = NULL) +
    ggplot2::theme_minimal(base_size = 10) +
    ggplot2::theme(
      legend.position = "bottom",
      axis.text.y = ggplot2::element_text(size = 10),
      strip.text = ggplot2::element_text(size = 10, face = "bold"),
      strip.background = ggplot2::element_rect(fill = "grey95", color = NA)
    )

  # Pattern settings for the "Badge" group.
  # We want a clear group distinction without washing out the underlying fill colours.
  pattern_params <- list(
    # ggplot stacks fills in reverse factor order by default in this coord/geom setup.
    # We want responses to increase in strength *away* from 0:
    # - positive side: Neutral (closest) → Agree → Strongly Agree (furthest)
    # - negative side: Neutral (closest) → Disagree → Strongly Disagree (furthest)
    # so we explicitly reverse the stacking direction.
    position = ggplot2::position_stack(reverse = TRUE),
    # Remove segment outlines (they can look like a dashed border in patterned bars).
    color = NA,
    linewidth = 0,
    # Make the pattern "line-only" (no opaque pattern fill) so bar colours remain visible.
    pattern_fill = NA,
    # Light, semi-transparent lines (instead of filled stripes) to avoid muting fills.
    pattern_colour = "white",
    pattern_alpha = 0.35,
    # Fewer stripes and more spacing makes the fill read first, pattern second.
    pattern_density = 0.12,
    pattern_spacing = 0.12,
    pattern_angle = 45,
    pattern_key_scale_factor = 0.8,
    key_glyph = draw_key_half_stripe_overlay
  )

  base +
    # Legend-only layer so the fill legend keys are deterministic:
    # each key shows 50% plain fill + 50% stripe overlay.
    ggplot2::layer(
      data = tibble::tibble(
        Item = dfp$Item[[1]],
        Group = factor("Footnotes", levels = c("Footnotes", "Badges")),
        value = 0,
        variable = factor(names(palette_5), levels = names(palette_5))
      ),
      mapping = ggplot2::aes(x = Group, y = value, fill = variable),
      stat = "identity",
      geom = ggplot2::GeomCol,
      position = "stack",
      show.legend = TRUE,
      inherit.aes = FALSE,
      key_glyph = draw_key_half_stripe_overlay,
      params = list(linewidth = 0, colour = NA, na.rm = TRUE)
    ) +
    do.call(
      ggpattern::geom_col_pattern,
      c(
        list(
          data = df_neg,
          mapping = ggplot2::aes(x = Group, y = value, fill = variable, pattern = pattern),
          show.legend = c(fill = FALSE, pattern = FALSE)
        ),
        pattern_params
      )
    ) +
    do.call(
      ggpattern::geom_col_pattern,
      c(
        list(
          data = df_pos,
          mapping = ggplot2::aes(x = Group, y = value, fill = variable, pattern = pattern),
          show.legend = c(fill = FALSE, pattern = FALSE)
        ),
        pattern_params
      )
    )
}

#' Generate a Likert-type horizontal stacked barplot for questionnaire items.
#'
#' @param data_dir    Directory where the CSV lives (relative or absolute).
#' @param out_dir     Output directory for charts (created if missing).
#' @param input_file  CSV file name inside `data_dir`.
#' @param output_file PNG file name inside `out_dir`.
generate_likert_barplot <- function(
  data_dir    = "data",
  out_dir     = "r_output",
  input_file  = "questionnaire_likert_scores.csv",
  output_file = "likert_barplot_by_group.png"
) {
  # Resolve paths
  input_path  <- file.path(data_dir, input_file)
  output_path <- file.path(out_dir, output_file)

  if (!file.exists(input_path)) {
    stop("Likert input file not found: ", input_path)
  }

  if (!dir.exists(out_dir)) {
    dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  }

  message("Reading Likert data from: ", input_path)

  df <- readr::read_csv(input_path, show_col_types = FALSE)

  # By default we treat all non-id columns as Likert items.
  id_cols <- intersect(c("group", "participantId"), names(df))
  item_cols <- setdiff(names(df), id_cols)

  # Human-readable question text for each item (used as axis labels / headers)
  item_label_map <- c(
    saliency        = "Easy to spot.",
    clutter         = "Cluttered or distracted from the visualization.",
    interpretability = "Clear and easy to interpret.",
    usefulness      = "Information was useful for understanding the visualization.",
    trust           = "Increased my trust in the information and methodology.",
    standardization = "Should be widely used alongside visualizations."
  )

  if (length(item_cols) == 0) {
    stop(
      "No Likert item columns found in ", input_path,
      ". Expected at least one column beyond: ", paste(id_cols, collapse = ", ")
    )
  }

  # Standardise all item columns to the same ordered factor levels (required by likert::likert)
  # We map numeric codes 1–5 to the actual response labels used in the report:
  # 1 = Strongly Disagree, 5 = Strongly Agree
  likert_codes  <- as.character(1:5)
  likert_labels <- c(
    "Strongly Disagree",
    "Disagree",
    "Neither Agree nor Disagree",
    "Agree",
    "Strongly Agree"
  )

  items_df <- df %>%
    dplyr::select(dplyr::all_of(item_cols))

  # Coerce via base R to avoid any tibble/list-column surprises,
  # and apply shared ordered factor levels with human-readable labels.
  items_df <- as.data.frame(
    lapply(
      items_df,
      function(col) {
        codes <- as.integer(as.character(col))
        factor(
          codes,
          levels  = 1:5,
          labels  = likert_labels,
          ordered = TRUE
        )
      }
    ),
    stringsAsFactors = FALSE
  )

  # Apply the long-form question text as column names where we have a mapping
  original_names <- colnames(items_df)
  colnames(items_df) <- ifelse(
    original_names %in% names(item_label_map),
    item_label_map[original_names],
    original_names
  )

  # Optional grouping (e.g. "badge" vs "footnote")
  grouping <- if ("group" %in% names(df)) df$group else NULL

  likert_obj <- if (!is.null(grouping)) {
    likert::likert(items = items_df, grouping = grouping)
  } else {
    likert::likert(items = items_df)
  }

  # Print-friendly greyscale palette for a 5-point Likert scale.
  # Darkest (Strongly Agree) is a near-black so it prints well without crushing.
  palette_5 <- c(
    "#d9d9d9", # 1: Strongly Disagree
    "#bdbdbd", # 2: Disagree
    "#969696", # 3: Neither...
    "#636363", # 4: Agree
    "#252525"  # 5: Strongly Agree
  )

  message("Writing Likert barplot to: ", output_path)

  grDevices::png(output_path, width = 1500, height = 1200, res = 200)
  on.exit(grDevices::dev.off(), add = TRUE)

  p_base <- plot(
    likert_obj,
    type          = "bar",   # stacked bar representation
    centered      = 3,       # center on the neutral point (for 1–5 scale)
    wrap          = 200,     # Prevent wrapping of long labels
    plot.percent.low = FALSE,
    plot.percent.neutral = FALSE,
    plot.percent.high = FALSE,
    colors        = palette_5 # Pass colors directly to plot.likert
  )

  # Build the print-friendly ggpattern version from the base plot data.
  palette_named <- setNames(palette_5, likert_labels)
  p <- generate_likert_plot_print_friendly(p_base$data, palette_named)

  # Ensure plot is drawn into the device
  print(p)

  invisible(output_path)
}


