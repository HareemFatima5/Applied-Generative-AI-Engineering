# Section Metadata Extraction

Each chunk now carries the heading of the section it came from, in
addition to the document level metadata already extracted (title,
author, subject, page).

Headings are detected by looking at bold text rather than font size
since in these documents section headings are usually the same size
as the body text but bold. A line only counts as a heading if it is
bold, is not a bare number is between one and fourteen words, does
not start with "Fig", "Table", or "Eq." and does not end on a
preposition or article like "to" or "the", which filters out
boilerplate journal text that happens to be bold but is really a
sentence continuing rather than a title. Headings that wrap across
two physical lines are merged into one before these checks run so a
heading split across two lines is not cut down to just its second
half.

Only one heading is tracked per page, taken as the last one found on
that page. A page covering more than one subsection will have all of
its chunks tagged with that same last heading rather than the one
closest to each individual chunk.

While building this, the chunking logic was also cleaned up: a long
paragraph that needs character-based splitting no longer has its
overlap applied twice since it is now added once by the same general
overlap step used everywhere else instead of also being handled
separately inside the splitting step.
