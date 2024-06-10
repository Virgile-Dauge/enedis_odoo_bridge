# Doc 
#ERDF_R151_<destinataire>_<num_contrat>_<id_abonnement>_<num_seq>_<frequence>_<XXXXX>_<YYYYY>_<horodatage>.zip
#<emetteur>_R15_<destinataire>_<num_contrat>_<Instance_GRD>_<num_seq>_<horodatage>.zip
"""C15
17X100A100A0001A_C15_17X100AXXXXXXXXX_GRD-FXXX_0321_00710_20200416051429.zip
"""
"""F15
<emetteur>_F15_<destinataire>_<num_contrat>_<Instance_GRD>_<type_facture>_<frequencefacturation>_<type_client>_<dematerialisation>_<num_seq>_<horodatage>.zip
<type_facture>
Typologie de facture :
C : Cyclique/événementielle
R : Rectificative
I : Intérêts de retard
H : Hors PRM
Z : Autre

<frequencefacturation>
Fréquence de facturation :
B : Bimestrielle
M : Mensuelle
P : Ponctuelle
A : Annuelle
Z : Multiple (autre)

<type_client>
Typologie de client :
0 : facture pour des PRM de type professionnel
1 : facture pour des PRM de type résidentiel
9 : sans objet (dans le cas d’une facture d’intérêts de retard, hors
PRM, multiple ou autre)

<dematerialisation>
Identifie le mode d’envoi de la facture :
M : format papier
D : EDI normé
P : PDF signé déposé sur le serveur de dématérialisation
F : PDF signé envoyé sur le portail du client
Z : Autre
B : PPF B2B
G : PPF B2G

<num_seq>
Numéro de séquence du flux F15 sur 5 chiffres, de 00001 à 99999.
Ce numéro est lié au sextuplet suivant :
Fournisseur ou Acheteur (<destinataire>)
Numéro de contrat GRD-F ou GRD-A (<contrat>)
DIR (<Instance_GRD>)
Type de facture (<type_facture>)
Fréquence de facturation (<frequencefacturation>)
Type de client (<type_client>).
C’est-à-dire que, pour un fournisseur (respectivement un acheteur), un
numéro de contrat GRD-F (respectivement GRD-A), une DIR, un type de
facture et un type de client donnés, ce numéro est incrémenté de un à chaque
flux produit.
Remarque : avec la mise en place de la version 2 de Ginko et la modification
de la définition du numéro de séquence (par l’ajout de la fréquence de
facturation), toutes les séquences sont réinitialisées à 00001.

<horodatage>
Date et heure de constitution du fichier au format AAAAMMJJhhmmss.
"""