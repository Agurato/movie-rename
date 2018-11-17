import mimetypes
import requests
from os import listdir, rename
from os.path import isfile, join
from urllib.parse import quote


def list_files(path, change_mimetypes):
    """
    Get all files which correspond to one of the mime types passed in parameter
    :param path: Folder where to search for files
    :param change_mimetypes: MIME types allowed
    :return: Files filtered
    """
    all_files = [f for f in listdir(path) if isfile(join(path, f))]
    need_change = []

    for f in all_files:
        file_mime = mimetypes.guess_type(f)[0]
        for mime in change_mimetypes:
            if mime in file_mime:
                need_change.append(f)

    return need_change


def get_new_names(files, api_key, keep_info):
    """
    Get array of 2-tuples with old and new names
    :param files: list of files
    :param api_key: API key of TheMovieDB (https://www.themoviedb.org)
    :param keep_info: Select if the info (Audio + Sub languages) is kept at the end of the new name
    :return: Array of tuples with old and new names for each file
    """
    new_names = []
    for f in files:
        index_sep = f.index(' - ')
        movie_name = f[:index_sep]
        movie_info = f[index_sep:]
        new_movie_name = movie_name
        query = quote(movie_name)

        get_movie_id = requests.get('https://api.themoviedb.org/3/search/movie?api_key='+api_key+'&query='+query)
        if get_movie_id.status_code == 200:
            results = get_movie_id.json()['results']
            if len(results) > 0:
                movie_id = results[0]['id']

                get_movie_info = requests.get('https://api.themoviedb.org/3/movie/'+str(movie_id)+'?api_key='+api_key)
                if get_movie_info.status_code == 200:
                    release_date = get_movie_info.json()['release_date']
                    new_movie_name = movie_name + ' ('+release_date.split('-')[0]+')'
        if keep_info:
            new_movie_name += movie_info
        else:
            dot_index = movie_info.index('.')
            new_movie_name += movie_info[dot_index:]

        new_names.append((f, new_movie_name))

    return new_names


def rename_files(path, new_names):
    """
    Rename files in parameters
    :param path: Folder where the files are
    :param new_names: Array of 2-tuples (old_name, new_name)
    """
    for name in new_names:
        rename(join(path, name[0]), join(path, name[1]))


if __name__ == '__main__':
    with open('api_key.txt', 'r') as api_key_txt:
        api_key = api_key_txt.read().replace('\n', '')
        path = 'D:\Films - Séries\A MUX'

        change_mimetypes = ['video/', 'application/x-subrip']

        # List files
        files = list_files(path, change_mimetypes)

        # Parse files
        new_names = get_new_names(files, api_key, True)
        print(new_names)

        # Rename
        rename_files(path, new_names)
