# Site conventions

This is a personal portfolio, built as a static site and hosted on GitHub Pages.

## Structure
- `pages/` holds About and Contact (About is also the home page)
- `work/` holds one Markdown file per case study
- `notes/` holds one Markdown file per blog post
- `images/` holds images, which are resized on build
- `templates/base.html` is the shared layout
- `static/style.css` is the stylesheet
- `build.py` generates the site into `dist/`, along with the RSS feed and sitemap

## Front matter
- Pages: title, summary
- Work: title, summary, role, order, cover (optional image filename)
- Notes: title, date (YYYY-MM-DD), summary, draft (true or false)

## Rules
- Push to main deploys the site automatically via GitHub Actions
- Never commit the `dist/` folder
- Keep `build.py` simple, with minimal dependencies
- Write in plain, direct English. No filler.
- Make small, focused changes and explain what changed
