# -*- coding: utf-8 -*-

import mimetypes
import os
import subprocess
import sys
from shutil import move


class Multiplexer:
    def __init__(self, mkvtools_path, movie_path):
        self.mkvtools_path = mkvtools_path

        self.movie_path = movie_path
        self.movie_name = os.path.basename(movie_path)
        self.parent_dir = os.path.abspath(os.path.join(movie_path, os.pardir))
        self.ext_index = self.movie_name.rfind(".")
        self.output_path = os.path.join(self.parent_dir, self.movie_name[:self.ext_index] + ".mux" + self.movie_name[self.ext_index:])
        self.subtitles = []

        self.failed = False
        self.msg = ""

    def mux(self, no_subtitles):
        self.subtitles = get_subtitles(self.parent_dir, self.movie_name[:self.ext_index])

        sub_params = f""
        for sub in self.subtitles:
            sub_filename = os.path.basename(sub)
            sub_info = sub_filename[self.ext_index:sub_filename.rfind(".")][1:]
            if 'forced' in sub_info:
                self.failed = True
                self.msg = "Forced subtitle"
            if len(sub_info) == 2:
                sub_params += f" --language 0:{sub_info} ( \"{sub}\" )"
            else:
                sub_params += f" --language 0:en ( \"{sub}\" )"

        track_order = ""
        if len(self.subtitles) == 0:
            self.failed = True
            self.msg = "No subtitle file"
        if len(self.subtitles) == 2:
            track_order = " --track-order \"1:0,0:0\""
        elif len(self.subtitles) > 2:
            self.failed = True
            self.msg = "More than 2 subtitles"

        get_track_number(self.mkvtools_path, self.movie_path)
        track_names = ""
        for index in range(0, get_track_number(self.mkvtools_path, self.movie_path)):
            track_names += f" --track-name {index}:\"\""

        if not self.failed:
            nosub_param = ""
            if no_subtitles:
                nosub_param = " --no-subtitles"
            params = f"--output \"{self.output_path}\" {sub_params} --no-attachments {nosub_param} {track_names} ( \"{self.movie_path}\" ) --title \"{os.path.splitext(self.movie_name)[0]}\" {track_order}"
            print("Muxing " + self.movie_path)
            try:
                subprocess.check_output(self.mkvtools_path + "\\mkvmerge.exe  " + params, stderr=subprocess.STDOUT, shell=True)
            except subprocess.CalledProcessError as e:
                self.failed = True
                self.msg = str(e.output)

    def clean(self):
        try:
            for s in self.subtitles:
                os.remove(s)
            os.remove(self.movie_path)
        except PermissionError as e:
            self.failed = True
            self.msg = str(e.strerror)
        try:
            move(self.output_path, self.movie_path)
        except PermissionError as e:
            self.failed = True
            self.msg = "Need to clean"


def get_movies(root_dir):
    """
    Get all movies
    :param root_dir: Folder where to search for files
    :return: Files filtered
    """
    movies = []

    for root, directories, filenames in os.walk(root_dir):
        for f in filenames:
            file_mime = mimetypes.guess_type(f)[0]
            if file_mime is not None and 'video/' in file_mime:
                movies.append(os.path.join(root, f))

    return movies


def get_subtitles(parent_path, movie_name):
    """
    Get subtitles from folder and movie name (without extension)
    :param parent_path:
    :param movie_name:
    :return:
    """
    all_files = [f for f in os.listdir(parent_path) if os.path.isfile(os.path.join(parent_path, f))]
    subtitles = []

    for f in all_files:
        if movie_name in f:
            if f.endswith(".srt"):
                subtitles.append(os.path.join(parent_path, f))

    return subtitles


def get_track_number(mkvtools_path, file):
    """
    Get track number in mkv file
    :param mkvtools_path: path to MKVToolNix folder
    :param file:
    :return: number of tracks in file
    """
    file_info = subprocess.Popen(f"{mkvtools_path}\\mkvinfo.exe \"{file}\"", shell=True, stdout=subprocess.PIPE).stdout.read().decode("utf-8")
    count_tracks = 0

    record_tracks = False

    for line in file_info.split("\n"):
        if line == "|+ Tracks":
            record_tracks = True
        elif record_tracks:
            if line.startswith("|+"):
                record_tracks = False
            elif line == "| + Track":
                count_tracks += 1

    return count_tracks


if __name__ == '__main__':

    failed_files = []
    mkvtools_path = r"D:\Logiciels\mkvtoolnix"

    maximum = -1
    count = 0
    no_subtitles = True

    if len(sys.argv) > 1:
        movies_path = sys.argv[1]
        movies = get_movies(movies_path)
        for movie in movies:
            if count == maximum:
                break
            multiplexer = Multiplexer(mkvtools_path, movie)
            multiplexer.mux(no_subtitles)
            if multiplexer.failed:
                failed_files.append((multiplexer.movie_path, multiplexer.msg))
            else:
                multiplexer.clean()
                count += 1

        if len(failed_files) > 0:
            print("\nFailed files :\n")
            for f in failed_files:
                print(f[0] + " : " + f[1])
        else:
            print("No failed files")
