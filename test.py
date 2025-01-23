from collections import namedtuple
from agents import Acheteur, Coalition, generer_reduction


# Définition des acheteurs
Acheteur = namedtuple("Acheteur", ["name", "budget"])
acheteur1 = Acheteur("acheteur1", 450)
acheteur2 = Acheteur("acheteur2", 400)
acheteur3 = Acheteur("acheteur3", 500)

REDUCTIONS_COMBINAISONS = {
    ("acheteur1",): 0,
    ("acheteur1", "acheteur2"): 3,
    ("acheteur1", "acheteur2", "acheteur3"): 1,
    ("acheteur2", "acheteur3"): 2,
}

# Définition des coalitions de test
coalitions = [
    [acheteur1],
    [acheteur1, acheteur2],
    [acheteur1, acheteur2, acheteur3],
    [acheteur2, acheteur3],
]

def valeur_coalition(coalition):
    print("passe ici")
    print(coalition)
    """Calcule la valeur d'une coalition en fonction des budgets et de la réduction prédéfinie."""
    # Génération des noms des acheteurs en minuscules et triés
    noms_acheteurs = tuple(sorted(acheteur.name.lower() for acheteur in coalition))
    print(noms_acheteurs)
    # Recherche de la réduction pour cette coalition
    reduction = REDUCTIONS_COMBINAISONS.get(noms_acheteurs, 0)  # Réduction par défaut : 0%
    
    # Calcul de la valeur totale en fonction de la réduction
    budgets = [acheteur.budget for acheteur in coalition]
    valeur_totale = sum(budgets) * (reduction / 100)
    return valeur_totale


# Test des valeurs pour chaque coalition
for coalition in coalitions:
    valeur = valeur_coalition(coalition)
    print(f"Coalition: {[acheteur.name for acheteur in coalition]}, Valeur: {valeur}")


