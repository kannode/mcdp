# MCDP-vols {#mcdp-vols}

## Usage

    $ mcdp-book -d dest op-manual run
    $ mcdp-book -d dest op-manual status
    $ mcdp-book -d dest op-manual clean



# Semantics


## Variables

Variables:

- `sources`: list of markdown files
- `stylesheets`: list of CSS files
- `joined`: Joined document (BS4)
- `links`: Links generated


## Commands

### `add`

    add stylesheet ![stylesheets]

        Appends the stylesheets.

### `set`

    set ![name] ![value]

### `load`

    load ![var name] ![filename pattern]

### `source`

    source ![directories]

        Searches for markdown files in the directories
        Appends to ![sources].




### `render`

    render

Runs the rendering

Reads: sources, stylesheets
Writes: joined, links

### `note_errors`

Writes the errors to the file.

    note_errors <files>

### `remove_status`

    remove_status <status>

### `extract_assets`

    extract_assets out/filename.html out/assets

### `extract_links`

    extract_links <filename>

    load_links_recipes
