import random


def get_reduction(noms_acheteurs):
    """Retourne la réduction de la coalition en fonction de la longeur des acheteurs."""
    return random.randint(10 * (len(noms_acheteurs) - 1), len(noms_acheteurs) * 10)