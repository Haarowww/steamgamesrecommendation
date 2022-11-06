import json


def open_user_review(file_name) -> list[dict]:
    with open(file_name, encoding="utf-8") as f:
        s = f.read()
        s = s.replace('\'', '\"')
        s = s.replace('True', '\"True\"')
        s = s.replace('False', '\"False\"')
        data = s.split("\n")
        data_so_far = []
        for x in data:
            try:
                s = x.split('\"reviews\": ')[1][:-2]
                s = s.split('\"funny\": \"\", ')
                h = ['{' + m for m in s[1:]]
                reviews_so_far = []
                for y in h:
                    j = y.split(', \"review\":')[0] + '}'
                    reviews_so_far.append(json.loads(j))
                i = x.split(', \"reviews\":')[0] + '}'
                user_data = json.loads(i)
                user_data['reviews'] = reviews_so_far
                data_so_far.append(user_data)
            except (json.decoder.JSONDecodeError, IndexError):
                pass

        return data_so_far


def filter_the_reviews_data(file_name='json/example_user_reviews.json') -> dict:
    """the function.

    this file format is {'user_id': ([{'item_id': 'recommend'},...], 'user_url')}
    """
    single_data = {}
    data = open_user_review(file_name)
    for item in data:
        single_data[item['user_id']] = ([{x['item_id']: x['recommend']} for x in item['reviews']],
                                        item['user_url'])

    return single_data


def open_steam_games(file_name='json/steam_games.json') -> list[dict]:
    with open(file_name, encoding="utf-8") as f:
        s = f.read()
        s = s.replace('u\'', '\"')
        s = s.replace('\'', '\"')
        s = s.replace('True', '\"True\"')
        s = s.replace('False', '\"False\"')
        data = s.split("\n")
        data_so_far = []

        for x in data:
            try:
                data_so_far.append(json.loads(x))
            except json.decoder.JSONDecodeError:
                pass
            else:
                pass

    return data_so_far


def filter_the_games_data(file_name='json/steam_games.json') -> dict:
    """the function

    the file format is {'id': ('app_name', 'url')}
    """
    dictionary = {}
    data = open_steam_games(file_name)
    for item in data:
        if 'id' in item:
            if 'title' in item:
                dictionary[item['id']] = (item['title'], item['url'])
            elif 'app_name' in item:
                dictionary[item['id']] = (item['app_name'], item['url'])
            else:
                dictionary[item['id']] = ('N/A', item['url'])
        else:
            pass
    return dictionary


def filter_for_game_graph(file_name='json/steam_games.json') -> list:
    """filter the useful information for game graph.

    the file format is [['game_name', 'game_id', 'tags', 'url'], ....]
    """
    file_so_far = []
    data = open_steam_games(file_name)
    for item in data:
        small_data = []
        if 'app_name' in item:
            small_data.append(item['app_name'])
        elif 'title' in item:
            small_data.append(item['title'])
        else:
            small_data.append('N/A')

        if 'id' in item:
            small_data.append(item['id'])
        else:
            small_data.append('N/A')

        if 'tags' in item:
            small_data.append(item['tags'])
        elif 'genres' in item:
            small_data.append(item['genres'])
        else:
            small_data.append('N/A')

        small_data.append(item['url'])

        file_so_far.append(small_data)

    return file_so_far
