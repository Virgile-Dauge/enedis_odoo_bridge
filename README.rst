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

==================
enedis_odoo_bridge
==================


    Automate enedis flux parsing, then inject data into odoo


Need to create .env file :

Bienvenue dans la Documentation du Pont Enedis Odoo
==================================================

Introduction
------------

Le Pont Enedis Odoo est un module Python permettant l'intégration des données d'Enedis dans Odoo, un système ERP open-source.

Fonctionnalités Principales
---------------------------

- **Récupére les Flux Enedis depuis un Sftp** :
- **TODO Déchiffre les zip** :
- **Extrait les zip en xml** :
- **Parse les XML des Flux** : R15, plus à venir
- **Récupére Depuis Odoo les Factures brouillon** :
- **Édite les lignes de factures avec les consos** :

Pour Commencer
--------------

Installation
^^^^^^^^^^^^

Pour commencer, installez simplement le module `enedis_odoo_bridge` en utilisant pip :

.. code-block:: bash

    pip install enedis_odoo_bridge

Configuration
^^^^^^^^^^^^^

Configurez le script en remplissant un fichier .env à la racine du module

.. code-block:: bash

    URL = "https://truc.odoo.com/"
    DB = "truc"
    USERNAME = "truc@truc.com"
    PASSWORD = "truc"
    TURPE_TAUX_HPH_CU4 = 6.67
    TURPE_TAUX_HCH_CU4 = 4.56
    TURPE_TAUX_HPB_CU4 = 1.43
    TURPE_TAUX_HCB_CU4 = 0.88   
    TURPE_B_CU4 = 9.00
    TURPE_CG = 15.48
    TURPE_CC = 19.92
    FTP_ADDRESS = xxx.xxx.xxx.xxx
    FTP_USER = truc
    FTP_PASSWORD = truc
    FTP_R15 = R15 ¿ R16
    FTP_C15 = C15
    FTP_F15 = F15
    ENEDIS_CIPHER = truc

Utilisation
^^^^^^^^^^^



Documentation
-------------

Pour des informations détaillées sur l'installation, la configuration et l'utilisation du module, veuillez consulter notre `Documentation`_

.. _pyscaffold-notes:

Note
====

This project has been set up using PyScaffold 4.5. For details and usage
information on PyScaffold see https://pyscaffold.org/.
