---
title: Mind the Badge – Study Report
---

## Executive summary

Write your summary here. This section supports Markdown and simple templating.  
Example: We analyzed {{ participants_count }} participants across groups:

{% for gc in group_counts %}
- {{ gc.group }}: {{ gc.n_participants }}
{% endfor %}

## Compact overview

| Item | Value |
|---|---|
| Participants | {{ participants_count }} |
| Groups | {% for gc in group_counts %}{{ gc.group }}: {{ gc.n_participants }}{% if not loop.last %}; {% endif %}{% endfor %} |
| Languages (top) | {% for l in languages_top %}{{ l[0] }} ({{ l[1] }}){% if not loop.last %}; {% endif %}{% endfor %} |
| Countries (top) | {% for c in countries_top %}{{ c[0] }} ({{ c[1] }}){% if not loop.last %}; {% endif %}{% endfor %} |
| Resolutions (top) | {% for r in resolutions_top %}{{ r[0] }} ({{ r[1] }}){% if not loop.last %}; {% endif %}{% endfor %} |
| Files present | participants: {{ 'yes' if files_present.participants else 'no' }}, time: {{ 'yes' if files_present.time_per_component else 'no' }}, likert: {{ 'yes' if files_present.likert_scores else 'no' }}, open: {{ 'yes' if files_present.open_responses else 'no' }}, badges: {{ 'yes' if files_present.badge_metrics else 'no' }}, notes: {{ 'yes' if files_present.notes else 'no' }} |
| Time components | {% for t in time_components %}{{ t }}{% if not loop.last %}; {% endif %}{% endfor %} |
| Time outliers (>30m) | {% for k, v in time_outliers.items() %}{{ k }}: {{ v }}{% if not loop.last %}; {% endif %}{% endfor %} |
| Questionnaire | Likert participants: {{ n_likert }}, Open responses: {{ n_open }} |
| Notes | Entries: {{ n_notes }}{% if median_note_words is not none %}, Median words: {{ median_note_words }}{% endif %} |
| Badges | Rows: {{ n_badge_rows }}, Unique labels: {{ n_badge_labels }}, Stimuli: {{ n_stimuli_with_badges }} |
| Data dir | `{{ data_dir }}` |
| Generated | `{{ generated_at }}` |

## Notes

- Data directory: `{{ data_dir }}`
- Generated at: `{{ generated_at }}`
- Run id: `{{ run_id }}`

## Highlights

- Replace this list with key findings and context.
- You can add images, code blocks, and tables.

### Basic example figure

This is a clean example figure generated automatically (total session time, trimmed at the 95th percentile), overlaid by group:

{% set fig = (figures | selectattr('name','equalto','f_total_time_hist') | list | first) %}
{% if fig %}
![Total session time (trimmed)]({{ fig.path }})
{% else %}
> Total time figure is not available (missing `participant_time_per_component.csv`).
{% endif %}

```text
Example fenced code block (appears styled in the report).
```

| Dimension | Comment                      |
|----------:|------------------------------|
|   Sample1 | This is an example table     |
|   Sample2 | You can edit this freely     |


