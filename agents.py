import itertools
import random
import socket
import json
#on fait des coalitions d'acheteur uniquement 

from enum import Enum
import random

class AgentBase:
    def __init__(self, name, host, port):
        self.name = name  # Nom de l'agent
        self.host = host  # Adresse IP ou hostname
        self.port = port  # Port d'écoute
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def start_server(self):
        """Démarre le serveur pour écouter les messages entrants."""
        self.socket.bind((self.host, self.port))
        self.socket.listen(5)

    def send_message(self, target_host, target_port, message):
        """Envoie un message à un autre agent."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((target_host, target_port))

            # Affiche le message avant l'envoi pour vérifier la sérialisation
            print(f"Envoi du message à {target_host}:{target_port} : {message}")

            sock.sendall(json.dumps(message).encode('utf-8'))

    def receive_message(self):
        """Attend et reçoit un message entrant."""
        conn, addr = self.socket.accept()
        with conn:
            data = conn.recv(1024)
            if data:
                message = json.loads(data.decode('utf-8'))
                print(f"{self.name} a reçu un message : {message}")

                if message["type"] == "reponse" and message["decision"] > 0:
                    service_id = message["service_id"]
                    if service_id not in self.services_achetes:
                        self.services_achetes.add(service_id)
                        print(f"Service {service_id} marqué comme acheté.")
                return message


class Fournisseur(AgentBase):
    def __init__(self, name, host, port, services, strategie="accept_first"):
        super().__init__(name, host, port)
        self.services = services  # Liste des services disponibles (dictionnaire avec details)
        self.strategy = strategie
        self.services_achetes = set()  # Pour suivre les services achetés

    def proposer_service(self, acheteur_host, acheteur_port, service_id, mode):
        """Propose un service à un agent acheteur."""
        if service_id in self.services_achetes:
            print(f"Service {service_id} déjà acheté, proposition ignorée.")
            return
        
        if service_id in self.services:
            service = self.services[service_id]
            prix_initial = random.randint(service['prix_min'], service['prix_min'] + 100)

            message = {
                "type": "proposition",
                "service_id": service_id,
                "prix": prix_initial,
                "details": {
                    "service": service,
                    "fournisseur": self.name,
                    "port": self.port
                }
            }

            self.send_message(acheteur_host, acheteur_port, message)
            print(f"{self.name} a proposé le service {service_id} pour {prix_initial} euros.")
    
    def repondre_negociation(self, message):
        """Répond à une contre-offre en fonction de la stratégie."""
        prix_par_acheteur = message["prix"]
        service_id = message["service_id"]
        min_price = self.services[service_id]['prix_min']

        if self.strategy == "accept_first":
            if prix_par_acheteur >= min_price:
                print(f"{self.name} accepte immédiatement le prix proposé de {prix_par_acheteur} pour {service_id}.")
                return {"service_id": service_id, "prix": prix_par_acheteur, "decision": 1}
            else:
                print(f"{self.name} refuse l'offre car le prix est trop bas.")
                return {"service_id": service_id, "prix": prix_par_acheteur, "decision": -1}

        elif self.strategy == "randomly_accept":
            die = random.randint(1, 100)
            if die > 50:
                print(f"{self.name} accepte aléatoirement le prix proposé de {prix_par_acheteur} pour {service_id}.")
                return {"service_id": service_id, "prix": prix_par_acheteur, "decision": 1}
            else:
                nouveau_prix = round(prix_par_acheteur * 1.05, 2)  # Augmente de 5%
                print(f"{self.name} refuse et contre-propose un nouveau prix : {nouveau_prix}.")
                return {"service_id": service_id, "prix": nouveau_prix, "decision": -1}

        elif self.strategy in ["negotiate_until_satisfied", "reject_first_accept_second", "negotiate_once"]:
            if prix_par_acheteur >= min_price:
                print(f"{self.name} accepte le prix proposé de {prix_par_acheteur} pour {service_id}.")
                return {"service_id": service_id, "prix": prix_par_acheteur, "decision": 1}
            else:
                nouveau_prix = round(prix_par_acheteur * 1.05, 2)  # Augmente de 5%
                print(f"{self.name} refuse et propose un nouveau prix : {nouveau_prix}.")
                return {"service_id": service_id, "prix": nouveau_prix, "decision": 0}


class Acheteur(AgentBase):
    def __init__(self, name, host, port, budget, preferences, strategie="accept_first"):
        super().__init__(name, host, port)
        self.budget = budget
        self.strategy = strategie
        self.preferences = preferences
        self.achete=False
        self.offres = []  # Pour suivre les offres reçues
        self.previous_rejected = []  # Pour suivre les offres rejetées

    def analyser_offre(self, offre):
        """Analyse une offre reçue."""
        prix = offre["prix"]
        service_id = offre["service_id"]
        print(f"{self.name} analyse l'offre {service_id} à {prix} euros.")

        if prix <= self.budget:
            print(f"{self.name} accepte l'offre pour {service_id} pour un gain de {self.budget - prix} euros.")
        else:
            print(f"{self.name} refuse l'offre car le prix dépasse le budget de {prix - self.budget} euros.")

        return self.budget - prix
    
    def negocier(self, offre):
        """Analyse une offre reçue et applique la stratégie choisie."""
        prix = offre["prix"]
        service_id = offre["service_id"]
        print(f"{self.name} analyse l'offre {service_id} à {prix} euros.")

        if self.strategy == "accept_first":
            if prix <= self.budget:
                print(f"{self.name} accepte immédiatement l'offre pour {service_id}.")
                return {"decision": 1, "prix": prix, "service_id":service_id}  # Accepte directement
            else:
                print(f"{self.name} refuse car le prix dépasse le budget.")
                return {"decision": -1, "prix": max(0, prix * 0.9), "service_id":service_id}  # Propose un prix inférieur

        elif self.strategy == "reject_first_accept_second":
            if service_id in self.previous_rejected:
                if prix <= self.budget:
                    print(f"{self.name} accepte l'offre pour {service_id} après un rejet initial.")
                    return {"decision": 1, "prix": prix, "service_id":service_id}
            else:
                self.previous_rejected.append(service_id)
                nouveau_prix = round(prix * 0.9, 2)  # Réduction de 10%
                print(f"{self.name} rejette l'offre initiale et propose un nouveau prix : {nouveau_prix}.")
                return {"decision": 0, "prix": nouveau_prix, "service_id":service_id}

        elif self.strategy == "randomly_accept":
            die = random.randint(1, 100)
            if prix <= self.budget and die > 50:
                print(f"{self.name} accepte l'offre aléatoirement pour {service_id}.")
                return {"decision": 1, "prix": prix, "service_id":service_id}
            else:
                nouveau_prix = round(prix * 0.9, 2)
                print(f"{self.name} refuse et propose un nouveau prix : {nouveau_prix}.")
                return {"decision": 0, "prix": nouveau_prix, "service_id":service_id}

        elif self.strategy == "negotiate_until_satisfied":
            if prix <= self.budget:
                print(f"{self.name} accepte l'offre pour {service_id}.")
                return {"decision": 1, "prix": prix, "service_id":service_id}
            else:
                nouveau_prix = round(prix * 0.9, 2)
                print(f"{self.name} rejette et continue à négocier avec un prix de {nouveau_prix}.")
                return {"decision": 0, "prix": nouveau_prix, "service_id":service_id}

        elif self.strategy == "negotiate_once":
            if service_id in self.previous_rejected:
                if prix <= self.budget:
                    print(f"{self.name} accepte l'offre pour {service_id} après une seule négociation.")
                    return {"decision": 1, "prix": prix, "service_id":service_id}
            else:
                self.previous_rejected.append(service_id)
                nouveau_prix = round(prix * 0.9, 2)
                print(f"{self.name} rejette une fois et propose un nouveau prix : {nouveau_prix}.")
                return {"decision": 0, "prix": nouveau_prix, "service_id":service_id}

    def envoyer_reponse(self, fournisseur_host, fournisseur_port, offre, decision):
        """Envoie une réponse au fournisseur."""
        message = {
            "type": "reponse",
            "service_id": offre["service_id"],
            "decision": decision,
            "acheteur": self.name
        }
        self.send_message(fournisseur_host, fournisseur_port, message)

    def receive_message(self):
        """Attend et reçoit un message entrant."""
        conn, addr = self.socket.accept()
        with conn:
            data = conn.recv(1024)
            if data:
                message = json.loads(data.decode('utf-8'))
                print(f"{self.name} a reçu un message : {message}")

                if "fournisseur" not in message:
                    print("La clé 'fournisseur' est manquante dans le message.")
                    return {"decision": -1, "service_id": message["service_id"]}

                # Analyser l'offre et envoyer une réponse
                decision = self.analyser_offre(message)
                self.envoyer_reponse(message["fournisseurHost"], message["port"], message, decision)
                return {"decision": decision, "service_id": message["service_id"]}
            
    def receive_message_direct(self, message):
        """Traite un message reçu directement sans utiliser de socket."""
        print(f"{self.name} a reçu un message : {message}")

        if "fournisseur" not in message:
            print("La clé 'fournisseur' est manquante dans le message.")
            return {"decision": -1, "service_id": message["service_id"]}

        # Analyser l'offre et envoyer une réponse
        decision = self.analyser_offre(message)
        return {"decision": decision, "service_id": message["service_id"], "prix": message["prix"], "fournisseur": message["fournisseur"]}



class Coalition:
    def __init__(self, acheteurs, reduction):
        self.acheteurs = acheteurs
        self.reduction = reduction

    def __str__(self):
        acheteurs_noms = ", ".join(acheteur.name for acheteur in self.acheteurs)
        return f"Coalition ({acheteurs_noms}) avec réduction {self.reduction}%"

    def appliquer_reduction(self, prix):
        """Applique la réduction au prix donné."""
        prix_reduit = round(prix * (1 - self.reduction / 100), 2)
        print(f"Prix réduit pour {self}: {prix_reduit}")
        return prix_reduit

