import datetime
import json
import mimetypes
import requests
import sys
from os import listdir, rename, makedirs
from os.path import isfile, join, exists
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


def get_new_names(files, api_key, keep_info, max_nb):
    """
    Get array of 2-tuples with old and new names
    :param files: list of files
    :param api_key: API key of TheMovieDB (https://www.themoviedb.org)
    :param keep_info: Select if the info (Audio + Sub languages) is kept at the end of the new name
    :return: Array of tuples with old and new names for each file
    """
    new_names = []
    not_found = []
    count = 0
    file_nb = len(files)
    for f in files:
        print('Processing {}/{} files ({:.2f} %)'.format(count+1, file_nb, ((count+1)/file_nb)*100))
        count += 1
        if max_nb != -1 and count > max_nb:
            break
        try:
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
                else:
                    not_found.append(f)
                    continue

            if keep_info:
                new_movie_name += movie_info
            else:
                dot_index = movie_info.index('.')
                new_movie_name += movie_info[dot_index:]

            new_names.append((f, new_movie_name))
        except ValueError:
            not_found.append(f)
            pass

    return new_names, not_found


def save_output(new_names, not_found):
    """
    Save new names array and not found array in files
    :param new_names:
    :param not_found:
    """
    print(new_names)
    print('Failed on {} files'.format(len(not_found)))
    print(not_found)
    output_dir = 'output'
    now = datetime.datetime.now()
    now_string = now.strftime('%Y%m%d-%H%M')

    if not exists(output_dir):
        makedirs(output_dir)

    with open(join(output_dir, now_string+' - new_names.json'), 'w') as new_names_json:
        json.dump(new_names, new_names_json)
    with open(join(output_dir, now_string+' - not_found.json'), 'w') as not_found_json:
        json.dump(not_found, not_found_json)


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
        if len(sys.argv) > 1:
            path = sys.argv[1]
            max_nb = -1
            if len(sys.argv) > 2:
                max_nb = int(sys.argv[2])

            change_mimetypes = ['video/', 'application/x-subrip']

            # List files
            files = list_files(path, change_mimetypes)

            # Parse files
            new_names, not_found = get_new_names(files, api_key, True, max_nb)
            save_output(new_names, not_found)

            # Rename
            rename_files(path, new_names)
