.. These are examples of badges you might want to add to your README:
   please update the URLs accordingly

    .. image:: https://api.cirrus-ci.com/github/<USER>/enedis_odoo_bridge.svg?branch=main
        :alt: Built Status
        :target: https://cirrus-ci.com/github/<USER>/enedis_odoo_bridge
    .. image:: https://readthedocs.org/projects/enedis_odoo_bridge/badge/?version=latest
        :alt: ReadTheDocs
        :target: https://enedis_odoo_bridge.readthedocs.io/en/stable/
    .. image:: https://img.shields.io/coveralls/github/<USER>/enedis_odoo_bridge/main.svg
        :alt: Coveralls
        :target: https://coveralls.io/r/<USER>/enedis_odoo_bridge
    .. image:: https://img.shields.io/pypi/v/enedis_odoo_bridge.svg
        :alt: PyPI-Server
        :target: https://pypi.org/project/enedis_odoo_bridge/
    .. image:: https://img.shields.io/conda/vn/conda-forge/enedis_odoo_bridge.svg
        :alt: Conda-Forge
        :target: https://anaconda.org/conda-forge/enedis_odoo_bridge
    .. image:: https://pepy.tech/badge/enedis_odoo_bridge/month
        :alt: Monthly Downloads
        :target: https://pepy.tech/project/enedis_odoo_bridge
    .. image:: https://img.shields.io/twitter/url/http/shields.io.svg?style=social&label=Twitter
        :alt: Twitter
        :target: https://twitter.com/enedis_odoo_bridge

.. image:: https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold
    :alt: Project generated with PyScaffold
    :target: https://pyscaffold.org/

|

=========================
Projet enedis_odoo_bridge
=========================

Le projet **enedis_odoo_bridge** vise à automatiser le traitement des flux de données d'Enedis et leur intégration dans Odoo, une suite d'applications de gestion d'entreprise open source. Ce pont entre Enedis et Odoo simplifie la gestion des données de consommation énergétique, permettant une gestion plus efficace et automatisée des factures et des analyses de consommation.

Fonctionnalités Principales
---------------------------

- **Récupération automatique des données** : Importation des données de consommation énergétique depuis Enedis. Flux R15 et F15 supportés, R151 est le prochain objectif
- **Traitement et fusion des données** : Traitement des données récupérées et fusion avec les données existantes dans Odoo.
- **Calcul des tarifs TURPE** : Application des tarifs TURPE (Tarif d'Utilisation des Réseaux Publics d'Électricité) aux données de consommation.
- **Mise à jour des factures dans Odoo** : Automatisation de la mise à jour des factures de consommation énergétique dans Odoo.

Classes et Responsabilités
--------------------------

1. **OdooAPI** :
   - *Responsabilité* : Gère la communication avec l'API d'Odoo pour récupérer et mettre à jour les données.

2. **enedis_flux_engine** :
   - *Responsabilité* : Interagit avec les flux de données d'Enedis pour récupérer les données contractuelles, de consommation énergétique, de facturation... 
   
   a. **FluxRepository** :
      - *Responsabilité* : Choisi les archives zip à lire, et propose des méthodes spécifiques à chaque type de flux Enedis. Flux actuellement supportés : [C15, R15, R151, F15].
      - *Prérequis*: Archives présentes dans le dossier de travail local

   b. **ZipRepository** :
      - *Responsabilité* : Chaque Zip repository sait comment traiter les archives zip d'un flux en particulier

   c. **services** : 
      - *Responsabilité* : Met a disposition des fonction simples de récupération des données

3. **Processes** :
    L'idée des process est d'implémenter divers process métiers, qui traitent et mettent à jour des données différentes. On pourrait dire en gros que le reste c'est la lib, et ici on l'utilise en fonction de nos besoins spécifiques.
    
    a. **AddEnedisServiceToDraftInvoiceProcess** :
    - *Responsabilité* : Lit le flux F15 pour récupérer les prestations Enedis facturées et les ajouter au factures usager.ères correspondantes.

    b. **UpdateValuesInDraftInvoicesProcess** :
        - *Responsabilité* : Récupére les estimations de consommation d'EnedisFluxEngine, calcule les taxes. Récupére les factures brouillons dans Odoo, et met à jour les consommations, ainsi que les données légales de facturation comme le numéro de série du compteur.


4. **Utils** :
   - *Responsabilité* : Fournit des fonctions utilitaires divers.

5. **Interfaces** : Fournit des interfaces marimo, l'idée étant de remplacer les processes par des notebook marimo, accessible à distance. L'avantage sera d'avoir un outil présentable, mélangeant documentation ET process, permettant de visualiser en direct les données et de réagir en fonction, sans besoin de connaissances en prog.

Installation et Configuration
-----------------------------

Installation
^^^^^^^^^^^^
a. Installer depuis le repo


Configuration
^^^^^^^^^^^^^

Configurez le script en complétant un fichier .env à la racine du module comme suit :

.. code-block:: bash
    
    # Pour Odoo
    ENEDIS_ODOO_BRIDGE_ODOO_URL = "https://mon-site.odoo.com/"
    ENEDIS_ODOO_BRIDGE_ODOO_DB = "ma-db"
    ENEDIS_ODOO_BRIDGE_ODOO_USERNAME = "admin"
    ENEDIS_ODOO_BRIDGE_ODOO_PASSWORD = "sooooseccuuure"

    # Connexion au FTP contenant les Flux
    ENEDIS_ODOO_BRIDGE_FTP_ADDRESS = xxx.xxx.xxx.xxx
    ENEDIS_ODOO_BRIDGE_FTP_USER = user
    ENEDIS_ODOO_BRIDGE_FTP_PASSWORD = pswwdd
    ENEDIS_ODOO_BRIDGE_FTP_R15_DIR = R15 ¿ R16
    ENEDIS_ODOO_BRIDGE_FTP_C15_DIR = C15
    ENEDIS_ODOO_BRIDGE_FTP_F15_DIR = F15
    ENEDIS_ODOO_BRIDGE_FTP_R151_DIR = R151
    # Déchiffrage des archives des flux
    ENEDIS_ODOO_BRIDGE_AES_IV = iv
    ENEDIS_ODOO_BRIDGE_AES_KEY = clé


Utilisation
^^^^^^^^^^^
Utilisation des interfaces
^^^^^^^^^^^^^^^^^^^^^^^^^^
   .. code-block:: bash

       marimo run src/enedis_odoo_bridge/interfaces/nom_interface.py

Utilisation des commandes
^^^^^^^^^^^^^^^^^^^^^^^^^

Le module `enedis_odoo_bridge` propose plusieurs commandes pour interagir avec les données Enedis et Odoo. Voici comment utiliser les principales commandes :

1. Commande `facturation`
   Cette commande permet de remplir les factures odoo à partir des fichiers manuels fournis.

   .. code-block:: bash

       python -m enedis_odoo_bridge.skeleton facturation -m chemin/vers/fichier.csv -d 2023-01-01

2. Commande `extract-services`
   Cette commande permet d'extraire les services à partir des fichiers F15 pour une période donnée.

   .. code-block:: bash

       python -m enedis_odoo_bridge.skeleton extract-services --start-date 2023-01-01 --end-date 2023-01-31 

3. Commande `extract-mes`
   Cette commande permet d'extraire les MES à partir des fichiers R15 pour une période donnée.

   .. code-block:: bash

       python -m enedis_odoo_bridge.skeleton extract-mes --start-date 2023-01-01 --end-date 2023-01-31 --filter "REF DEMANDEUR"

Pour chaque commande, vous pouvez ajouter l'option `-v` pour obtenir des informations de log supplémentaires ou `-vv` pour des informations de débogage détaillées.
Ces commandes peuvent s'effectuent par défault avec les données locales dans `~/data/flux_enedis`. Pour récupére les données à jour sur le sFTP, il s'uffit d'ajouter l'option `-u`.

.. code-block:: bash

    python -m enedis_odoo_bridge.skeleton <commande> -v
    python -m enedis_odoo_bridge.skeleton <commande> -vv



Documentation
-------------

Pour des informations détaillées sur l'installation, la configuration et l'utilisation du module, veuillez consulter notre `Documentation`_

.. _pyscaffold-notes:

Release on PyPI
---------------

Simply tag 

.. code-block:: bash

    git tag -a v0.1.0 -m "first release"
    
Note
----

This project has been set up using PyScaffold 4.5. For details and usage
information on PyScaffold see https://pyscaffold.org/.
