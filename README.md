# PROJET: Simulation de négociation et formation de coalitions pour l'achat de billets

*BONADA Nathan - CONSTANT Céline - LAURENT Clément*

*5A Polytech dans le cadre du module sma*

Ce projet simule un système multi-agents où des acheteurs et des fournisseurs interagissent pour négocier l'achat de billets en formant des coalitions. L'objectif est de maximiser le gain collectif des acheteurs tout en respectant leurs préférences et budgets.

## Exécution

Modifiez le fichier config.json pour définir les fournisseurs, acheteurs et leurs paramètres.

Assurez vous de ne pas avoir de doublon pour les ports et noms des agents

### Structure du config.json
- *mode* défini le mode de négociation utilisé par défaut en normal.
- *coalition_unique* est un booléen qui défini si l'on forme des coalitions unique ou non (c'est à dire si l'on forme des coalitions ou pas).
- *fournisseurs* est un tableau contenant la liste des fournisseurs disponible :
    - *name* un nom unique pour identification
    - *host* par défaut 127.0.0.1
    - *port* un port unique pour la communication par socket.
    - *services* dictionnaire avec les noms uniques des *billets*.
        - les *billets* contiennent prix_min, date_limite, moyen_transport, temps_trajet.
- *acheteurs* est un tableau contenant la liste des acheteurs disponible:
    - *name* un nom unique pour identification
    - *host* par défaut 127.0.0.1
    - *port* un port unique pour la communication par socket.
    - *budget* le budget maximum que l'acheteur peut se permettre.
    - *preferences* l'ensemble des préférences de l'acheteurs: moyen_transport_pref, date_limite, temps_trajet_max avec un ordre de préférence associé.


Exécutez le script principal. **main.py** Les étapes suivantes se dérouleront :
- Formation des coalitions.
- Démarrage des serveurs pour chaque agent.
- Processus de négociation entre les coalitions et les fournisseurs.

## Fonctionnalités principales

### Formation de coalitions :

Les acheteurs se regroupent en coalitions basées sur :
- Une valeur aléatoire influencée par la similitude de leurs préférences (mode de transport, date limite, etc.).
- Leurs budgets respectifs.
- Les grosses coalitions sont favorisées.

### Négociation des prix
- Si un acheteur ne peut pas se permettre un billet au prix initial, une négociation est déclenchée.
- Les fournisseurs proposent un prix réduit en fonction de leur politique commerciale et des demandes des acheteurs.

### Optimisation du gain collectif :
- Les fournisseurs offrent des billets aux acheteurs.
- Les acheteurs analysent les propositions selon leurs préférences et budgets.
- Une liste d'offres acceptable est ensuite créée par acheteurs
- Les coalitions tentent de créer les meilleur combinaisons acheteurs billets, c'est à dire les combinaison avec le plus gros gain.

## Structure du code
Décrit les fournisseurs, acheteurs, services disponibles (billets), et les préférences des agents.

### Agents :

- **Fournisseurs** : Proposent des billets avec des caractéristiques spécifiques (prix, date limite, moyen de transport).
- **Acheteurs** : Décident d'accepter ou non les offres en fonction de leurs budgets et préférences.
- **Coalitions** : Groupes d'acheteurs qui combinent leurs ressources pour augmenter leur pouvoir d'achat.

### Mécanisme de communication :

Les agents communiquent via des sockets pour envoyer et recevoir des messages.