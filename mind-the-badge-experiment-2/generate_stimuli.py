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
            width=300,
            height=220,
            title="Yearly revenue by company",
        )
    )

    # Use a higher scale factor so the PNG looks crisp even if displayed larger.
    chart.save(str(output_path), scale_factor=3.0)

    return output_path


def make_area_bubble_chart(
    output_path: str | pathlib.Path,
    value_x: float = 10.0,
    value_y: float = 20.0,
    radius_x: float = 1.0,
    radius_y: float = 2.0,
) -> pathlib.Path:
    """
    Generate an \"area as quantity\" deceptive bubble chart.

    The data values differ by a factor of 2 (X=10, Y=20), but the circle
    radii differ by a factor of 2 (1 vs 2), so the visible areas differ
    by a factor of 4 (A ∝ r²), visually exaggerating the difference.
    """
    output_path = pathlib.Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    source = pd.DataFrame(
        {
            "label": ["Value X", "Value Y"],
            "value": [float(value_x), float(value_y)],
            # Use radius values directly; Altair encodes circle size as area,
            # so we square the radii to get 1² : 2² → 1 : 4 area ratio.
            "size": [radius_x**2, radius_y**2],
            "x": [0, 1],
        }
    )

    chart = (
        alt.Chart(source)
        .mark_circle(color="#4b72b8", opacity=0.9)
        .encode(
            x=alt.X("x:O", title=None, axis=None),
            y=alt.Y("value:Q", title=None, axis=None),
            size=alt.Size(
                "size:Q",
                legend=None,
                scale=alt.Scale(range=[400, 1600]),
            ),
            tooltip=["label:N", "value:Q"],
        )
        .properties(
            width=320,
            height=200,
            title="Visual comparison of Value X and Value Y",
        )
    )

    chart.save(str(output_path), scale_factor=3.0)

    return output_path


def make_inverted_axis_chart(
    output_path: str | pathlib.Path,
    start_crime: float = 100.0,
    end_crime: float = 50.0,
) -> pathlib.Path:
    """
    Generate an inverted‑axis line chart for crime rates.

    Numeric values drop from `start_crime` to `end_crime`, but the plotted
    line moves up because we encode an inverted crime value and fake the
    axis labels so that 0 appears at the top and the maximum at the bottom.
    """
    output_path = pathlib.Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Simple four‑point series to show a trend
    crime_values = [start_crime, 80.0, 65.0, end_crime]
    max_crime = max(crime_values)

    source = pd.DataFrame(
        {
            "time": [1, 2, 3, 4],
            "crime": crime_values,
        }
    )
    # Plot inverted crime so the line moves up as crime decreases
    source["crime_inverted"] = max_crime - source["crime"]

    tick_values = list(range(0, int(max_crime) + 1, 10))

    chart = (
        alt.Chart(source)
        .mark_line(point=True, color="#c2410c")
        .encode(
            x=alt.X("time:Q", title="Year", axis=alt.Axis(values=[1, 2, 3, 4])),
            y=alt.Y(
                "crime_inverted:Q",
                scale=alt.Scale(domain=(0, max_crime), nice=False, zero=True),
                axis=alt.Axis(
                    title="Crime rate (index)",
                    values=tick_values,
                    # Display labels as descending: 100 (bottom) → 0 (top)
                    labelExpr=f"{int(max_crime)} - datum.value",
                ),
            ),
        )
        .properties(
            width=320,
            height=220,
            title="Reported crime rate over time",
        )
    )

    chart.save(str(output_path), scale_factor=3.0)

    return output_path


def generate_all_stimuli() -> None:
    """
    Generate all image stimuli for Mind‑the‑Badge Experiment 2.

    Currently:
      - Truncated‑axis bar chart
      - Area‑as‑quantity bubble chart (circles)
      - Inverted‑axis line chart (crime rate)
    """
    root = pathlib.Path(__file__).resolve().parent

    # Truncated axis
    trunc_base = root / "assets" / "truncated-axis"
    trunc_source = trunc_base / "source.png"

    print("Generating truncated‑axis stimulus...")
    make_truncated_axis_chart(trunc_source)
    print("  source :", trunc_source)

    # Area as quantity (bubble/disc chart)
    bubbles_base = root / "assets" / "area-bubbles"
    bubbles_source = bubbles_base / "source.png"

    print("Generating area‑as‑quantity (bubble) stimulus...")
    make_area_bubble_chart(bubbles_source)
    print("  source :", bubbles_source)

    # Inverted axis (crime over time)
    inverted_base = root / "assets" / "inverted-axis"
    inverted_source = inverted_base / "source.png"

    print("Generating inverted‑axis (crime) stimulus...")
    make_inverted_axis_chart(inverted_source)
    print("  source :", inverted_source)

    print("Done.")


if __name__ == "__main__":
  generate_all_stimuli()


