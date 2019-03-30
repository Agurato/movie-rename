import mimetypes
import os
import subprocess
import sys
from shutil import move


class Multiplexer:
    def __init__(self, mkvmerge_path, movie_path):
        self.mkvmerge_path = mkvmerge_path

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
            movie_dots = sub_filename.split(".")
            sub_info = sub_filename[self.ext_index:sub_filename.rfind(".")][1:]
            if 'forced' in sub_info:
                self.failed = True
                self.msg = "Forced subtitle"
            if len(sub_info) == 2:
                sub_params += f" --language 0:{sub_info} ( \"{sub}\" )"
            else:
                sub_params += f" --language 0:en ( \"{sub}\" )"
                # self.failed = True
                # self.msg = "No language in srt name"

        track_order = ""
        if len(self.subtitles) == 0:
            self.failed = True
            self.msg = "No subtitle file"
        if len(self.subtitles) == 2:
            track_order = " --track-order \"1:0,0:0\""
        elif len(self.subtitles) > 2:
            self.failed = True
            self.msg = "More than 2 subtitles"

        if not self.failed:
            nosub_param = ""
            if no_subtitles:
                nosub_param = " --no-subtitles"
            params = f"--output \"{self.output_path}\" {sub_params} {nosub_param} ( \"{self.movie_path}\" ) --title \"\" {track_order}"
            print("Muxing " + self.output_path)
            try:
                subprocess.check_output(self.mkvmerge_path + "  " + params, stderr=subprocess.STDOUT, shell=True)
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
    :param path: Folder where to search for files
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
            file_mime = mimetypes.guess_type(f)[0]
            if file_mime == 'application/x-subrip':
                subtitles.append(os.path.join(parent_path, f))

    return subtitles


if __name__ == '__main__':

    failed_files = []
    mkvmerge_path = "D:\\Logiciels\\Installations\\mkvtoolnix\\mkvmerge.exe"

    max = -1
    count = 0
    no_subtitles = True

    if len(sys.argv) > 1:
        movies_path = sys.argv[1]
        movies = get_movies(movies_path)
        for movie in movies:
            if count == max:
                break
            multiplexer = Multiplexer(mkvmerge_path, movie)
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
