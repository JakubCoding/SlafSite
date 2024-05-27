import requests


class DataManager:
    URL_ENDPOINT_SLAF = "https://api-web.nhle.com/v1/player/8483515/landing"
    URL_ENDPOINT_LC = "https://api-web.nhle.com/v1/player/8483431/landing"
    def __init__(self):
        self.stats = {}

    def get_stats_data(self):
        global SHEETY_URL

        self.response = requests.get(url=self.SHEETY_URL)
        self.result = self.response.json()
        self.stats = self.result["slafy"]

        return self.stats

    def Slaf_Data(self):
        self.response = requests.get(url=self.URL_ENDPOINT_SLAF)
        self.data = self.response.json()
        # Slafy points
        self.season_totals = self.data.get("seasonTotals", [])
        self.current_season_games = self.data["featuredStats"]["regularSeason"]["subSeason"]["gamesPlayed"]
        self.current_season_goals = self.data["featuredStats"]["regularSeason"]["subSeason"]["goals"]
        self.current_season_assists = self.data["featuredStats"]["regularSeason"]["subSeason"]["assists"]
        self.current_season_plusminus = self.data["featuredStats"]["regularSeason"]["subSeason"]["plusMinus"]
        self.current_points = self.current_season_goals + self.current_season_assists
        return self.current_season_games, self.current_season_goals, self.current_season_assists, self.current_season_plusminus, self.current_points

    def LC_Data(self):
        self.response = requests.get(url=self.URL_ENDPOINT_LC)
        self.data = self.response.json()
        # Slafy points
        self.season_totals_LC = self.data.get("seasonTotals", [])
        self.current_season_games_LC = self.data["featuredStats"]["regularSeason"]["subSeason"]["gamesPlayed"]
        self.current_season_goals_LC = self.data["featuredStats"]["regularSeason"]["subSeason"]["goals"]
        self.current_season_assists_LC = self.data["featuredStats"]["regularSeason"]["subSeason"]["assists"]
        self.current_season_plusminus_LC = self.data["featuredStats"]["regularSeason"]["subSeason"]["plusMinus"]
        self.current_points_LC = self.current_season_goals_LC + self.current_season_assists_LC
        return self.current_season_games_LC, self.current_season_goals_LC, self.current_season_assists_LC, self.current_season_plusminus_LC, self.current_points_LC


