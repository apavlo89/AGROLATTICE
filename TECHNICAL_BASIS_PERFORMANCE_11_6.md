# AGROLATTICE 11.6 — Technical basis: performance and navigation

Release 11.6 changes runtime architecture, not scientific algorithms.

## Identified bottleneck

The 11.5 application called `country_dataset_status(...)` during top-level
Streamlit execution. That helper reread the complete active-country CSV into a
new Pandas DataFrame to calculate row, location and year counts. The same script
had already loaded the climate table for analysis. Because Streamlit reruns the
script on navigation/control changes, this redundant read could be repeated.

In the release-build Linux container, a direct read/status calculation on the
bundled Mexico CSV (~579.4 MB, 8,792,484 rows) took about **9.43 seconds** and
reached roughly **1.51 GB** maximum resident memory for that short-lived probe.
These figures are environment-specific and are not promised Windows timings;
they document why the code path was removed.

## Process-local resource cache

`st.cache_data` is designed around serialised/copy-on-return data semantics.
That is useful for ordinary tables but undesirable for a multi-million-row
immutable application dataset on every navigation rerun. Release 11.6 uses a
process-local `st.cache_resource` for the prepared active-country runtime.
Downstream code treats those DataFrames as read-only.

The cache key contains path, file size and nanosecond modification time for both
worldcities and the active climate CSV. Dataset Updater installation therefore
changes the key without hashing the entire 579 MB file on every rerun.

## Coordinate attachment

11.5 performed a full DataFrame many-to-one merge to attach latitude/longitude
to every climate row. 11.6 aligns the small unique country location lookup to
climate row keys and adds only the two coordinate arrays. If all climate
locations match the catalogue (the normal updater-generated case), the analysis
frame aliases the cleaned climate frame instead of duplicating all six climate
columns. If unmatched locations exist, a filtered frame retains the previous
inner-match behaviour.

## Database service resources

The database classes do not hold persistent SQLite connections; methods open
connections when needed. Caching the service objects therefore avoids repeated
`CREATE TABLE IF NOT EXISTS`, migration inspection and integrity initialisation
on ordinary Streamlit reruns without caching transaction state. Manual service
reinitialisation remains available in System Diagnostics.

## Settings I/O

`global_country_support.save_settings` now compares the logical persisted
values and skips the atomic rewrite when nothing changed. This preserves useful
modification timestamps and removes routine disk writes during navigation.

## Scientific invariants

No climate measurement is rounded/recomputed for performance. No model or
validated crop parameter was changed. Field, trial, Twin and Research Evidence
SQLite schemas are unchanged. The Mechanistic Maize Twin source file is
unchanged byte-for-byte from 11.5 in the release build.
