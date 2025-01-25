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
            print("============================")
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
        self.offres_potentielles = []  # Pour suivre les offres potentielles

    def analyser_offre(self, offre):
        """Analyse une offre reçue."""
        prix = offre["prix"]
        service_id = offre["service_id"]
        print(f"{self.name} analyse l'offre {service_id} à {prix} euros.")

        if prix <= self.budget:
            print(f"{self.name} trouve l'offre {service_id} acceptable.")
            return self.budget - prix
        else:
            print(f"{self.name} refuse l'offre car le prix dépasse le budget de {prix - self.budget}.")
        
        return self.budget - prix
    
    def start_listening(self):
        """Démarre un serveur d'écoute pour cet acheteur."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            print(f"{self.name} écoute sur {self.host}:{self.port}")
        except Exception as e:
            print(f"Erreur lors de l'initialisation de l'écoute pour {self.name} : {e}")


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
                print("============================")
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
        print("Prix initial ",prix)
        prix_reduit = round(prix * (1 - self.reduction / 100), 2)
        print(f"Prix réduit pour {self}: {prix_reduit}")
        return prix_reduit
    
    def recueillir_offres(self, fournisseurs):
        offres = []
        for fournisseur in fournisseurs:
            for service, details in fournisseur.services.items():
                prix_reduit = details['prix_min'] * (1 - self.reduction)
                offres.append({
                    "fournisseur": fournisseur.name,
                    "service": service,
                    "details": details,
                    "prix_reduit": prix_reduit
                })
        return offres
    
    def evaluer_offres(self, offres):
        def score(offre):
            details = offre['details']
            acheteurs_scores = []
            for acheteur in self.acheteurs:
                # Calcul du score basé sur les préférences
                score = 0
                if details["moyen_transport"] == acheteur.preferences["moyen_transport_pref"]["name"]:
                    score += acheteur.preferences["moyen_transport_pref"]["order"]
                if details["temps_trajet"] <= acheteur.preferences["temps_trajet_max"]["name"]:
                    score += acheteur.preferences["temps_trajet_max"]["order"]
                if details["date_limite"] <= acheteur.preferences["date_limite"]["name"]:
                    score += acheteur.preferences["date_limite"]["order"]
                # Ajouter le score si le prix est dans le budget
                if offre["prix_reduit"] <= acheteur.budget:
                    acheteurs_scores.append(score)
            # Retourner la moyenne des scores pour cette offre
            return sum(acheteurs_scores) / len(self.acheteurs) if acheteurs_scores else 0

        # Trier les offres par score décroissant
        offres_triees = sorted(offres, key=score, reverse=True)
        return offres_triees[0] if offres_triees else None  # Retourner la meilleure offre
    
    def choisir_offre(self, offre):
        if offre:
            print(f"Coalition {self} accepte l'offre {offre}.")
            # Simuler l'achat (vous pouvez notifier le fournisseur ici)
            return True
        else:
            print(f"Coalition {self} n'a trouvé aucune offre acceptable.")
            return False



