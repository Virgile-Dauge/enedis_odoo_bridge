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

2. **EnedisFluxEngine** :
   - *Responsabilité* : Interagit avec les flux de données d'Enedis pour récupérer les données contractuelles, de consommation énergétique, de facturation... 
   
   a. **Flux Transformers** :
      - *Responsabilité* : Transforme les données des flux en une matrice exploitable, et propose des méthodes spécifiques à chaque type de flux Enedis. Flux actuellement supportés : [R15, F15] Bientôt R151.
      - *Prérequis*: Les transformers utilisent les xsd fournis par Enedis pour lire les XML des flux. La confidentialité de ces flux n'étant pas claire, ils ne sont pas inclus dans la repo. (dispos dans SGE, avec le kit d'implémentation des flux)

   b. **Consumption Estimators** :
      - *Responsabilité* : Chaque estimateur implémente une heuristique permettant d'estimer la consommation à partir des données du Flux R15. Bientôt d'autres à partir du R151.
      - *pourquoi une estimation ?* : Les flux ne sont pas toujours complets ou publiés à temps.

3. **Processes** :
    L'idée des process est d'implémenter divers process métiers, qui traitent et mettent à jour des données différentes. On pourrait dire en gros que le reste c'est la lib, et ici on l'utilise en fonction de nos besoins spécifiques.
    
    a. **AddEnedisServiceToDraftInvoiceProcess** :
    - *Responsabilité* : Lit le flux F15 pour récupérer les prestations Enedis facturées et les ajouter au factures usager.ères correspondantes.

    b. **UpdateValuesInDraftInvoicesProcess** :
        - *Responsabilité* : Récupére les estimations de consommation d'EnedisFluxEngine, calcule les taxes. Récupére les factures brouillons dans Odoo, et met à jour les consommations, ainsi que les données légales de facturation comme le numéro de série du compteur.


4. **Utils** :
   - *Responsabilité* : Fournit des fonctions utilitaires pour la génération de dates et la vérification des configurations.

Installation et Configuration
-----------------------------

Installation
^^^^^^^^^^^^
a. Installer depuis le repo

b. Installer le module en utilisant pip :
Sera valable une fois un poil stabilisé, pour l'instant le package n'est pas publié. 
Pour commencer, installe simplement le module `enedis_odoo_bridge` en utilisant pip :

.. code-block:: bash

    pip install enedis-odoo-bridge

Configuration
^^^^^^^^^^^^^

Configurez le script en remplissant un fichier .env à la racine du module

.. code-block:: bash
    
    # Pour Odoo
    ENEDIS_ODOO_BRIDGE_ODOO_URL = "https://mon-site.odoo.com/"
    ENEDIS_ODOO_BRIDGE_ODOO_DB = "ma-db"
    ENEDIS_ODOO_BRIDGE_ODOO_USERNAME = "admin"
    ENEDIS_ODOO_BRIDGE_ODOO_PASSWORD = "sooooseccuuure"
    # Pour la maj des activités
    ENEDIS_ODOO_BRIDGE_ODOO_FACTURISTE_ID = 13 
    ENEDIS_ODOO_BRIDGE_ODOO_ACTIVITY_APPROUVAL_ID = 17

    # Constantes calculs des Taxes
    ENEDIS_ODOO_BRIDGE_TURPE_TAUX_HPH_CU4 = 6.67
    ENEDIS_ODOO_BRIDGE_TURPE_TAUX_HCH_CU4 = 4.56
    ENEDIS_ODOO_BRIDGE_TURPE_TAUX_HPB_CU4 = 1.43
    ENEDIS_ODOO_BRIDGE_TURPE_TAUX_HCB_CU4 = 0.88
    ENEDIS_ODOO_BRIDGE_TURPE_B_CU4 = 9.00
    ENEDIS_ODOO_BRIDGE_TURPE_CG = 15.48
    ENEDIS_ODOO_BRIDGE_TURPE_CC = 19.92

    # Connexion au FTP contenant les Flux
    ENEDIS_ODOO_BRIDGE_FTP_ADDRESS = xxx.xxx.xxx.xxx
    ENEDIS_ODOO_BRIDGE_FTP_USER = user
    ENEDIS_ODOO_BRIDGE_FTP_PASSWORD = pswwdd
    ENEDIS_ODOO_BRIDGE_FTP_R15_DIR = R15 ¿ R16
    ENEDIS_ODOO_BRIDGE_FTP_C15_DIR = C15
    ENEDIS_ODOO_BRIDGE_FTP_F15_DIR = F15
    # Déchiffrage des archives des flux
    ENEDIS_ODOO_BRIDGE_AES_IV = iv
    ENEDIS_ODOO_BRIDGE_AES_KEY = clé


Utilisation
^^^^^^^^^^^



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
