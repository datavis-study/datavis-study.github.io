import pathlib
from typing import Union

import matplotlib.pyplot as plt
import seaborn as sns


def make_truncated_axis_chart(
  output_path: Union[str, pathlib.Path],
  company_a: float = 96.0,
  company_b: float = 100.0,
  ymin: float = 90.0,
  ymax: float = 105.0,
) -> pathlib.Path:
  """
  Generate a deceptive truncated‑axis bar chart stimulus.

  Default numbers follow your example:
  - Company A = 96
  - Company B = 100
  - Y‑axis from 90 to 105 (visually exaggerates the 4% difference)
  """
  output_path = pathlib.Path(output_path)
  output_path.parent.mkdir(parents=True, exist_ok=True)

  sns.set_theme(style="whitegrid")

  fig, ax = plt.subplots(figsize=(4, 4), dpi=200)

  values = [company_a, company_b]
  labels = ["Company A", "Company B"]
  palette = sns.color_palette("muted", n_colors=2)

  ax.bar(labels, values, color=palette)
  ax.set_ylim(ymin, ymax)
  ax.set_ylabel("Annual revenue (million USD)")
  ax.set_title("Yearly revenue by company")

  # Hide top/right spines for a cleaner look
  sns.despine(ax=ax)

  fig.tight_layout()
  fig.savefig(output_path, bbox_inches="tight")
  plt.close(fig)

  return output_path


def generate_all_stimuli() -> None:
  """
  Generate all image stimuli for Mind‑the‑Badge Experiment 2.

  Currently:
    - Truncated‑axis bar chart (control)
    - Copies of the same chart for badge and footnote groups as placeholders
  """
  root = pathlib.Path(__file__).resolve().parent

  # Base directories for this task
  base = root / "assets" / "truncated-axis"
  control_path = base / "source.png"
  badges_path = base / "grp-badges" / "source.png"
  footnotes_path = base / "grp-footnotes" / "source.png"

  print("Generating truncated‑axis stimuli...")
  make_truncated_axis_chart(control_path)
  # For now, use the same chart as a starting point for all three variants.
  make_truncated_axis_chart(badges_path)
  make_truncated_axis_chart(footnotes_path)

  print("  control :", control_path)
  print("  badges  :", badges_path)
  print("  footnotes:", footnotes_path)
  print("Done.")


if __name__ == "__main__":
  generate_all_stimuli()


