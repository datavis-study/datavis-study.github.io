Generated at: `{{ generated_at }}`

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

{% set lbar = (figures | selectattr('name','equalto','f_likert_mean_bars') | list | first) %}
{% if lbar %}
![Likert mean bars]({{ lbar.path }})
<sub>Grouped vertical bars: Footnotes (grey) and Badges (blue) per dimension. Values shown above bars.</sub>
{% else %}
> Mean bars figure is not available.
{% endif %}

