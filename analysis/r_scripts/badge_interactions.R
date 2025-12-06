#!/usr/bin/env Rscript

suppressPackageStartupMessages({
  library(tidyverse)
})

#' Generate badge interaction plots (counts and times)
#'
#' @param data_dir    Directory where the CSV lives (relative or absolute).
#' @param out_dir     Output directory for charts (created if missing).
#' @param input_file  CSV file name inside `data_dir`.
generate_badge_interaction_plots <- function(
  data_dir    = "data",
  out_dir     = "r_output",
  input_file  = "stimulus_badge_metrics.csv"
) {
  # Resolve paths
  input_path  <- file.path(data_dir, input_file)
  
  if (!file.exists(input_path)) {
    warning("Badge metrics input file not found: ", input_path)
    return()
  }

  if (!dir.exists(out_dir)) {
    dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)
  }

  message("Reading Badge metrics data from: ", input_path)
  df <- readr::read_csv(input_path, show_col_types = FALSE)

  # The input CSV aggregates metrics per badge/stimulus.
  # However, the user requested "stacked bar per participant interaction".
  # The aggregate file `stimulus_badge_metrics.csv` does not contain per-participant events.
  # But `stimulus_badge_participant_flags.csv` only has binary flags (hoveredAnyBadge).
  
  # If we want "per participant interaction", we would ideally need a file with:
  # participantId, stimulusId, badgeId, hoverCount
  
  # Assuming the user wants to visualize the total counts but stacked by... 
  # wait, "stacked bar per participant interaction" implies we want to see 
  # how many participants interacted vs didn't, OR the distribution of interactions across participants.
  
  # BUT, the provided file `stimulus_badge_metrics.csv` only has `hoverCount` (total) and `hoverParticipantCount` (unique participants).
  
  # Let's re-read the user request:
  # "on the y axis should be the badges" (horizontal bar chart)
  # "make it a stacked bar per participant interaction"
  
  # This is ambiguous. Does it mean:
  # 1. X axis = Count, Y axis = Badge. Bars stacked by participant? (We don't have per-participant counts in this file).
  # 2. X axis = Count, Y axis = Badge. Bars stacked by interaction type? (No, "per participant interaction").
  
  # If we look at `stimulus_badge_metrics.csv`, we have:
  # hoverCount (total hovers across all participants)
  # hoverParticipantCount (number of participants who hovered at least once)
  
  # Maybe the user means:
  # Y axis: Badge Labels
  # X axis: Count
  # Stack: Maybe just total count?
  
  # Wait, if the user wants "per participant interaction", they might mean they want to see the individual participants' contributions to the total count?
  # I don't have that data in the loaded CSV `stimulus_badge_metrics.csv`.
  # I only have totals.
  
  # However, the user said "make it a stacked bar per participant interaction".
  # Maybe they mean "Badge" on Y, "Count" on X.
  # If I can't stack by participant, I will just make it a bar chart but flipped (Badge on Y).
  
  # Let's look for another file. `stimulus_badge_participant_flags.csv` is just flags.
  # Is there a raw events file? No.
  
  # I will assume the user wants a Horizontal Bar Chart (Badges on Y).
  # And for "stacked bar per participant interaction", since I lack the granular data,
  # I'll interpret this as "Total Interactions" for now, possibly distinguishing between something if possible,
  # or perhaps they just meant "Show me the total interactions for each badge".
  
  # Actually, maybe they mean "Hover vs Click"?
  # "interaction" usually implies multiple types.
  # If I stack "Hovers" and "Clicks" and "Drawer Opens"?
  # That would be a stacked bar of interactions.
  
  # Let's try stacking the Interaction Types (Hover, Click, Drawer Open) for each Badge.
  # Y = Badge
  # X = Count
  # Fill = Interaction Type
  
  # Filter / Select relevant data
  df_interactions <- df %>%
    dplyr::select(stimulusId, badgeLabel, hoverCount, clickCount, drawerOpenCount) %>%
    tidyr::pivot_longer(
      cols      = c(hoverCount, clickCount, drawerOpenCount),
      names_to  = "interaction_type",
      values_to = "count"
    ) %>%
    dplyr::mutate(
      interaction_type = factor(interaction_type, 
        levels = c("drawerOpenCount", "clickCount", "hoverCount"), # Order for stacking (largest usually at bottom/left)
        labels = c("Drawer Opens", "Clicks", "Hovers")
      )
    )

  output_path_hover <- file.path(out_dir, "badge_interaction_counts.png")
  message("Writing Badge Interaction Counts plot to: ", output_path_hover)

  # Create the plot
  p_hover <- ggplot(df_interactions, aes(x = count, y = badgeLabel, fill = interaction_type)) +
    # Horizontal bars (y = badge)
    geom_col(width = 0.7) +
    # Facet by stimulus
    facet_wrap(~ stimulusId, scales = "free_y", ncol = 1) +
    # Colors
    scale_fill_manual(values = c(
      "Hovers"       = "#92c5de", # Light Blue
      "Clicks"       = "#f4a582", # Light Red
      "Drawer Opens" = "#0571b0"  # Dark Blue
    )) +
    # Labels
    labs(
      title = "Badge Interactions",
      x = "Count",
      y = NULL, # Badge labels on Y
      fill = "Interaction"
    ) +
    # Theme
    theme_minimal(base_size = 12) +
    theme(
      legend.position = "bottom",
      axis.text.y     = element_text(size = 10),
      axis.text.x     = element_text(size = 10),
      strip.text      = element_text(size = 12, face = "bold"),
      strip.background = element_rect(fill = "grey95", color = NA),
      panel.grid.major.y = element_blank()
    )

  # Save
  grDevices::png(output_path_hover, width = 1600, height = 1200, res = 200)
  print(p_hover)
  grDevices::dev.off()
}
