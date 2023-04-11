# Script for populating songs.json with links to Google Drive resources.
# Meant to be run separately, i.e. `python populate_song_links.py`.

import asyncio
import json
import pprint
import re
import sys

import google_client

from config import (
    DRIVE_SHEET_MUSIC_FOLDER,
    DRIVE_MIDI_FULL_FOLDER,
    DRIVE_MIDI_PARTS_FOLDER,
    DRIVE_SIBELIUS_FOLDER,
)

pp = pprint.PrettyPrinter(indent=4, stream=sys.stderr)
PARTS_PATTERN = re.compile(r'\w+$')


def find_song(files, number):
    for file in files:
        if file['name'].startswith(number):
            return file
    return None


def find_songs(files, tmp):
    res = []
    for file in files:
        if file['name'].startswith(tmp):
            res.append(file)
    return res


async def main():
    with open('songs.json', 'r') as f:
        songs = json.load(f)

    client = google_client.GoogleAPIClient()
    result = await client.list_drive_folder(DRIVE_SHEET_MUSIC_FOLDER, sort_by_name=True)

    for song, file in zip(sorted(songs, key=lambda s: int(s.get('page', '999'))), result['files']):
        assert song.get('page', None)
        song['flerstamt_number'] = file['name'][:4]
        song['tmp'] = file['name'][:-4]
        song['links'] = [
            ('Not', file['webViewLink'])
        ]

    midi_full_files = (await client.list_drive_folder(DRIVE_MIDI_FULL_FOLDER, sort_by_name=True))['files']
    midi_parts_files = (await client.list_drive_folder(DRIVE_MIDI_PARTS_FOLDER, sort_by_name=True))['files']
    sibelius_files = (await client.list_drive_folder(DRIVE_SIBELIUS_FOLDER, sort_by_name=True))['files']
    for song in songs:
        if not song.get('page', None):
            continue
        print(song['name'])
        print(song['flerstamt_number'])
        print(song['tmp'])
        midi_full = find_song(midi_full_files, song['flerstamt_number'])
        assert midi_full is not None
        print(midi_full['name'])
        midi_parts = find_songs(midi_parts_files, song['flerstamt_number'])
        assert len(midi_parts) > 0
        print([f['name'] for f in midi_parts])
        sibelius = find_song(sibelius_files, song['flerstamt_number'])
        assert sibelius is not None
        print(sibelius['name'])

        song['links'].append(("MIDI", midi_full['webViewLink']))

        for midi_part in midi_parts:
            match = PARTS_PATTERN.search(midi_part['name'][:-4])
            print(f"MIDI {match[0]}")
            song['links'].append((f"MIDI {match[0]}", midi_part['webViewLink']))

        song['links'].append(("Sibelius", sibelius['webViewLink']))
        song.pop('tmp')


    pp.pprint(songs)
    with open('songs.json', 'w') as f:
        json.dump(songs, f)


if __name__ == '__main__':
    asyncio.run(main())