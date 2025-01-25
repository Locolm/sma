import socket

# Exemple de fonction pour vérifier si un acheteur est en écoute
def is_listening(host, port):
    try:
        # Tentative de connexion au port de l'acheteur
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)  # Timeout pour la tentative de connexion
            sock.connect((host, port))
            return True
    except socket.error:
        # Si une erreur se produit, l'acheteur n'est pas en écoute
        return False

# Fonction pour configurer l'acheteur en mode écoute si nécessaire
def configure_listener(acheteur):
    if not is_listening(acheteur.host, acheteur.port):
        print(f"{acheteur.name} n'est pas en écoute sur le port {acheteur.port}. Configuration du serveur d'écoute.")
        
        # Configurer l'acheteur pour écouter sur son port
        acheteur.start_listening()  # Vous devez avoir une méthode pour démarrer le serveur
