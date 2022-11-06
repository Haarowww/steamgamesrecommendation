"""
CSC111 Final Project: Computing Similarity
"""
from __future__ import annotations

from typing import Any, Union
import math
import project


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
        if player in self._vertices:
            users = self.get_all_vertices(kind='user')
            users_score = [(self.get_two_items_similarity_score(user, player), user)
                           for user in users if user != player]
            users_score.sort(reverse=True)
            strict_users = users_score[:limit]
            result = []
            for single in strict_users:
                if single[1] not in result and single[0] > 0:
                    result.append((single[1], self._vertices[single[1]].get_url()))

            return result
        else:
            return 'out of range'

    def find_the_most_similar_player(self, player: Any) -> Any:
        """find the player that has the most similar ratings to the given player
        """
        if player in self._vertices:
            return self.find_similar_player(player, 1)[0]
        else:
            return 'out of range'

    def recommend_games(self, game: str, limit: int) -> list[str]:
        """this function can help to recommend the games that satisfies your favorite.

        Preconditions:
            - game in self._vertices
            - self._vertices[game].kind == 'game'
            - limit >= 1

        """
        games = self.get_all_vertices(kind='game')
        games_scores = [(x, self.get_two_items_similarity_score(x, game))
                        for x in games if x != game]

        s1 = sorted(games_scores, key=lambda x: x[0], reverse=True)
        s2 = sorted(s1, key=lambda x: x[1], reverse=True)

        recommend_so_far = []
        for i in range(0, limit):
            if s2[i][1] == 0:
                return recommend_so_far
            else:
                recommend_so_far.append(s2[i][0])

        return recommend_so_far


####################################################################################################
# the following functions are given to prepare the environment for the above graph
####################################################################################################


def load_weighted_graph(reviews_file: str, game_names_file: str) -> GameRecommendationGraph:
    """Return a game recommendation WEIGHTED graph corresponding to the given datasets.

    try the following code to test this function:
    load_weighted_graph('json/example_user_reviews.json', 'json/steam_games.json')
    load_weighted_graph('json/australian_user_reviews.json', 'json/steam_games.json')

    format of game_files: {'id': ('app_name', 'url')}
    format of user_files: {'user_id': ([{'item_id': 'recommend'},...], 'user_url')}
    """
    user_files = project.filter_the_reviews_data(reviews_file)
    game_files = project.filter_the_games_data(game_names_file)

    graph = GameRecommendationGraph()

    for user_id in user_files:
        graph.add_vertex(item=user_id, kind='user', url=user_files[user_id][1])

        for review in user_files[user_id][0]:
            if review != []:
                key = [x for x in review][0]
                if key in game_files:
                    graph.add_vertex(game_files[key][0], 'game', game_files[key][1])
                    if review[key] == 'True':
                        graph.add_edge(user_id, game_files[key][0], weight=1)
                    else:  # review[key] == 'False'
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
