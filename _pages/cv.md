---
layout: page
title: cv
permalink: /cv/
description: Curriculum vitae of Callum Witten.
nav: true
nav_order: 2
cv_file: https://www.callumwitten.com/_files/ugd/46b2c2_9e100c70c37344e6ac1e3fddc5827c72.pdf
_styles: >
  .cv-download { display: inline-block; margin: 0.5rem 0 1.5rem; padding: 0.55rem 1.1rem; border: 1px solid var(--global-theme-color); border-radius: 0.5rem; font-weight: 500; }
  .cv-download:hover { background: var(--global-theme-color); color: var(--global-hover-text-color) !important; text-decoration: none; }
  .cv-frame { width: 100%; height: 80vh; min-height: 500px; border: 1px solid var(--global-divider-color); border-radius: 0.5rem; }
---

<p><a class="cv-download" href="{% if page.cv_file contains '://' %}{{ page.cv_file }}{% else %}{{ page.cv_file | relative_url }}{% endif %}">Download my CV (PDF)</a></p>

{% assign first_char = page.cv_file | slice: 0 %}
{% if first_char == '/' %}
  <iframe class="cv-frame" src="{{ page.cv_file | relative_url }}" title="Callum Witten CV"></iframe>
{% endif %}
