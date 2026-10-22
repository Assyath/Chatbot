import os

import httpx


def recherche_web(requete: str, actualites: bool = False, max_resultats: int = 5) -> str:
    """Recherche des informations à jour sur Internet (sujets, entreprises, personnes, événements, actualités).

    Args:
        requete: La recherche à effectuer, formulée en mots-clés clairs.
        actualites: True pour des actualités récentes, False pour une recherche générale.
        max_resultats: Nombre de résultats souhaités (entre 1 et 10).
    """
    api_key = os.environ.get("TAVILY_API_KEY", "")
    if not api_key:
        return "Erreur : la clé API Tavily n'est pas configurée."

    body = {
        "query": requete,
        "topic": "news" if actualites else "general",
        "max_results": max(1, min(max_resultats, 10)),
        "search_depth": "basic",
    }

    if actualites:
      body["time_range"] = "month"

    try:
        response = httpx.post(
            "https://api.tavily.com/search",
            json=body,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=20,
        )
        if response.status_code == 401:
            return "Erreur : clé API Tavily invalide."
        if response.status_code in (429, 432, 433):
            return "Erreur : limite d'utilisation de Tavily atteinte, réessaie plus tard."
        response.raise_for_status()
        results = response.json().get("results", [])
    except Exception as e:
        print(f"Erreur Tavily : {e}")
        return "Erreur temporaire lors de la recherche en ligne."

    if not results:
        return f"Aucun résultat trouvé pour : {requete}."

    lignes = []
    for r in results:
        date = f" ({r['published_date']})" if r.get("published_date") else ""
        lignes.append(
            f"- {r.get('title', 'Sans titre')}{date}\n"
            f"  {r.get('content', '')[:600]}\n"
            f"  Source : {r.get('url', '')}"
        )
    return "\n".join(lignes)