# v16.3.1 — Language switch reliability fix

- Fixed the sidebar remaining in Traditional Chinese after selecting English or Thai.
- Fixed the user role label remaining in the previous language.
- Preserved the currently selected navigation page while rebuilding the menu.
- Added `data-i18n` metadata to dynamically generated navigation buttons.
- Isolated dynamic refresh functions so one rendering problem does not interrupt the entire language switch.
- Removed the duplicated embedded translation/application source from `index.html`; it now loads the maintained external files.
- Added a visible build marker and clearer extraction instructions to prevent opening an older temporary copy.
