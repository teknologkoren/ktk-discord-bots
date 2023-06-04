# This script outputs all songs from Flerstämt in a format usable for the
# rotary tuning fork project.
# See https://github.com/teknologkoren/rotary-tuning-fork

import json

# Mapping from note name to mp3 file number on the device.
NOTE_FILES = {
    "G#": 2,
    "Ab": 3,
    "A": 4,
    "A#": 5,
    "Bb": 6,
    "B": 7,
    "C": 8,
    "C#": 9,
    "Db": 10,
    "D": 11,
    "D#": 12,
    "Eb": 13,
    "E": 14,
    "F": 15,
    "F#": 16,
    "Gb": 17,
    "G": 18
}

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
        notes.append(str(NOTE_FILES[note]))
    for i in range(5-len(song['tones'])):
        notes.append("-1")
    print(", ".join(notes), end="}},\n")
    
print("}")
