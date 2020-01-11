import os
import subprocess
import sys
from iso639 import languages

class Track:
    def __init__(self, id=None, type=None, language=None):
        self.id = id
        self.type = type
        self.language = language

    def __repr__(self):
        return f"{self.id}: {self.type} - {self.language}"


def get_mkv_files(root_dir):
    """
    Get all MKV files
    :param root_dir: Folder where to search for files
    :return: Files filtered
    """
    mkv_files = []

    for root, directories, filenames in os.walk(root_dir):
        for f in filenames:
            if f.endswith(".mkv"):
                mkv_files.append(os.path.join(root, f))

    return mkv_files


def get_tracks(mkvinfo, mkv_file):
    """
    Get tracks for specific MKV file
    :param mkvinfo: path to mkvinfo.exe
    :param mkv_file: path to MKV file
    :return: list of tracks of input file
    """
    tracks = []
    file_info = subprocess.getoutput(f'{mkvinfo} "{mkv_file}"')

    record_tracks = False
    current_track_id = -1
    current_track_type = ""
    current_track_lang = "eng"
    for line in file_info.split("\n"):
        if line == "|+ Tracks":
            record_tracks = True
        elif record_tracks:
            if line.startswith("|+"):
                record_tracks = False
            elif line == "| + Track":
                if current_track_id != -1:
                    current_track_lang = languages.get(part2b=current_track_lang).part1
                    tracks.append(
                        Track(current_track_id, current_track_type, current_track_lang)
                    )
                current_track_id = -1
                current_track_type = ""
                current_track_lang = "eng"
            elif line.startswith("|  +"):
                if "Track number" in line:
                    current_track_id = int(line.split(" ")[5]) - 1
                elif "Track type" in line:
                    current_track_type = line.split(" ")[5]
                elif "Language" in line:
                    current_track_lang = line.split(" ")[4]
                    if current_track_lang == "und":
                        current_track_lang = "eng"

    tracks.append(Track(current_track_id, current_track_type, current_track_lang))
    return tracks


def filter_sub(tracks, langs):
    filtered = []
    for track in tracks:
        if track.type == "subtitles" and track.language in langs:
            filtered.append(track)
    return filtered


if __name__ == "__main__":
    """
    Extract subtitles from all mkv files in folder
    python extract_sub.py <folder> <lang1,lang2,...>
    """
    mkvtoolnix_path = r"C:\Dossiers\Logiciels\mkvtoolnix"
    mkvextract = os.path.join(mkvtoolnix_path, "mkvextract.exe")
    mkvinfo = os.path.join(mkvtoolnix_path, "mkvinfo.exe")

    folder = sys.argv[1]
    langs = sys.argv[2].split(",")

    mkv_files = get_mkv_files(folder)
    for mkv_file in mkv_files:
        tracks = filter_sub(get_tracks(mkvinfo, mkv_file), langs)
        tracks_param = ""
        for track in tracks:
            srt_path = mkv_file[:-4]+f".{track.language}.srt"
            tracks_param += f" {track.id}:\"{srt_path}\""
        extract_command = f"\"{mkvextract}\" \"{mkv_file}\" tracks {tracks_param}"
        subprocess.run(extract_command)
