# callumwitten.com

Personal website of Callum Witten, built with the [al-folio](https://github.com/alshedivat/al-folio) template and hosted on GitHub Pages.

## Editing the site

Every change you commit to the `main` branch rebuilds and republishes the site automatically within a few minutes (watch progress in the **Actions** tab).

| To change                         | Edit                                                       |
| --------------------------------- | ---------------------------------------------------------- |
| Home page text and "In the news"  | `_pages/about.md`                                          |
| Research page text                | `_pages/research.html`                                     |
| Research page paper cards         | `_data/research.yml` (images in `assets/img/research/`)    |
| CV                                | upload a new `assets/pdf/cv.pdf` (or edit `_pages/cv.md`)  |
| Contact and profile icons         | `_data/socials.yml`                                        |
| Profile photo                     | replace `assets/img/prof_pic.jpg`                          |
| Site name, description, keywords  | `_config.yml`                                              |

## Publications and h-index

The publications page (paper lists and stats cards for papers, first-author papers, citations and h-index) comes from the SciX library `GMHWLZNeQGedFToaW4i9uw`. The **Update publications** workflow refreshes them every morning using the `ADS_TOKEN` repository secret, and republishes the site if anything changed. To refresh straight away: **Actions → Update publications → Run workflow**.

Don't edit `_includes/publications_generated.html` or `_data/publications.json` by hand: they are overwritten on every update. To change how the lists look, edit `bin/update_publications.py`; to change their styling, edit the `_styles` block at the top of `_pages/publications.html`. Joint first-author papers that SciX lists with you second are set in `JOINT_FIRST_AUTHOR` at the top of that script.
