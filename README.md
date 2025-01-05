# Application de Gestion des Sondages

## Description

Cette application permet la gestion et la participation à des sondages pour deux types d'utilisateurs : **Admin** et **User**. L'application offre une interface simple et intuitive pour créer, modifier, supprimer et analyser des sondages.

---

## Fonctionnalités

### Admin
- **Gestion des sondages** : 
  - Création de sondages
  - Modification de sondages
  - Suppression de sondages
  - Listage des sondages
- **Analyse des résultats** :
  - Visualisation des réponses
  - Exportation des résultats 
  - Analyse des résultats avec des graphes interactifs


### User
- **Participation aux sondages** : Participation et soumission de réponses.
- **Gestion du profil** :
  - Édition du profil
  - Suppression du compte
- **Consultation** :
  - Historique des sondages
  - Recherche des sondages par mots-clés

---

## Technologies Utilisées

- **Back-end** : Flask (framework Python)
- **Front-end** :
  - HTML/CSS : Pour la structure et le style des pages
  - JavaScript : Pour les interactions dynamiques
- **Base de données** : SQLite ou tout autre système de gestion de bases de données


---

## Installation et Lancement

### Étapes
1. **Clonez ce dépôt** :
   ```bash
   git clone https://github.com/votre-utilisateur/gestion-sondages.git
   cd gestion-sondages
   ```

2. **Installez les dépendances Python :** :
   ```bash
   pip install -r requirements.txt
   ```

3. **Lancez l'application :** :
   ```bash
   flask run
   ```

4. **Accédez à l'application dans votre navigateur :** :
   ```bash
   http://127.0.0.1:5000
   ```

---

## Connexion 

Pour accéder à l'espace administrateur, vous pouvez vous inscrire. Ou bien si vous voulez visualiser des résultats de sondage, vous pouvez vous authentifiez avec les identifiants suivants:
- **email**: administrateur@gmail.com
- **password**: admin
