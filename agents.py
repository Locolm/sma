import itertools
import random
import socket
import json
#on fait des coalitions d'acheteur uniquement 

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
    def __init__(self, name, host, port, services):
        super().__init__(name, host, port)
        self.services = services  # Liste des services disponibles (dictionnaire avec details)
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


class Acheteur(AgentBase):
    def __init__(self, name, host, port, budget, preferences):
        super().__init__(name, host, port)
        self.budget = budget
        self.preferences = preferences
        self.achete=False

    def analyser_offre(self, offre):
        """Analyse une offre reçue."""
        prix = offre["prix"]
        service_id = offre["service_id"]
        print(f"{self.name} analyse l'offre {service_id} à {prix} euros.")

        if prix <= self.budget:
            print(f"{self.name} devrait accepter l'offre pour {service_id} avec un gain de {self.budget - prix}.")
        else:
            print(f"{self.name} refuse l'offre car le prix dépasse le budget de {prix - self.budget}.")
        return self.budget - prix

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

