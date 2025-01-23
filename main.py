import random
import time
from threading import Thread
from agents import Fournisseur, Acheteur, Coalition
from itertools import combinations
from collections import namedtuple

REDUCTIONS_COMBINAISONS = {
    ("acheteur1",): 0,
    ("acheteur3",): 1,
    ("acheteur1", "acheteur2"): 3,
    ("acheteur1", "acheteur2", "acheteur3"): 1,
    ("acheteur2", "acheteur3"): 2,
    ("acheteur4",): 0,
    ("acheteur4", "acheteur5"): 3,
    ("acheteur1", "acheteur4"): 2
}

def load_config(file_path):
    """Charge la configuration depuis un fichier JSON."""
    import json
    with open(file_path, "r") as file:
        return json.load(file)

def valeur_coalition(coalition):
    """Calcule la valeur d'une coalition en fonction des budgets et de la réduction prédéfinie."""
    noms_acheteurs = tuple(sorted(acheteur.name.lower() for acheteur in coalition))
    reduction = REDUCTIONS_COMBINAISONS.get(noms_acheteurs, 0)  # Réduction par défaut : 0%
    budgets = [acheteur.budget for acheteur in coalition]
    valeur_totale = sum(budgets) * (reduction / 100)
    return valeur_totale

def former_coalitions_idp(acheteurs):
    """Forme les meilleures coalitions avec l'approche Improved Dynamic Programming."""
    # Cache pour stocker la meilleure valeur et la meilleure coalition pour chaque ensemble d'acheteurs
    cache = {}

    def valeur_coalition_memo(coalition):
        """Calcule ou récupère la meilleure valeur et la meilleure coalition mémorisée."""
        noms_acheteurs = tuple(sorted([acheteur.name.lower() for acheteur in coalition]))
        
        # Si la coalition est déjà calculée, on récupère à la fois la valeur et la coalition
        if noms_acheteurs in cache:
            return cache[noms_acheteurs]
        
        # Calcul de la valeur totale pour cette coalition
        valeur_totale = valeur_coalition(coalition)
        
        # Stockage dans le cache : (valeur_totale, coalition)
        cache[noms_acheteurs] = (valeur_totale, coalition)
        
        return valeur_totale, coalition

    meilleures_coalitions = []
    acheteurs_restants = set(acheteurs)

    while acheteurs_restants:
        meilleure_coalition = None
        meilleure_valeur = 0

        sous_coalitions = {tuple([acheteur]) for acheteur in acheteurs_restants}  

        while sous_coalitions:
            nouvelle_generation = set()
            for coalition in sous_coalitions:
                # Récupération ou calcul de la valeur de la coalition
                valeur, _ = valeur_coalition_memo(coalition)
                if valeur > meilleure_valeur:
                    meilleure_valeur = valeur
                    meilleure_coalition = coalition

                # Étendre la coalition avec un autre acheteur restant
                for acheteur in acheteurs_restants - set(coalition):
                    nouvelle_coalition = tuple(sorted(set(coalition) | {acheteur}, key=lambda a: a.name.lower()))
                    if nouvelle_coalition not in cache:  # Éviter les doublons
                        nouvelle_generation.add(nouvelle_coalition)

            sous_coalitions = nouvelle_generation  

        if meilleure_coalition:
            noms_acheteurs = tuple(sorted([acheteur.name for acheteur in meilleure_coalition]))
            reduction = REDUCTIONS_COMBINAISONS.get(noms_acheteurs, 0)

            coalition = Coalition(list(meilleure_coalition), reduction)
            meilleures_coalitions.append(coalition)

            acheteurs_restants -= set(meilleure_coalition)

    return meilleures_coalitions


if __name__ == "__main__":
    config = load_config("config.json")
    mode = config.get("mode", "normal")
    print(f"Mode de négociation : {mode}")

    # Initialiser les fournisseurs
    fournisseurs = []
    for fournisseur_data in config["fournisseurs"]:
        fournisseur = Fournisseur(
            fournisseur_data["name"],
            fournisseur_data["host"],
            fournisseur_data["port"],
            fournisseur_data["services"]
        )
        fournisseurs.append(fournisseur)

    print("Fin de l'importation des fournisseurs")
    # Initialiser les acheteurs
    acheteurs = []
    for acheteur_data in config["acheteurs"]:
        acheteur = Acheteur(
            acheteur_data["name"],
            acheteur_data["host"],
            acheteur_data["port"],
            acheteur_data["budget"],
            acheteur_data["preferences"]
        )
        acheteurs.append(acheteur)


    print("fin de l'importation des acheteurs")
    # Former des coalitions
    coalitions = former_coalitions_idp(acheteurs)
    print("fin de la formation des coalitions")
    for coalition in coalitions:
        print(coalition)

    # Démarrage des serveurs
    agents = fournisseurs + acheteurs
    threads = [Thread(target=agent.start_server) for agent in agents]
    for thread in threads:
        thread.start()

    time.sleep(1)

# Simulation des propositions
for fournisseur in fournisseurs:
    for coalition in coalitions:
        # On boucle d'abord sur les acheteurs de la coalition
        for acheteur in coalition.acheteurs:
            # Si l'acheteur a déjà acheté quelque chose, on passe à l'acheteur suivant
            if acheteur.achete:
                print(f"{acheteur.name} a déjà acheté un service.")
                continue

            # Boucle sur les services proposés par ce fournisseur
            for service_id, service in list(fournisseur.services.items()):  # Utiliser list pour pouvoir modifier la dict
                # On propose un service si l'acheteur n'a pas encore acheté ce service
                prix_avec_reduction = coalition.appliquer_reduction(service["prix_min"])
                print(f"{fournisseur.name} propose {service_id} à {prix_avec_reduction} euros pour {coalition}.")

                message = {
                    "service_id": service_id,
                    "prix": prix_avec_reduction,
                    "details": service,
                    "fournisseur": fournisseur.name,
                    "fournisseurHost": fournisseur.host,
                    "port": fournisseur.port
                }
                acheteur.send_message(acheteur.host, acheteur.port, message)

                reponse = acheteur.receive_message()
                decision = reponse.get("decision")
                if decision == "accepter":
                    print(f"{acheteur.name} a accepté l'offre pour {service_id}.")
                    # L'acheteur a acheté le service, donc on marque son achat
                    acheteur.achete = True  # Marque que l'acheteur a acheté un service

                    # Le service est retiré des services proposés par le fournisseur
                    fournisseur.services.pop(service_id)

                    # Ajoute le service à la liste des services achetés du fournisseur
                    fournisseur.services_achetes.add(service_id)

                    break  # On arrête la boucle sur les services pour cet acheteur
                else:
                    print(f"{acheteur.name} a refusé l'offre pour {service_id}.")

