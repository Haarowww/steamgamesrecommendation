"""
CSC111 Final Project: Recommendation for games and game friends
"""
from __future__ import annotations
from typing import Any, Union
import json
import math
import tkinter as tk
import tkinter.messagebox
import python_ta


####################################################################################################
# Part 1: load .json files and pre-processing data
####################################################################################################


def open_user_review(file_name: str) -> list[dict]:
    """
    Read the data file 'australian_user_reviews.json'.
    Load the review data and transform it into list[dict].
    Each element in the list is the review data from one user.
    And we drop some data with extremely messy strings.
    """
    with open(file_name, encoding="utf-8") as f:
        s = f.read()
        # avoid JSONDecodeError when calling json.loads
        s = s.replace('\'', '\"')
        s = s.replace('True', '\"True\"')
        s = s.replace('False', '\"False\"')
        # using s.split("\n") to divide review data from each user
        data = s.split("\n")
        data_so_far = []
        for x in data:
            try:
                # for each user, we drop their detailed comments to avoid JSONDecodeError.
                # Since there are lots of messy strings in detailed comments.
                s = x.split('\"reviews\": ')[1][:-2]
                s = s.split('\"funny\": \"\", ')
                h = ['{' + m for m in s[1:]]
                reviews_so_far = []
                for y in h:
                    j = y.split(', \"review\":')[0] + '}'
                    reviews_so_far.append(json.loads(j))
                # reviews_so_far is a clean list of the user's reviews of games,
                # in which we drop user's detailed comments.
                i = x.split(', \"reviews\":')[0] + '}'
                user_data = json.loads(i)
                # i is the information of user's account.
                user_data['reviews'] = reviews_so_far
                data_so_far.append(user_data)
            except (json.decoder.JSONDecodeError, IndexError):
                # we drop the data with extremely messy strings to avoid JSONDecodeError
                pass

    return data_so_far


def open_steam_games(file_name: str) -> list[dict]:
    """
    Read the data file 'steam_games.json'.
    Load the games' data and transform it into list[dict].
    Each element in the list is the data of one game.
    And we drop some data with extremely messy strings.
    """
    with open(file_name, encoding="utf-8") as f:
        s = f.read()
        # avoid JSONDecodeError when calling json.loads
        s = s.replace('u\'', '\"')
        s = s.replace('\'', '\"')
        s = s.replace('True', '\"True\"')
        s = s.replace('False', '\"False\"')
        # using s.split("\n") to divide data of each game
        data = s.split("\n")
        data_so_far = []

        for x in data:
            try:
                data_so_far.append(json.loads(x))
            except json.decoder.JSONDecodeError:
                # we drop the data with extremely messy strings to avoid JSONDecodeError
                pass
            else:
                pass

    return data_so_far


def filter_the_reviews_data(file_name: str) -> dict:
    """the function that filter the reviews data

    this file format is {'user_id': ([{'item_id': 'recommend'},...], 'user_url')}
    """
    single_data = {}
    data = open_user_review(file_name)
    for item in data:
        single_data[item['user_id']] = ([{x['item_id']: x['recommend']} for x in item['reviews']],
                                        item['user_url'])

    return single_data


def filter_the_games_data(file_name: str) -> dict:
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


###################################################################################################
# Part 2: Construct the Graph to store data about users, reviews, and games.
# Using simularity scores to do recommendation for game friends and games.

# file we gonna use
FILE_NAME = 'json/steam_games.json'


###################################################################################################


class _ReviewVertex:
    """A vertex in our game recommendation graph, which can represent a user or a game.

    Each vertex item is either a user id or game title. Both are represented as strings.

    Instance Attributes:
        - item: The data stored in this vertex, representing a user or a game.
        - kind: The type of this vertex: 'user' or 'game'.
        - neighbours: The vertices that are adjacent to this vertex.

    Representation Invariants:
        - self not in self.neighbours
        - all(self in u.neighbours for u in self.neighbours)
        - self.kind in {'user', 'game'}

    """
    item: Any
    kind: str
    url: str
    neighbours: dict[_ReviewVertex, Union[int, float]]

    def __init__(self, item: Any, kind: str, url: str) -> None:
        """Initialize a new vertex with the given item and kind.

        This vertex is initialized with no neighbours.

        Preconditions:
            - kind in {'user', 'game'}
        """
        self.item = item
        self.kind = kind
        self.url = url
        self.neighbours = {}

    def get_url(self) -> str:
        """get the url page of one single game or one single user
        """
        return self.url

    def get_consice_similarity(self, other: _ReviewVertex) -> float:
        """the function that can help to get the consice similarity of two users.

        """
        user1 = []
        user2 = []
        for item in self.neighbours:
            if item in other.neighbours:
                user1.append(self.neighbours[item])
                user2.append(other.neighbours[item])
            else:
                user1.append(self.neighbours[item])
                user2.append('N/A')

        for item in other.neighbours:
            if item not in self.neighbours:
                user1.append('N/A')
                user2.append(other.neighbours[item])

        return consice_similarity(user1, user2)


class GameRecommendationGraph:
    """A graph that used to represent a game review networks and contains the ratings to each games.

    """
    _vertices: dict[Any, _ReviewVertex]

    def __init__(self) -> None:
        """Initialize a new empty game recommendation graph.
        """
        self._vertices = {}

    def add_vertex(self, item: Any, kind: str, url: str) -> None:
        """Add a new vertex in this graph.

        Preconditions:
            - kind in {'user', 'game'}
        """
        if item not in self._vertices:
            self._vertices[item] = _ReviewVertex(item, kind, url)

    def add_edge(self, item1: Any, item2: Any, weight: Union[int, float]) -> None:
        """Add an edge between the two vertices with the given items in this graph,
        with the given weight.

        Raise a ValueError if item1 or item2 do not appear as vertices in this graph.

        Preconditions:
            - item1 != item2
        """
        if item1 in self._vertices and item2 in self._vertices:
            v1 = self._vertices[item1]
            v2 = self._vertices[item2]

            v1.neighbours[v2] = weight
            v2.neighbours[v1] = weight
        else:
            raise ValueError

    def adjacent(self, item1: Any, item2: Any) -> bool:
        """Return whether item1 and item2 are adjacent vertices in this graph.

        Return False if item1 or item2 do not appear as vertices in this graph.
        """
        if item1 in self._vertices and item2 in self._vertices:
            v1 = self._vertices[item1]
            return any(v2.item == item2 for v2 in v1.neighbours)
        else:
            return False

    def get_weight(self, item1: Any, item2: Any) -> Union[int, float]:
        """Return the weight of the edge between the given items.

        Return 0 if item1 and item2 are not adjacent.

        Preconditions:
            - item1 and item2 are vertices in this graph
        """
        v1 = self._vertices[item1]
        v2 = self._vertices[item2]
        return v1.neighbours.get(v2, 0)

    def get_all_vertices(self, kind: str = '') -> set:
        """Return a set of all vertex items in this graph.

        If kind != '', only return the items of the given vertex kind.

        Preconditions:
            - kind in {'', 'user', 'game'}
        """
        if kind != '':
            return {v.item for v in self._vertices.values() if v.kind == kind}
        else:
            return set(self._vertices.keys())

    ################################################################################################
    # the following codes are our main body of the graph
    ################################################################################################

    def get_two_items_similarity_score(self, item1: Any, item2: Any) -> float:
        """get the similarity score of two items.

        test for this function: self.get_two_items_similarity_score('DJKamBer', '76561198077246154')
        """
        if item1 in self._vertices and item2 in self._vertices:
            return self._vertices[item1].get_consice_similarity(self._vertices[item2])
        else:
            raise ValueError

    def find_similar_player(self, player: Any, limit: int) -> Any:
        """find players that has similar ratings to the given player

        Preconditions:
            - player in self._vertices
            - self._vertices[player].kind == 'user'
            - limit >= 1

        """
        if player not in self._vertices:
            return 'out of range'

        users = self.get_all_vertices(kind='user')
        users_score = [(x, self.get_two_items_similarity_score(x, player))
                       for x in users if x != player]

        s1 = sorted(users_score, key=lambda x: x[0], reverse=True)
        s2 = sorted(s1, key=lambda x: x[1], reverse=True)
        result_so_far = []
        for i in range(0, limit):
            if s2[i][1] == 0:
                pass
            else:
                result_so_far.append(s2[i][0])

        if len(result_so_far) == 0:
            return 'No recommended friends'
        else:
            return [(user, self._vertices[users].get_url()) for user in result_so_far]

    def recommend_games(self, game: str, limit: int) -> Union[list[tuple[str, str]], str]:
        """this function can help to recommend the games that satisfies your favorite.

        Preconditions:
            - game in self._vertices
            - self._vertices[game].kind == 'game'
            - limit >= 1

        """
        if game not in self._vertices:
            return 'out of range'

        games = self.get_all_vertices(kind='game')
        games_scores = [(x, self.get_two_items_similarity_score(x, game))
                        for x in games if x != game]

        s1 = sorted(games_scores, key=lambda x: x[0], reverse=True)
        s2 = sorted(s1, key=lambda x: x[1], reverse=True)

        recommend_so_far = []
        for i in range(0, limit):
            if s2[i][1] == 0:
                pass
            else:
                recommend_so_far.append(s2[i][0])

        if len(recommend_so_far) == 0:
            return 'No recommended games'
        else:
            return [(game_id, self._vertices[game_id].url) for game_id in recommend_so_far]


####################################################################################################
# the following functions are given to prepare the environment for the above graph
####################################################################################################


def load_weighted_graph(reviews_file: str, game_names_file: str) -> GameRecommendationGraph:
    """Return a game recommendation WEIGHTED graph corresponding to the given datasets.

    try the following code to test this function:
    load_weighted_graph('json/example_user_reviews.json', 'steam_games.json')
    load_weighted_graph('australian_user_reviews.json', 'steam_games.json')

    format of game_files: {'id': ('app_name', 'url')}
    format of user_files: {'user_id': ([{'item_id': 'recommend'},...], 'user_url')}
    """
    user_files = filter_the_reviews_data(reviews_file)
    game_files = filter_the_games_data(game_names_file)

    graph = GameRecommendationGraph()

    for user_id in user_files:
        graph.add_vertex(item=user_id, kind='user', url=user_files[user_id][1])

        for review in user_files[user_id][0]:
            key = list(review.keys())[0]
            if key in game_files and review[key] == 'True':
                graph.add_vertex(game_files[key][0], 'game', game_files[key][1])
                graph.add_edge(user_id, game_files[key][0], weight=1)
            if key in game_files and review[key] == 'False':
                graph.add_vertex(game_files[key][0], 'game', game_files[key][1])
                graph.add_edge(user_id, game_files[key][0], weight=0)

    return graph


def consice_similarity(user1: list, user2: list) -> float:
    """
    compute the consice similarity of two users.
    >>> u1 = [4, 'N/A', 'N/A', 5, 1, 'N/A', 'N/A']
    >>> u2 = [5, 5, 4, 'N/A', 'N/A', 'N/A', 'N/A']
    >>> u3 = ['N/A', 'N/A', 'N/A', 2, 4, 5, 'N/A']
    >>> consice_similarity(u1, u2)
    0.38
    >>> consice_similarity(u1, u3)
    0.32
    """
    length = len(user1)
    above = 0
    for i in range(length):
        if user1[i] != 'N/A' and user2[i] != 'N/A':
            above += user1[i] * user2[i]

    m, n = 0, 0
    for i in range(length):
        if user1[i] != 'N/A':
            m += user1[i] ** 2
        if user2[i] != 'N/A':
            n += user2[i] ** 2
    below = math.sqrt(m) * math.sqrt(n)
    if above == 0 or below == 0:
        return 0
    else:
        return round(above / below, 2)


####################################################################################################
# Part 3: Construct an interface for users to do recommendation
####################################################################################################


def recommend(method: str, input_id: str, graph: GameRecommendationGraph) \
        -> Union[list[tuple[str, str]], str]:
    """Using the certain method to recommend games with the input id/app name.
    Return a list of recommended games/game users together with their url.

    Precondition:
        - method1 in {'user id', 'favorite game id'}
    """
    if method == 'user id':
        return recommend_user_id(input_id, graph)
    elif method == 'favorite game id':
        return recommend_game_id(input_id, graph)
    else:
        raise ValueError


def print_result(method: str, input_id: str, graph: GameRecommendationGraph) -> None:
    """
    Using the certain method to recommend games/game friends with the input id/app name.
    Show a messagebox including recommended games together with their url.
    Precondition:
        - method2 in {'user id', 'favorite game id'}
    """
    recommended_games = recommend(method, input_id, graph)
    if recommended_games == 'out of range':
        error_message = 'Sorry, the input id is not in our library. ' \
                        'We are very sorry we can"t make recommendation for this id.' \
                        '(Please be sure entering letter capitalization correctly. ' \
                        'The identification of game names is strict.'
        tkinter.messagebox.showwarning(title='Recommendation Games/Friends',
                                       message=error_message)
    elif recommended_games == 'No recommended games':
        error_message = 'We are very sorry that there is no recommended game ' \
                        'related to your favorite game.'
        tkinter.messagebox.showinfo(title='Recommendation Games/Friends',
                                    message=error_message)
    else:
        message_so_far = ''
        for game in recommended_games:
            message_so_far += 'ID: ' + game[0] + ', URL: ' + game[1] + '\n'
        tkinter.messagebox.showinfo(title='Recommendation Games/Friends', message=message_so_far)


def recommend_user_id(user_id: str, graph: GameRecommendationGraph) \
        -> Union[list[tuple[str, str]], str]:
    """
    Recommend at most 10 game friends to users with a certain user_id.
    Return a list of recommended friends together with their url.
    """
    return graph.find_similar_player(user_id, 10)


def recommend_game_id(game_name: str, graph: GameRecommendationGraph) \
        -> Union[list[tuple[str, str]], str]:
    """
    Recommend at most 10 games to users with their favorite game name.
    Return a list of recommended games together with their url.
    """
    return graph.recommend_games(game_name, 10)


def recommend_interface(graph: GameRecommendationGraph) -> None:
    """
    Construct an interface for users to make games recommendations based on a
    certain game id or a certain user id. User can choose the method of recommendation freely
    (with a game id or a user id). And after entering the id number, users can press the
    'Recommend!' button to get their unique game recommendation list.
    """
    # initialize the interface window
    window = tk.Tk()
    window.title('Games and Friends Recommendation')
    window.geometry('500x300')
    tk.Label(window, text='Welcome', font=('Arial', 16)).pack()

    # Use Radiobutton for users to choose the way to do recommendation
    method = tk.StringVar()
    method.set('user id')
    r1 = tk.Radiobutton(window, text='user id (recommend game friends)',
                        variable=method, value='user id')
    r1.pack()
    r2 = tk.Radiobutton(window, text='favorite game name (recommend games)',
                        variable=method, value='favorite game id')
    r2.pack()

    # Construct the entry box for users to enter id number
    id_entry = tk.Entry(window, show=None, font=('Arial', 14))
    id_entry.pack()

    # Construct the start button 'Recommend!' for users to start recommendation
    db = tk.Button(window, text="Recommend!",
                   command=(lambda: print_result(method.get(), id_entry.get(), graph)))
    db.pack()

    window.mainloop()


####################################################################################################
# Part 4: load data sets and call functions to do recommendation
####################################################################################################


recommendation_graph = load_weighted_graph('australian_user_reviews.json', 'steam_games.json')
recommend_interface(recommendation_graph)

python_ta.check_all(config={
    'extra-imports': ['json', 'math', 'tkinter', 'tkinter.messagebox'],
    # the names (strs) of imported modules
    'allowed-io': ['open_steam_games', 'open_user_review'],
    # the names (strs) of functions that call print/open/input
    'max-line-length': 100,
    'disable': ['E1136']
})
