# Mind the Badge - Study Data Report
Generated at: `{{ generated_at }}`

**Demographics**

{% if demographics_summary and demographics_summary|length > 0 %}
| Category | Top values |
|---|---|
{% for item in demographics_summary -%}
| {{ item.label }} | {% for v in item.top_values %}{{ v.value }} ({{ v.count }}){% if not loop.last %}, {% endif %}{% endfor %} |
{% endfor %}
{% else %}
> No demographics available.
{% endif %}

{% if demographics_rows and demographics_rows|length > 0 %}
<details>
<summary><strong>Show full demographics table</strong></summary>

| Participant | Gender | Age | Education | Field | Reads charts | Creates charts | Color vision |
|---|---|---|---|---|---|---|---|
{% for r in demographics_rows -%}
| {{ r.readableId or '' }} | {{ r['gender'] or '' }} | {{ r['age'] or '' }} | {{ r['education'] or '' }} | {{ r['field-of-study'] or '' }} | {{ r['chart-reading-frequency'] or '' }} | {{ r['chart-creation-frequency'] or '' }} | {{ r['color-vision'] or '' }} |
{% endfor %}

</details>
{% endif %}

# Main Tasks
Task description: Imagine you're presenting this visualization to your boss. Write down the text you would use for your speech.

## Stimuli 1: CO₂ Emissions

| Footnotes condition | Badges condition |
| :-----------------: | :--------------: |
| <img src="figures/stimuli_co2_emissions_footnotes.jpg" alt="CO₂ emissions stimulus with footnotes" width="420" /> | <img src="figures/stimuli_co2_emissions_badges.jpg" alt="CO₂ emissions stimulus with badges" width="420" /> |
{% if notes_items and notes_items|length > 0 %}
{% set co2_notes = (notes_items | selectattr('stimulus','equalto','CO₂ Emissions') | list | first) %}
{% if co2_notes %}
{% set co2_foot = co2_notes.responses | selectattr('group','equalto','Footnotes') | list %}
{% set co2_badge = co2_notes.responses | selectattr('group','equalto','Badges') | list %}

{% if co2_foot and co2_foot|length > 0 %}
<details>
<summary><strong>Stimulus notes – CO₂ Emissions (Footnotes)</strong> — {{ co2_foot|length }} notes</summary>

{% for r in co2_foot %}
- <em>{{ r.group }}</em> ({{ r.participant }}, {{ r.words }} words): {{ r.text }}
{% endfor %}

</details>
{% endif %}

{% if co2_badge and co2_badge|length > 0 %}
<details>
<summary><strong>Stimulus notes – CO₂ Emissions (Badges)</strong> — {{ co2_badge|length }} notes</summary>

{% for r in co2_badge %}
- <em>{{ r.group }}</em> ({{ r.participant }}, {{ r.words }} words): {{ r.text }}
{% endfor %}

</details>
{% endif %}
{% endif %}
{% endif %}

## Stimuli 2: Global Warming Projection

| Footnotes condition | Badges condition |
| :-----------------: | :--------------: |
| <img src="figures/stimuli_global_warming_footnotes.jpg" alt="Global warming projection stimulus with footnotes" width="420" /> | <img src="figures/stimuli_global_warming_badges.jpg" alt="Global warming projection stimulus with badges" width="420" /> |

{% if notes_items and notes_items|length > 0 %}
{% set gw_notes = (notes_items | selectattr('stimulus','equalto','Global Warming Projection') | list | first) %}
{% if gw_notes %}
{% set gw_foot = gw_notes.responses | selectattr('group','equalto','Footnotes') | list %}
{% set gw_badge = gw_notes.responses | selectattr('group','equalto','Badges') | list %}

{% if gw_foot and gw_foot|length > 0 %}
<details>
<summary><strong>Stimulus notes – Global Warming Projection (Footnotes)</strong> — {{ gw_foot|length }} notes</summary>

{% for r in gw_foot %}
- <em>{{ r.group }}</em> ({{ r.participant }}, {{ r.words }} words): {{ r.text }}
{% endfor %}

</details>
{% endif %}

{% if gw_badge and gw_badge|length > 0 %}
<details>
<summary><strong>Stimulus notes – Global Warming Projection (Badges)</strong> — {{ gw_badge|length }} notes</summary>

{% for r in gw_badge %}
- <em>{{ r.group }}</em> ({{ r.participant }}, {{ r.words }} words): {{ r.text }}
{% endfor %}

</details>
{% endif %}
{% endif %}
{% endif %}

### Badge interactions – hover metrics

{% if badge_hover_chart or badge_hover_time_chart or badge_hover_duration_chart %}
| {% if badge_hover_chart %}Hover counts{% endif %} | {% if badge_hover_time_chart %}Total hover time{% endif %} | {% if badge_hover_duration_chart %}Duration stats{% endif %} |
| :-----------------------------------------------: | :--------------------------------------------------------: | :-----------------------------------------------------------: |
| {% if badge_hover_chart %}<img src="{{ badge_hover_chart.path }}" alt="Hover counts per stimulus" width="320" />{% endif %} | {% if badge_hover_time_chart %}<img src="{{ badge_hover_time_chart.path }}" alt="Hover times per stimulus" width="320" />{% endif %} | {% if badge_hover_duration_chart %}<img src="{{ badge_hover_duration_chart.path }}" alt="Hover duration statistics per stimulus" width="320" />{% endif %} |
{% else %}
> No badge interaction metrics available (missing `stimulus_badge_metrics.csv` or hover counts).
{% endif %}

### Badge interactions – clicks and drawer metrics 
_Note: No data, because nobody clicked on any badge_
| Click counts | Total open time | Mean open duration |
| :----------: | :-------------: | :----------------: |
| {% if badge_click_chart %}<img src="{{ badge_click_chart.path }}" alt="Click counts per stimulus" width="320" />{% endif %} | {% if badge_drawer_time_chart %}<img src="{{ badge_drawer_time_chart.path }}" alt="Total drawer open time per stimulus" width="320" />{% endif %} | {% if badge_drawer_duration_chart %}<img src="{{ badge_drawer_duration_chart.path }}" alt="Mean drawer open time per stimulus" width="320" />{% endif %} |

### Likert questions

- **Saliency** Footnotes/Badges were easy to spot.
- **Clutter** Footnotes/Badges cluttered or distracted from the visualization.
- **Interpretability** Footnotes/Badges were clear and easy to interpret.
- **Usefulness** Information in the Footnotes/Badges was useful for understanding the visualization.
- **Trust** Footnotes/Badges increased my trust in the information and methodology.
- **Standardization** Footnotes/Badges like these should be widely used alongside visualizations.

### Likert – distributions and medians

{% set ldist = (figures | selectattr('name','equalto','f_likert_distribution_median') | list | first) %}
{% if ldist %}
<img src="{{ ldist.path }}" alt="Likert distributions and medians" width="640" />
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
<img src="{{ lbar.path }}" alt="Likert mean bars" width="640" />
<sub>Small multiples in a single row: one facet per dimension with two bars (Footnotes = grey, Badges = blue). Values shown above bars.</sub>
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

### Time spent per component

{% if time_detail_rows and time_detail_rows|length > 0 %}
<details>
<summary><strong>Show participant time per component (Footnotes vs Badges)</strong></summary>

| Participant | Group | Global warming figure (s) | CO₂ emissions figure (s) | Total session (s) |
|---|---|---|---|---|
{% for r in time_detail_rows %}
| {{ r.display_id }} | {{ r.group_friendly }} | {{ r["global-warming-projection (s)"] }} | {{ r["co2-emissions (s)"] }} | {{ r["total (s)"] }} |
{% endfor %}

</details>
{% else %}
> No participant time-per-component data available.
{% endif %}

