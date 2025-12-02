import pathlib

import altair as alt
import pandas as pd


def make_truncated_axis_chart(
    output_path: str | pathlib.Path,
    company_a: float = 96.0,
    company_b: float = 100.0,
    ymin: float = 95.0,
    ymax: float = 101.0,
) -> pathlib.Path:
    """
    Generate a deceptive truncated‑axis bar chart stimulus using Altair.

    Key idea:
    - Bars are drawn relative to the truncated range [ymin, ymax]
    - Axis labels are "faked" so the ticks show real values (95–101),
      but the bar heights are scaled on the small 0–(ymax-ymin) range.
    """
    output_path = pathlib.Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ymin_f = float(ymin)
    ymax_f = float(ymax)
    span = ymax_f - ymin_f

    source = pd.DataFrame(
        {
            "company": ["A", "B"],
            "revenue": [float(company_a), float(company_b)],
        }
    )
    # Height above the truncated baseline
    source["revenue_offset"] = source["revenue"] - ymin_f

    # Tick positions in the offset space (0, 1, 2, ..., span)
    tick_values = list(range(0, int(span) + 1))

    chart = (
        alt.Chart(source)
        .mark_bar()
        .encode(
            x="company:N",
            y=alt.Y(
                "revenue_offset:Q",
                scale=alt.Scale(domain=(0, span), nice=False, zero=True),
                axis=alt.Axis(
                    title="Annual revenue (million USD)",
                    values=tick_values,
                    labelExpr=f"{int(ymin_f)} + datum.value",
                ),
            ),
        )
        .properties(
            width=250,
            height=250,
            title="Yearly revenue by company",
        )
    )

    chart.save(str(output_path), format="png")

    return output_path


def generate_all_stimuli() -> None:
  """
  Generate all image stimuli for Mind‑the‑Badge Experiment 2.

  Currently only:
    - Truncated‑axis bar chart (single source.png used across all groups)
  """
  root = pathlib.Path(__file__).resolve().parent

  # Base directory for this task
  base = root / "assets" / "truncated-axis"
  source_path = base / "source.png"

  print("Generating truncated‑axis stimulus...")
  make_truncated_axis_chart(source_path)

  print("  source :", source_path)
  print("Done.")


if __name__ == "__main__":
  generate_all_stimuli()


