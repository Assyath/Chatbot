import os

import httpx


def obtenir_meteo(ville: str) -> str:
    """Récupère la météo actuelle d'une ville.

    Args:
        ville: Le nom de la ville (ex: Paris, Accra, Cotonou)
    """
    api_key = os.environ.get("OPENWEATHER_API_KEY", "")
    if not api_key:
        return "Erreur : la clé API OpenWeather n'est pas configurée."

    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": ville, "appid": api_key, "units": "metric", "lang": "fr"}

    try:
        response = httpx.get(url, params=params, timeout=10)
        if response.status_code == 404:
            return f"Impossible de trouver la ville : {ville}."
        if response.status_code == 401:
            return "Erreur : clé API OpenWeather invalide ou pas encore activée."
        response.raise_for_status()
        data = response.json()
        return (
            f"Météo à {ville} : {data['main']['temp']}°C, "
            f"{data['weather'][0]['description']}. "
            f"Humidité : {data['main']['humidity']}%."
        )
    except Exception as e:
        print(f"Erreur météo : {e}")
        return f"Erreur temporaire lors de la récupération de la météo pour {ville}."