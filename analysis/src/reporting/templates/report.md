Generated at: `{{ generated_at }}`

### Demographics

{% if demographics_rows and demographics_rows|length > 0 %}
| Participant | Gender | Age | Education | Field | Reads charts | Creates charts | Color vision |
|---|---|---|---|---|---|---|---|
{% for r in demographics_rows -%}
| {{ r.readableId or '' }} | {{ r['gender'] or '' }} | {{ r['age'] or '' }} | {{ r['education'] or '' }} | {{ r['field-of-study'] or '' }} | {{ r['chart-reading-frequency'] or '' }} | {{ r['chart-creation-frequency'] or '' }} | {{ r['color-vision'] or '' }} |
{% endfor %}
{% else %}
> No demographics available.
{% endif %}

### Badge interactions – hover metrics

{% if badge_hover_chart or badge_hover_time_chart or badge_hover_duration_chart %}
| {% if badge_hover_chart %}Hover counts{% endif %} | {% if badge_hover_time_chart %}Total hover time{% endif %} | {% if badge_hover_duration_chart %}Duration stats{% endif %} |
| :-----------------------------------------------: | :--------------------------------------------------------: | :-----------------------------------------------------------: |
| {% if badge_hover_chart %}![Hover counts per stimulus]({{ badge_hover_chart.path }}){% endif %} | {% if badge_hover_time_chart %}![Hover times per stimulus]({{ badge_hover_time_chart.path }}){% endif %} | {% if badge_hover_duration_chart %}![Hover duration statistics per stimulus]({{ badge_hover_duration_chart.path }}){% endif %} |
| {% if badge_hover_chart %}<sub>Total hover counts per stimulus (shared y-axis labelled “Hover Count”).</sub>{% endif %} | {% if badge_hover_time_chart %}<sub>Total hover time per badge (bars), facetted by stimulus.</sub>{% endif %} | {% if badge_hover_duration_chart %}<sub>Mean hover time per badge (bars), facetted by stimulus.</sub>{% endif %} |
{% else %}
> No badge interaction metrics available (missing `stimulus_badge_metrics.csv` or hover counts).
{% endif %}

### Badge interactions – clicks and drawer metrics

| Click counts | Drawer opens | Total open time | Mean open duration |
| :----------: | :----------: | :-------------: | :----------------: |
| {% if badge_click_chart %}![Click counts per stimulus]({{ badge_click_chart.path }}){% endif %} | {% if badge_drawer_open_chart %}![Drawer open counts per stimulus]({{ badge_drawer_open_chart.path }}){% endif %} | {% if badge_drawer_time_chart %}![Total drawer open time per stimulus]({{ badge_drawer_time_chart.path }}){% endif %} | {% if badge_drawer_duration_chart %}![Mean drawer open time per stimulus]({{ badge_drawer_duration_chart.path }}){% endif %} |
| <sub>{% if badge_click_chart %}Total click counts per badge, facetted by stimulus.{% endif %}</sub> | <sub>{% if badge_drawer_open_chart %}Number of times the drawer was opened per badge.{% endif %}</sub> | <sub>{% if badge_drawer_time_chart %}Total time drawers were open per badge (s).{% endif %}</sub> | <sub>{% if badge_drawer_duration_chart %}Average open time per open event (s) per badge.{% endif %}</sub> |

### Stimulus notes

{% if notes_summary and notes_items and notes_items|length > 0 %}
- Total entries: {{ notes_summary.total }}
- Median words: {{ notes_summary.median_words }}
- Mean words: {{ notes_summary.mean_words }}
- By group: {% for g, c in notes_summary.counts_by_group.items() %}{{ g }}: {{ c }}{% if not loop.last %}; {% endif %}{% endfor %}

{% for s in notes_items %}
<details>
<summary><strong>{{ s.stimulus }}</strong> — {{ s.count }} notes</summary>

{% for r in s.responses %}
- <em>{{ r.group }}</em> ({{ r.participant }}, {{ r.words }} words): {{ r.text }}
{% endfor %}

</details>
{% endfor %}
{% else %}
> No stimulus notes available.
{% endif %}

### Likert questions

- **Saliency** Footnotes/Badges were easy to spot.
- **Clutter** Footnotes/Badges cluttered or distracted from the visualization.
- **Interpretability** Footnotes/Badges were clear and easy to interpret.
- **Usefulness** Information in the Footnotes/Badges was useful for understanding the visualization.
- **Trust** Footnotes/Badges increased my trust in the information and methodology.
- **Standardization** Footnotes/Badges like these should be widely used alongside visualizations.

### Likert beehive (compact)

{% set lb = (figures | selectattr('name','equalto','f_likert_beehive') | list | first) %}
{% if lb %}
![Likert beehive]({{ lb.path }})
<sub>Scale: 1 = {{ likert_scale_left or 'Strongly disagree' }}, 5 = {{ likert_scale_right or 'Strongly agree' }}. Facets show Group: Footnotes and Group: Badges. Colors indicate dimensions.</sub>
{% else %}
> Likert beehive figure is not available (missing `questionnaire_likert_scores.csv`).
{% endif %}

### Likert – distributions and medians

{% set ldist = (figures | selectattr('name','equalto','f_likert_distribution_median') | list | first) %}
{% if ldist %}
![Likert distributions and medians]({{ ldist.path }})
<sub>Per-dimension Likert score distributions (circle size = number of ratings), faceted by group (Footnotes vs Badges). Scale: 1 = Strongly Disagree, 5 = Strongly Agree.</sub>
{% else %}
> Distributions/medians figure is not available.
{% endif %}

### Open-ended answers

{% if open_questions and open_questions|length > 0 %}
{% for q in open_questions %}
<details>
<summary><strong>{{ q.label }}</strong> — {{ q.count }} responses</summary>

{% for r in q.responses %}
- <em>{{ r.group }}</em> ({{ r.participant }}): {{ r.text }}
{% endfor %}

</details>
{% endfor %}
{% else %}
> No open-ended responses available.
{% endif %}

### Likert – mean bar chart

{# Prefer Altair version if available; otherwise fall back to matplotlib version #}
{% set lbar = (figures | selectattr('name','equalto','f_likert_mean_bars_altair') | list | first) %}
{% if not lbar %}
  {% set lbar = (figures | selectattr('name','equalto','f_likert_mean_bars') | list | first) %}
{% endif %}
{% if lbar %}
![Likert mean bars]({{ lbar.path }})
<sub>Grouped vertical bars: Footnotes (grey) and Badges (blue) per dimension. Values shown above bars.</sub>
{% else %}
> Mean bars figure is not available.
{% endif %}

### Participant ID mapping

{% if participant_id_map and participant_id_map|length > 0 %}
<details>
<summary><strong>Show participant ID mapping</strong></summary>

| Readable ID | Participant GUID | Group |
|---|---|---|
{% for m in participant_id_map -%}
| {{ m.readableId }} | `{{ m.participantId }}` | {{ m.group }} |
{% endfor %}

</details>
{% else %}
> No participant mapping available.
{% endif %}

