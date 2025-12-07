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
<summary><span style="font-size: 1.1em;"><strong>Show full demographics table</strong></span></summary>

| Participant | Gender | Age | Education | Field | Reads charts | Creates charts | Color vision |
|---|---|---|---|---|---|---|---|
{% for r in demographics_rows -%}
| {{ r.readableId or '' }} | {{ r['gender'] or '' }} | {{ r['age'] or '' }} | {{ r['education'] or '' }} | {{ r['field-of-study'] or '' }} | {{ r['chart-reading-frequency'] or '' }} | {{ r['chart-creation-frequency'] or '' }} | {{ r['color-vision'] or '' }} |
{% endfor %}

</details>
{% endif %}

## Main tasks
Task description: Imagine you're presenting this visualization to your boss. Write down the text you would use for your speech.

### Stimuli 1: CO₂ Emissions

{% if notes_items and notes_items|length > 0 %}
{% set co2_notes = (notes_items | selectattr('stimulus','equalto','CO₂ Emissions') | list | first) %}
{% if co2_notes %}
{% set co2_foot = co2_notes.responses | selectattr('group','equalto','Footnotes') | list %}
{% set co2_badge = co2_notes.responses | selectattr('group','equalto','Badges') | list %}

{% if co2_foot and co2_foot|length > 0 %}
<details>
<summary><span style="font-size: 1.1em;"><strong>Participants Responses: CO₂ Emissions 🟦 Footnotes</strong> — {{ co2_foot|length }} notes</strong></span></summary>

{% for r in co2_foot %}
🟦 **{{ r.participant }} ({{ r.words }} words{% if r.isProlific %}; Prolific{% endif %}{% if r.stimOrderLabel %}; {{ r.stimOrderLabel }}{% endif %}{% if r.hoveredAnyBadge or r.clickedAnyBadge %};{% if r.hoveredAnyBadge %} hovered badges{% endif %}{% if r.hoveredAnyBadge and r.clickedAnyBadge %}, {% endif %}{% if r.clickedAnyBadge %} clicked badges{% endif %}{% endif %})**: {{ r.text }}
{% endfor %}

</details>
{% endif %}

{% if co2_badge and co2_badge|length > 0 %}
<details>
<summary><span style="font-size: 1.1em;"><strong>Participants Responses: CO₂ Emissions 🟩 Badges</strong> — {{ co2_badge|length }} notes</span></summary>

{% for r in co2_badge %}
🟩 **{{ r.participant }} ({{ r.words }} words{% if r.isProlific %}; Prolific{% endif %}{% if r.stimOrderLabel %}; {{ r.stimOrderLabel }}{% endif %}{% if r.hoveredAnyBadge or r.clickedAnyBadge %};{% if r.hoveredAnyBadge %} hovered badges{% endif %}{% if r.hoveredAnyBadge and r.clickedAnyBadge %}, {% endif %}{% if r.clickedAnyBadge %} clicked badges{% endif %}{% endif %})**: {{ r.text }}
{% endfor %}

</details>
{% endif %}
{% endif %}
{% endif %}

### Stimuli 2: Global Warming Projection

{% if notes_items and notes_items|length > 0 %}
{% set gw_notes = (notes_items | selectattr('stimulus','equalto','Global Warming Projection') | list | first) %}
{% if gw_notes %}
{% set gw_foot = gw_notes.responses | selectattr('group','equalto','Footnotes') | list %}
{% set gw_badge = gw_notes.responses | selectattr('group','equalto','Badges') | list %}

{% if gw_foot and gw_foot|length > 0 %}
<details>
<summary><span style="font-size: 1.1em;"><strong>Participants Responses: Global Warming Projection 🟦 Footnotes</strong> — {{ gw_foot|length }} notes</span></summary>

{% for r in gw_foot %}
🟦 **{{ r.participant }} ({{ r.words }} words{% if r.isProlific %}; Prolific{% endif %}{% if r.stimOrderLabel %}; {{ r.stimOrderLabel }}{% endif %}{% if r.hoveredAnyBadge or r.clickedAnyBadge %};{% if r.hoveredAnyBadge %} hovered badges{% endif %}{% if r.hoveredAnyBadge and r.clickedAnyBadge %}, {% endif %}{% if r.clickedAnyBadge %} clicked badges{% endif %}{% endif %})**: {{ r.text }}
{% endfor %}

</details>
{% endif %}

{% if gw_badge and gw_badge|length > 0 %}
<details>
<summary><span style="font-size: 1.1em;"><strong>Participants Responses: Global Warming Projection 🟩 Badges</strong> — {{ gw_badge|length }} notes</span></summary>

{% for r in gw_badge %}
🟩 **{{ r.participant }} ({{ r.words }} words{% if r.isProlific %}; Prolific{% endif %}{% if r.stimOrderLabel %}; {{ r.stimOrderLabel }}{% endif %}{% if r.hoveredAnyBadge or r.clickedAnyBadge %};{% if r.hoveredAnyBadge %} hovered badges{% endif %}{% if r.hoveredAnyBadge and r.clickedAnyBadge %}, {% endif %}{% if r.clickedAnyBadge %} clicked badges{% endif %}{% endif %})**: {{ r.text }}
{% endfor %}

</details>
{% endif %}
{% endif %}
{% endif %}

# Post-questionaire

**Likert scale questions per dimension**
- **Saliency** Footnotes/Badges were easy to spot. (1 = Strongly Disagree, 5 = Strongly Agree)
- **Clutter** Footnotes/Badges cluttered or distracted from the visualization. (1 = Strongly Disagree, 5 = Strongly Agree)
- **Interpretability** Footnotes/Badges were clear and easy to interpret. (1 = Strongly Disagree, 5 = Strongly Agree)
- **Usefulness** Information in the Footnotes/Badges was useful for understanding the visualization. (1 = Strongly Disagree, 5 = Strongly Agree)
- **Trust** Footnotes/Badges increased my trust in the information and methodology. (1 = Strongly Disagree, 5 = Strongly Agree)
- **Standardization** Footnotes/Badges like these should be widely used alongside visualizations. (1 = Strongly Disagree, 5 = Strongly Agree)


*(Chart-based visual summaries are omitted in this version of the report.)*

### Open-ended answers

{% if open_questions and open_questions|length > 0 %}
{# First, show the noticing summary table (not collapsed) #}
{% for q in open_questions if q.key == "noticed-in-task" %}
**{{ q.label }}** — {{ q.count }} responses

| Group | Yes | No | Sometimes | Not sure |
|---|---|---|---|---|
{%- set ns = q.noticed_summary %}
{%- if ns is iterable %}
{%- for row in ns %}
| {{ row.group }} | {{ row.options[0].count }} | {{ row.options[1].count }} | {{ row.options[2].count }} | {{ row.options[3].count }} |
{%- endfor %}
{%- else %}
| Footnotes | 0 | 0 | 0 | 0 |
| Badges | 0 | 0 | 0 | 0 |
{%- endif %}

{% endfor %}

{# Then, show all other open-ended questions in collapsible sections #}
{% for q in open_questions if q.key != "noticed-in-task" %}
<details>
<summary><span style="font-size: 1.1em;"><strong>{{ q.label }}</strong> — {{ q.count }} responses</span></summary>

{% if q.prompt_footnotes %}
**🟦 Footnotes question:** {{ q.prompt_footnotes }}

{% endif %}

{% if q.responses_footnotes and q.responses_footnotes|length > 0 %}
{% for r in q.responses_footnotes %}
- **{{ r.participant }} ({{ r.words }} words{% if r.isProlific %}; Prolific{% endif %}{% if r.firstStimulusLabel %}; {{ r.firstStimulusLabel }}{% endif %}{% if r.hoveredAnyBadge or r.clickedAnyBadge %};{% if r.hoveredAnyBadge %} hovered badges{% endif %}{% if r.hoveredAnyBadge and r.clickedAnyBadge %}, {% endif %}{% if r.clickedAnyBadge %} clicked badges{% endif %}{% endif %})**: {{ r.text }}
{% endfor %}
{% endif %}

{% if q.prompt_badges %}
**🟩 Badges question:** {{ q.prompt_badges }}

{% endif %}

{% if q.responses_badges and q.responses_badges|length > 0 %}
{% for r in q.responses_badges %}
- **{{ r.participant }} ({{ r.words }} words{% if r.isProlific %}; Prolific{% endif %}{% if r.firstStimulusLabel %}; {{ r.firstStimulusLabel }}{% endif %}{% if r.hoveredAnyBadge or r.clickedAnyBadge %};{% if r.hoveredAnyBadge %} hovered badges{% endif %}{% if r.hoveredAnyBadge and r.clickedAnyBadge %}, {% endif %}{% if r.clickedAnyBadge %} clicked badges{% endif %}{% endif %})**: {{ r.text }}
{% endfor %}
{% endif %}

{% if q.responses_other and q.responses_other|length > 0 %}
**[Other / Unknown group]**  
{% for r in q.responses_other %}
• **{{ r.participant }} ({{ r.group }}, {{ r.words }} words{% if r.isProlific %}; Prolific{% endif %}{% if r.firstStimulusLabel %}; {{ r.firstStimulusLabel }}{% endif %}{% if r.hoveredAnyBadge or r.clickedAnyBadge %};{% if r.hoveredAnyBadge %} hovered badges{% endif %}{% if r.hoveredAnyBadge and r.clickedAnyBadge %}, {% endif %}{% if r.clickedAnyBadge %} clicked badges{% endif %}{% endif %})**: {{ r.text }}
{% endfor %}
{% endif %}

</details>
{% endfor %}
{% else %}
> No open-ended responses available.
{% endif %}

### Badge interactions (text-only summary)

{% if badge_participant_stats and badge_participant_stats|length > 0 %}
**Per-stimulus participant coverage (hover and clicks):**

{% for s in badge_participant_stats %}
- **{{ s.label }}**: {{ s.hover_participants }} participants hovered at least one badge; {{ s.click_participants }} participants clicked at least one badge.
{% endfor %}

{% set total_click_participants = badge_participant_stats | map(attribute="click_participants") | sum %}
{% if total_click_participants == 0 %}
_Note: No click interaction data available (no participants clicked badges)._
{% endif %}
{% else %}
_No badge interaction metrics available (missing `stimulus_badge_metrics.csv` or badge metrics were not computed)._
{% endif %}

### Participant ID mapping and time per component

{% if participant_id_map and participant_id_map|length > 0 %}
<details>
<summary><span style="font-size: 1.1em;"><strong>Show participant ID mapping and time per component (minutes)</strong></span></summary>

_Times per component are shown in minutes (rounded to 1 decimal)._

| Readable ID | Participant GUID | Group | Prolific?{% if time_columns_map and time_columns_map|length > 0 %}{% for col in time_columns_map %} | {{ col.label }}{% endfor %}{% endif %} |
|---|---|---|---{% if time_columns_map and time_columns_map|length > 0 %}{% for col in time_columns_map %}|---{% endfor %}{% endif %}|
{% for m in participant_id_map -%}
| {{ m.readableId }} | `{{ m.participantId }}` | {{ m.group }} | {% if m.isProlific %}Yes{% else %}No{% endif %}{% if time_columns_map and time_columns_map|length > 0 %}{% for col in time_columns_map %} | {{ m.get(col.key, "") }}{% endfor %}{% endif %} |
{% endfor %}

</details>
{% else %}
> No participant mapping available.
{% endif %}

