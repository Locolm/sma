from logging import exception
import random
import time
from threading import Thread
from agents import Fournisseur, Acheteur, Coalition
from itertools import combinations
from collections import namedtuple
import reductions_combinaisons

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
    #reduction = REDUCTIONS_COMBINAISONS.get(noms_acheteurs, 0)  # Réduction par défaut : 0%
    reduction= reductions_combinaisons.get_reduction(noms_acheteurs)
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
            #reduction = REDUCTIONS_COMBINAISONS.get(noms_acheteurs, 0)
            reduction=reductions_combinaisons.get_reduction(noms_acheteurs)
            coalition = Coalition(list(meilleure_coalition), reduction)
            meilleures_coalitions.append(coalition)

            acheteurs_restants -= set(meilleure_coalition)

    return meilleures_coalitions

def former_coalitions_individuelles(acheteurs):
    """Forme des coalitions individuelles pour chaque acheteur."""
    coalitions = []
    for acheteur in acheteurs:
        noms_acheteurs = (acheteur.name,)
        reduction = reductions_combinaisons.get_reduction(noms_acheteurs)
        coalition = Coalition([acheteur], reduction)
        coalitions.append(coalition)
    return coalitions

def main():
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
            acheteur_data["preferences"],
            acheteur_data["strategie"]
        )
        acheteurs.append(acheteur)


    print("fin de l'importation des acheteurs")
    # Former des coalitions
    if ("coalition_unique" in config) and config["coalition_unique"]:
        coalitions = former_coalitions_individuelles(acheteurs) # Chaque acheteur forme sa propre coalition <==> aucune coalition
    else:
        coalitions = former_coalitions_idp(acheteurs) # Formation des coalitions avec l'approche Improved Dynamic Programming
    print("fin de la formation des coalitions")
    print("Affichage des coalitions :")
    for coalition in coalitions:
        print(coalition)

    print("====================fin des préparatifs====================")

    # Démarrage des serveurs
    agents = fournisseurs + acheteurs
    threads = [Thread(target=agent.start_server) for agent in agents]
    for thread in threads:
        thread.start()

    time.sleep(1)

    # Simulation des propositions
    print("====================Simulation des propositions====================")
    for fournisseur in fournisseurs:
        print(f"===================={fournisseur.name}====================")
        for coalition in coalitions:
            print(f"===================={coalition}====================")
            # On boucle d'abord sur les acheteurs de la coalition
            for acheteur in coalition.acheteurs:
                print(f"===================={acheteur.name}====================")
                # Si l'acheteur a déjà acheté quelque chose, on passe à l'acheteur suivant
                if acheteur.achete:
                    print(f"{acheteur.name} a déjà acheté un service.")
                    continue

                # Boucle sur les services proposés par ce fournisseur
                for service_id, service in list(fournisseur.services.items()):  # Utiliser list pour pouvoir modifier la dict
                    print(f"===================={service_id}====================")
                    # On propose un service si l'acheteur n'a pas encore acheté ce service
                    prix_avec_reduction = coalition.appliquer_reduction(service["prix_min"])
                    print(f"{fournisseur.name} propose {service_id} à {prix_avec_reduction} euros pour {coalition}.")

                    message = {
                        "service_id": service_id,
                        "prix": prix_avec_reduction
                    }
                    # Début de la négociation
                    reponse_acheteur = acheteur.negocier(message)

                    # Boucle de négociation
                    while reponse_acheteur["decision"] == 0:
                        reponse_fournisseur = fournisseur.repondre_negociation(reponse_acheteur)
                        if reponse_fournisseur["decision"] != 0:
                            reponse_acheteur = reponse_fournisseur
                            break
                        reponse_acheteur = acheteur.negocier(reponse_fournisseur)

                    if reponse_acheteur["decision"] == 1:
                        print(f"Accord trouvé pour le service {reponse_acheteur['service_id']} au prix de {reponse_acheteur['prix']} euros.")
                        acheteur.offres.append((reponse_acheteur, acheteur.budget - reponse_acheteur["prix"]))
                    elif reponse_acheteur["decision"] == -1:
                        print(f"La négociation a échoué pour le service {reponse_acheteur['service_id']}.")
                    # =====
    
    print("====================Offres trouvées : ====================")
    for acheteur in acheteurs:
        print(f"{acheteur.name} a reçu les offres suivantes :")
        for offre, diff in acheteur.offres:
            print(offre, diff)
            # Table pour stocker les billets achetés

    # Parcourir les offres et les traiter
    billets_achetes = []
    random.shuffle(coalitions)
    for coalition in coalitions:
        print(f"====================Traitement des offres pour {coalition}====================")
        acheteurs_sans_billet = list(coalition.acheteurs)

        for acheteur in coalition.acheteurs:
            meilleure_offre = None
            meilleure_valeur = 0

            for offre, diff in acheteur.offres:
                if offre["service_id"] in [billet["service_id"] for billet in billets_achetes]:
                    continue  # Ignorer les offres pour les services déjà achetés

                if diff > meilleure_valeur:
                    meilleure_valeur = diff
                    meilleure_offre = offre

            if meilleure_offre:
                acheteur.achete = True
                billets_achetes.append({"service_id": meilleure_offre["service_id"]})
                acheteurs_sans_billet.remove(acheteur)
                print(f"L'acheteur {acheteur.name} a acheté {meilleure_offre['service_id']} pour {meilleure_offre['prix']} euros avec une valeur de décision de {round(meilleure_valeur, 2)}.")

        if acheteurs_sans_billet:
            print(f"Les acheteurs suivants n'ont pas trouvé de billets dans la coalition {coalition}:")
            for acheteur in acheteurs_sans_billet:
                print(f"{acheteur.name}")
    
    print("====================Liste des billets achetés====================")
    for billet in billets_achetes:
        print(billet)
    print("====================Liste des billets invendus====================")
    for fournisseur in fournisseurs:
        for service_id, service in fournisseur.services.items():
            if service_id not in [billet["service_id"] for billet in billets_achetes]:
                print(f"Service {service_id} de {fournisseur.name} est invendu.")

if __name__ == "__main__":
    try:
        main()
    except exception as e:
        print(e)
        print("Une erreur est survenue lors de l'exécution du programme.")
        print("Veuillez vérifier que le fichier config.json est correctement formaté.")
        print("Chaque agents doivent avoir un nom et port différents.")
        exit(1)

