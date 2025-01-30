import random
import json


def get_reduction(noms_acheteurs):
    """Retourne la réduction de la coalition"""
    preferences = get_preferences_from_json("config.json", ["acheteur1", "acheteur2", "acheteur3"])
    similarity_score = calculate_similarity(preferences)
    similarity_score+=1
    return random.randint(1, similarity_score)
# on essaie de faire une coalition avec les acheteurs qui ont des preferences similaires.

def get_preferences_from_json(file_path, noms_acheteurs):
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    acheteurs = data.get('acheteurs', [])
    preferences = {}
    
    for acheteur in acheteurs:
        if acheteur['name'] in noms_acheteurs:
            preferences[acheteur['name']] = acheteur.get('preferences', {})
    
    return preferences

def calculate_similarity(preferences):
    similarity_score = 0
    acheteurs = list(preferences.keys())
    
    for i in range(len(acheteurs)):
        for j in range(i + 1, len(acheteurs)):
            acheteur1 = acheteurs[i]
            acheteur2 = acheteurs[j]
            prefs1 = preferences[acheteur1]
            prefs2 = preferences[acheteur2]
            
            for key in prefs1:
                if key in prefs2:
                    if prefs1[key]['name'] == prefs2[key]['name']:
                        similarity_score += 1
                        if prefs1[key]['order'] == prefs2[key]['order']:
                            similarity_score += 2
    
    return similarity_score

noms_acheteurs = ["acheteur1", "acheteur2", "acheteur3"]
