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

generate_likert_plot_print_friendly <- function(likert_plot_data, palette_5, counts_df) {
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
      Group = factor(Group, levels = c("Footnotes", "Badges"))
    ) %>%
    dplyr::filter(!is.na(Group))

  # Join absolute counts (n) computed from the raw questionnaire data.
  # Note: `likert::plot()` splits the Neutral category into two halves (positive + negative).
  # We keep both halves for geometry, but label Neutral only once (at y = 0) with the full count.
  counts_norm <- counts_df %>%
    dplyr::mutate(
      Group = dplyr::case_when(
        tolower(as.character(.data$Group)) %in% c("footnote", "footnotes") ~ "Footnotes",
        tolower(as.character(.data$Group)) %in% c("badge", "badges") ~ "Badges",
        TRUE ~ as.character(.data$Group)
      ),
      Group = factor(.data$Group, levels = c("Footnotes", "Badges")),
      Item = as.character(.data$Item),
      variable = as.character(.data$variable),
      n = as.integer(.data$n)
    )

  dfp <- dfp %>%
    dplyr::left_join(
      counts_norm %>% dplyr::select(.data$Group, .data$Item, .data$variable, .data$n),
      by = c("Group", "Item", "variable")
    )

  # Pattern encoding (group distinction without introducing color).
  # Match the waffle chart’s spirit: "Badges" = hatched/striped, "Footnotes" = solid.
  dfp <- dfp %>%
    dplyr::mutate(
      group_pattern = dplyr::if_else(.data$Group == "Badges", "stripe", "none")
    )

  # Enforce a consistent item/facet order (top-to-bottom).
  # Important: run this AFTER joins, since joins will coerce factor↔character to a common type.
  dfp <- dfp %>%
    dplyr::mutate(
      Item_chr = as.character(.data$Item),
      Item_order = dplyr::case_when(
        stringr::str_detect(stringr::str_to_lower(Item_chr), "easy to spot") ~ 1L,
        stringr::str_detect(stringr::str_to_lower(Item_chr), "clutter") ~ 2L,
        stringr::str_detect(stringr::str_to_lower(Item_chr), "interpret") ~ 3L,
        stringr::str_detect(stringr::str_to_lower(Item_chr), "useful") ~ 4L,
        stringr::str_detect(stringr::str_to_lower(Item_chr), "trust") ~ 5L,
        stringr::str_detect(stringr::str_to_lower(Item_chr), "widely used") ~ 6L,
        TRUE ~ 999L
      ),
      Item = forcats::fct_reorder(factor(Item_chr), .data$Item_order, .fun = min)
    ) %>%
    dplyr::select(-Item_chr, -Item_order)

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

  # Add per-segment labels using absolute counts (n).
  # We compute explicit midpoints (instead of relying on position_stack) to avoid misplacement
  # when the Neutral category is split across the zero line.
  add_segment_labels <- function(d) {
    d <- d %>%
      dplyr::mutate(
        # Keep labels readable on darker fills.
        label_color = dplyr::if_else(
          as.character(.data$variable) %in% c("Agree", "Strongly Agree"),
          "white",
          "black"
        ),
        label = dplyr::if_else(
          is.na(.data$n) | .data$n <= 0 | is.na(.data$value) | abs(.data$value) < 1e-9,
          "",
          as.character(.data$n)
        )
      ) %>%
      dplyr::group_by(.data$Item, .data$Group) %>%
      dplyr::arrange(.data$variable, .by_group = TRUE) %>%
      dplyr::mutate(
        y_start = dplyr::lag(cumsum(.data$value), default = 0),
        y_end = .data$y_start + .data$value,
        y_mid = (.data$y_start + .data$y_end) / 2
      ) %>%
      dplyr::ungroup()

    # Neutral is drawn as two halves; label it once with the full count at y = 0.
    d <- d %>%
      dplyr::mutate(
        is_neutral = as.character(.data$variable) == "Neither Agree nor Disagree",
        label = dplyr::if_else(.data$is_neutral & .data$value < 0, "", .data$label),
        y_mid = dplyr::if_else(.data$is_neutral & .data$value > 0 & .data$label != "", 0, .data$y_mid)
      )

    d
  }

  df_pos <- add_segment_labels(df_pos)
  df_neg <- add_segment_labels(df_neg)

  base_font_size <- 10
  # `geom_text(size=...)` uses mm, while theme text sizes are in pt.
  # Convert pt → mm so in-bar counts match legend/axis typography.
  label_size_mm <- base_font_size / ggplot2::.pt * 0.8

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
    ggplot2::scale_color_identity() +
    ggplot2::guides(
      fill = ggplot2::guide_legend(
        keywidth = grid::unit(0.25, "lines"),
        keyheight = grid::unit(0.25, "lines")
      )
    ) +
    ggplot2::labs(x = NULL, y = NULL) +
    ggplot2::theme_minimal(base_size = base_font_size) +
    ggplot2::theme(
      legend.position = "bottom",
      # Much smaller legend squares + right-aligned legend.
      legend.key.size = grid::unit(0.20, "lines"),
      legend.spacing.x = grid::unit(0.20, "lines"),
      legend.box.just = "right",
      legend.justification = "right",
      legend.text.align = 1,
      axis.text.y = ggplot2::element_text(size = 11),
      strip.text = ggplot2::element_text(size = 11),
      # Remove label backgrounds completely (facet strips + legend background/keys).
      strip.background = ggplot2::element_blank(),
      legend.background = ggplot2::element_blank(),
      legend.key = ggplot2::element_blank()
    )

  # Stacking settings.
  # We explicitly reverse stacking so response strength increases away from 0.
  stack_params <- list(
    position = ggplot2::position_stack(reverse = TRUE),
    colour = NA,
    linewidth = 0
  )

  # Stripe texture settings (kept subtle so fills remain readable).
  # White-ish stripes read clearly on darker response segments while staying low-noise on light ones.
  pattern_params <- list(
    pattern_fill = "#FFFFFF",
    pattern_colour = "#FFFFFF",
    pattern_angle = 45,
    pattern_alpha = 0.35,
    pattern_spacing = 0.06,
    pattern_density = 0.40,
    # Render at higher internal resolution to reduce jaggies in PNG export.
    pattern_res = 1600
  )

  base +
    do.call(
      ggpattern::geom_col_pattern,
      c(
        list(
          data = df_neg,
          mapping = ggplot2::aes(x = Group, y = value, fill = variable, pattern = group_pattern),
          show.legend = TRUE
        ),
        stack_params,
        pattern_params
      )
    ) +
    do.call(
      ggpattern::geom_col_pattern,
      c(
        list(
          data = df_pos,
          mapping = ggplot2::aes(x = Group, y = value, fill = variable, pattern = group_pattern),
          show.legend = TRUE
        ),
        stack_params,
        pattern_params
      )
    ) +
    ggpattern::scale_pattern_manual(values = c(none = "none", stripe = "stripe"), guide = "none") +
    # Per-segment absolute-count labels.
    ggplot2::geom_text(
      data = df_neg,
      mapping = ggplot2::aes(x = Group, y = y_mid, label = label, color = label_color),
      position = "identity",
      size = label_size_mm,
      lineheight = 0.95,
      show.legend = FALSE
    ) +
    ggplot2::geom_text(
      data = df_pos,
      mapping = ggplot2::aes(x = Group, y = y_mid, label = label, color = label_color),
      position = "identity",
      size = label_size_mm,
      lineheight = 0.95,
      show.legend = FALSE
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
    saliency        = "..were easy to spot",
    # This item is reverse-coded (see below) so that higher = better across all items.
    clutter         = "..did not clutter or distract from the visualizations",
    interpretability = "..were clear and easy to interpret",
    usefulness      = "..were useful for understanding the visualization",
    trust           = "..increased my trust in the information and methodology",
    standardization = "..should be widely used alongside visualizations."
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

  items_raw <- df %>%
    dplyr::select(dplyr::all_of(item_cols))

  # Coerce via base R to avoid any tibble/list-column surprises,
  # and apply shared ordered factor levels with human-readable labels.
  # Reverse-code negatively phrased items so that higher values consistently mean "better".
  items_df <- as.data.frame(
    purrr::imap(
      items_raw,
      function(col, nm) {
        codes <- as.integer(as.character(col))
        if (identical(nm, "clutter")) {
          # Reverse: 1↔5, 2↔4, 3 stays 3
          codes <- dplyr::if_else(is.na(codes), NA_integer_, 6L - codes)
        }
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

  # Prefer ragg for smoother pattern rendering; fall back to base png device.
  if (requireNamespace("ragg", quietly = TRUE)) {
    ragg::agg_png(output_path, width = 1500, height = 1200, res = 200)
  } else {
    grDevices::png(output_path, width = 1500, height = 1200, res = 200)
  }

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

  # Absolute counts (n) per Group × Item × response.
  # Use the already-renamed item columns so `Item` matches the plot facets.
  counts_long <- tibble::as_tibble(items_df) %>%
    dplyr::mutate(Group = grouping) %>%
    tidyr::pivot_longer(
      cols = -Group,
      names_to = "Item",
      values_to = "variable"
    ) %>%
    dplyr::filter(!is.na(.data$variable)) %>%
    dplyr::count(.data$Group, .data$Item, .data$variable, name = "n")

  p <- generate_likert_plot_print_friendly(p_base$data, palette_named, counts_long)

  # Ensure plot is drawn into the device
  print(p)
  grDevices::dev.off()

  # Also write a PDF next to the PNG for crisp zooming in the paper.
  pdf_path <- sub("\\.png$", ".pdf", output_path)
  grDevices::pdf(pdf_path, width = 1500 / 200, height = 1200 / 200, useDingbats = FALSE)
  print(p)
  grDevices::dev.off()

  invisible(list(png = output_path, pdf = pdf_path))
}


