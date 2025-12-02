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


if __name__ == "__main__":
  import argparse

  parser = argparse.ArgumentParser(
    description="Generate a deceptive truncated‑axis bar chart stimulus.",
  )
  parser.add_argument(
    "--out",
    type=str,
    default="public/mind-the-badge-experiment-2/assets/truncated-axis/source.png",
    help="Output PNG path (default: public/.../truncated-axis/source.png)",
  )
  parser.add_argument(
    "--a",
    type=float,
    default=96.0,
    help="Value for Company A (default: 96.0)",
  )
  parser.add_argument(
    "--b",
    type=float,
    default=100.0,
    help="Value for Company B (default: 100.0)",
  )
  parser.add_argument(
    "--ymin",
    type=float,
    default=90.0,
    help="Y‑axis minimum (default: 90.0)",
  )
  parser.add_argument(
    "--ymax",
    type=float,
    default=105.0,
    help="Y‑axis maximum (default: 105.0)",
  )

  args = parser.parse_args()
  out_path = make_truncated_axis_chart(
    output_path=args.out,
    company_a=args.a,
    company_b=args.b,
    ymin=args.ymin,
    ymax=args.ymax,
  )
  print(f"Saved truncated‑axis stimulus to: {out_path}")


