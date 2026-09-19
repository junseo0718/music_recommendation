from datetime import datetime

def get_current_season():
    month = datetime.now().month

    if 3 <= month <= 5:
        return "봄"

    if 6 <= month <= 8:
        return "여름"

    if 9 <= month <= 11:
        return "가을"

    else:
        return "겨울"

WEATHER_GENRES = {

    "Clear": [
        "hip-hop",
        "r-n-b",
        "k-pop"
    ],

    "Clouds": [
        "k-pop",
        "acoustic",
        "r-n-b"
    ],

    "Rain": [
        "acoustic",
        "indie",
        "r-n-b"
    ],

    "Drizzle": [
        "acoustic",
        "indie",
        "jazz"
    ],

    "Thunderstorm": [
        "rock",
        "alternative",
        "hip-hop"
    ],

    "Snow": [
        "r-n-b",
        "hip-hop",
        "classical"
    ],

    "Mist": [
        "indie",
        "ballad",
        "r-n-b"
    ],

    "Fog": [
        "indie",
        "hip-hop",
        "r-n-b"
    ]
}

SEASON_GENRES = {

    "봄": [
        "pop",
        "indie",
        "acoustic"
    ],

    "여름": [
        "dance",
        "pop",
        "k-pop"
    ],

    "가을": [
        "indie",
        "acoustic",
        "r-n-b"
    ],

    "겨울": [
        "acoustic",
        "jazz",
        "classical"
    ]
}

def get_recommendation_genres(season, weather):
    season_genres = SEASON_GENRES.get(season, [])
    weather_genres = WEATHER_GENRES.get(weather, [])

    genre_scores = {}
    for genre in season_genres:
        genre_scores.setdefault(genre, 0)

        genre_scores[genre] += 2

    for genre in weather_genres:
        genre_scores.setdefault(genre, 0)

        genre_scores[genre] += 3

    sorted_genres = sorted(genre_scores.items(),
                           key=lambda x: x[1],
                           reverse=True)

    return sorted_genres