# This script outputs all songs from Flerstämt in a format usable for the
# rotary tuning fork project.
# See https://github.com/teknologkoren/rotary-tuning-fork

import json

def note_to_filename(note):
    if len(note) == 1:
        note += ' '
    return f'"{note}"'

# Load all songs with a page number into `songs`.
songs = []
with open('instance/songs.json', 'r') as f:
    songs_full = json.load(f)
    for song in songs_full:
        if 'page' not in song or song['page'] is None:
            continue
        songs.append(song)


# Output page numbers and starting note in C array initialization format, sorted
# by page number in alphabetic order.
print("{")
for song in sorted(songs, key=lambda song: str(song['page'])):
    if 'page' not in song or song['page'] is None:
        continue

    print("  {", song['page'], ", {", end="", sep="")
    notes = []
    for note in song['tones']:
        notes.append(note_to_filename(note))
    for i in range(5-len(song['tones'])):
        notes.append('""')
    print(", ".join(notes), end="}")
    print(f", {len(song['tones'])}", end="")
    print("},")
    
print("}")
