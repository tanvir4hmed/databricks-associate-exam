# Databricks Associate Practice Room

Live website: https://tanvir4hmed.github.io/databricks-associate-exam/

280 archived questions with original diagrams/options, revealable answers, community vote bars, read-only discussion popups, and GPT concept notes shown as the first discussion user. Search, topic filtering, bookmarks, reviewed progress, pagination and direct question links work without a backend. Progress is stored only in the visitor's browser. There is no sign-in/profile widget, analytics, or comment submission.

## Publish

Every push to `main` verifies the collection and deploys `dist/` through GitHub Actions to GitHub Pages. The repository and website are public. GitHub Settings → Pages uses **GitHub Actions**. No deployment secrets are needed.

## Local preview

```sh
python scripts/build.py
python scripts/verify.py
python -m http.server 8765 --directory dist
```

Open http://localhost:8765. Serve over HTTP; loading the HTML directly from disk cannot fetch the JSON collection.

## Content

`content/questions.json` contains imported questions/discussions. `scripts/build.py` contains authored GPT concept notes and their official reference links. `dist/assets/` contains only question/answer diagrams. Saved source pages, account/profile elements, browser cookies and the original Word document are not published.

The importer reads a local folder containing the supplied six HTML pages, their companion asset folders and the discussion DOCX:

```sh
python -m pip install beautifulsoup4
python scripts/import_content.py "/path/to/RAW"
python scripts/build.py
```

The importer extracts Word text without rewriting community wording and removes answer-only assertions. `content/import-audit.json` records retention decisions for review. No community discussion is fabricated when the archive has none. Older and newer terminology coexist in the archive; GPT notes describe the related concepts and link official documentation. Archived answer keys/votes are not independently certified and can be disputed.

To change GPT notes, edit `scripts/build.py`, rebuild, verify, commit and push. Assets and the compiled JSON are committed so the deployed site has no runtime dependencies.
