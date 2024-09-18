import marimo

__generated_with = "0.8.15"
app = marimo.App(width="medium")


@app.cell
def download_trigger():
    import marimo as mo
    from pathlib import Path
    from enedis_odoo_bridge.utils import load_prefixed_dotenv

    env = load_prefixed_dotenv(prefix='ENEDIS_ODOO_BRIDGE_')
    #button = mo.ui.run_button(label="Mise à jour des flux Enedis")
    data_dir = Path("~/data/flux_axpo/").expanduser()
    mo.md(f"""
          # Téléchargement des Flux Enedis :
          **Serveur sFTP distant :** {env['RE_FTP_ADDRESS']}\n
          **Dossier local :** {data_dir}\n


          """)
    return Path, data_dir, env, load_prefixed_dotenv, mo


@app.cell(hide_code=True)
def download_util(Path, mo):
    import os
    import paramiko
    from enedis_odoo_bridge.utils import check_required
    def download_new_files(config: dict[str, str], tasks: list[str], local: Path, prefix: str="decrypted_") -> list[Path]:
        """
        Downloads specified directories from the SFTP server using paramiko, skipping files that already exist locally.
        Now includes progress tracking with rich.

        Parameters:
        config (dict[str, str]): Configuration dictionary containing SFTP details.
        tasks (list[str]): list of directory types to download (e.g., ['R15', 'C15']).
        local (Path): The local root path to save downloaded files. Defaults to '~/data/flux_enedis/'.

        Returns:
        dict[str, Path]: A dictionary mapping each task to its local path containing downloaded files.
        """
        required =  ['RE_FTP_ADDRESS', 'RE_FTP_USER', 'RE_FTP_PASSWORD',]
        config = check_required(config, required)
        completed_tasks = {}

        transport = paramiko.Transport((config['RE_FTP_ADDRESS'], 22))
        transport.connect(username=config['RE_FTP_USER'], password=config['RE_FTP_PASSWORD'])
        sftp = paramiko.SFTPClient.from_transport(transport)

        local_files = []
        for type in tasks:
            distant = type
            local_dir = local.joinpath(type).expanduser()
            if not local_dir.exists():
                local_dir.mkdir(parents=True, exist_ok=True)

            existing_files = {file.name.replace(prefix, '') if file.name.startswith(prefix) else file.name for file in local_dir.rglob('*') if file.is_file()}


            files_to_download = [f for f in sftp.listdir(distant) if f not in existing_files]
            if not files_to_download:
                print(f'{type} déjà à jour')
                continue
            for file_name in mo.status.progress_bar(files_to_download, title=f'Téléchargement du flux {type}'):
                remote_file_path = os.path.join(distant, file_name)
                local_file_path = local_dir.joinpath(file_name)
                sftp.get(remote_file_path, str(local_file_path))
                local_files.append(local_file_path)

        sftp.close()
        transport.close()

        return local_files
    return check_required, download_new_files, os, paramiko


@app.cell
def download_status(data_dir, download_new_files, env):
    from enedis_odoo_bridge.utils import recursively_decrypt_zip_files
    #mo.stop(not button.value)

    files = download_new_files(config=env, local=data_dir, tasks=['S505', 'S507', 'S518', 'S521'])
    return files, recursively_decrypt_zip_files


@app.cell(hide_code=True)
def __(mo):
    mo.md(
        r"""
        # Les acronymes utilisés :
          - **PDM** : Point de Mesure
          - **NEB** : Nouvelle Entité de Bilan
          - **RE** : Responsable d'Équilibre
          - **BGC** : Bilan Global de Consommation
          - **PRM** : Point de Référence de Mesure
          - **ACC** : Autoconsommation Collective
          - **SI** : Système d'Information
          - **CRE** : Commission de Régulation de l'Énergie
          - **CdC** : Courbe de Charge
          - **IdX** : Index
        """
    )
    return


@app.cell
def __(Path):
    import pandas as pd
    def load_csv_flux_data(flux_name: str, header_columns: list[str], data_columns: list[str], data_dir: Path) -> pd.DataFrame:
        _dataframes = []
        for _file in (data_dir / flux_name).glob("*.csv"):
            _header_df = pd.read_csv(_file, sep=';', nrows=1, names=header_columns)
            _header_values = _header_df.iloc[0].tolist()
            _df = pd.read_csv(_file, sep=';', skiprows=1, header=None)
            _df.columns = data_columns
            for i, col_name in enumerate(header_columns):
                _df[col_name] = _header_values[i]
            _dataframes.append(_df)
        if _dataframes:
            return pd.concat(_dataframes, ignore_index=True)
        return pd.DataFrame()
    return load_csv_flux_data, pd


@app.cell
def __(Path, pd):
    def load_xml_flux_data(flux_name: str, data_dir: Path) -> pd.DataFrame:
        _dataframes = []
        for _file in (data_dir / flux_name).glob("*.xml"):
            _df = pd.read_xml(_file)
            _dataframes.append(_df)
        if _dataframes:
            return pd.concat(_dataframes, ignore_index=True)
        return pd.DataFrame()
    return load_xml_flux_data,


@app.cell
def __(mo):
    mo.md(r"""# S518""")
    return


@app.cell
def __(mo):
    mo.md(
        r"""
        ## Entête du fichier

        C'est la première ligne du CSV

        | Type de champ | Nom du champ     | Définition |
        |---------------|------------------|------------|
        | Élément       | **IDFLUX**       | Identifiant du flux (« S518 ») |
        | Élément       | **NOMFLUX**      | « FU unitaires » |
        | Élément       | **EICCODE**      | Identifiant (code EIC) du destinataire (RE) du flux |
        | Élément       | **BGCSTART**     | Date de début de la période de Bilan Global de Consommation du flux |
        | Élément       | **BGCID**        | Identifiant du BGC utilisé pour le calcul des FU unitaires |
        | Élément       | **VERSION**      | Numéro de version de publication du BGC |
        | Élément       | **BGCAGE**       | Âge du BGC |
        | Élément       | **DATEGENERATION** | Date de génération du flux |
        | Élément       | **BGCAge**       | Âge de publication du BGC (sous forme S1, M1, M3, M6, M12, M14) |
        | Élément       | **BGCAgeVersion** | Numéro d’incrément de la version de l’âge du bilan publié |
        """
    )
    return


@app.cell
def __(mo):
    mo.md(r"""Le BGCAge est un concept qui représente l'âge de publication du Bilan Global de Consommation (BGC). Il indique le délai écoulé entre la période de consommation concernée et la date à laquelle le BGC a été publié. Les valeurs de BGCAge sont exprimées sous les formes suivantes : S1, M1, M3, M6, M12, M14.""")
    return


@app.cell(hide_code=True)
def __(mo):
    mo.md(
        r"""
        | Type de champ | Nom du champ   | Définition |
        |---------------|----------------|------------|
        | Attribut      | **PDM_CODE**       | Identifiant de PDM sous la forme :<br>`<EICGRD>_<SOURCENAME>[_<CENTRECODE>]_<EXTERNALID>` |
        | Attribut      | **IDENT_EXTERNE**   | N° PDC ou n° PDL ou n° PADT ou n° PRM identifiant le point de mesure dans le SI source |
        | Attribut      | **SISOURCE**        | Code du SI source auquel est rattaché le PDM (SIG, COF, CLI, DIS, FEL, GCP, SGE, COS, GIN) |
        | Attribut      | **CENTRE**          | Code centre du PDM |
        | Attribut      | **SSPROFIL**        | Code du sous-profil, obtenu en concaténant les éléments suivants :<br>- Un code profil<br>- Un séparateur (caractère « _ »)<br>- Un code de poste horo-saisonnier<br><br>**Exemple :** `ENT2_CONS_HCE` désigne un profil dont le code est « ENT2 » et le poste horo-saisonnier est « CONS_HCE ».<br>Le code profil ne comporte pas de caractère « _ ». |
        | Attribut      | **USAGEFACTOR**     | Valeur du FU pris en compte (en kW, sans arrondi). Pour les sites traités en index quotidiens Linky, valeur du FU hebdomadaire équivalent à l’ensemble des FU quotidiens appliqués sur la semaine |
        | Attribut      | **STARTTIME**       | Date de début de la mesure. Absent si Facteur d’Usage par Défaut (FUD) ou s'il s'agit d'un FU hebdomadaire sur un site traité en index quotidiens Linky |
        | Attribut      | **STOPTIME**        | Date de fin de la mesure. Absent si Facteur d’Usage par Défaut (FUD) ou s'il s'agit d'un FU hebdomadaire sur un site traité en index quotidiens Linky |
        | Attribut      | **VAL**             | Valeur du volume d’énergie (en kWh) de la consommation ayant servi à calculer le FU (en kWh). Absent si Facteur d’Usage par Défaut (FUD) ou s'il s'agit d'un FU hebdomadaire sur un site traité en index quotidiens Linky |
        | Attribut      | **FUEXTREME**       | Indication du typage extrême pour le FU de la mesure concernée lors du calcul de BGC (`Y` ou `N`). Pour les sites traités en index quotidiens Linky, `Y` si au moins une journée du FU hebdomadaire est extrême. |
        | Attribut      | **DATE_CALCUL**     | Date de calcul du Facteur d’Usage. Date max de calcul des FU quotidiens s'il s'agit d'un FU hebdomadaire sur un site traité en index quotidiens Linky |
        | Attribut      | **PS**              | Puissance souscrite du site pour ce sous-profil |
        | Attribut      | **METHODE**         | Méthode d’estimation des énergies. Pour les sites traités en index quotidiens Linky :<br>- `FUDCONS` / `FUDPROD` si le site a été traité au moins un jour en FUD sur la semaine<br>- Sinon `FUACONS` / `FUAPROD` si le site a été traité au moins un jour en FUA sur la semaine<br>- Sinon (si le site a été traité en FUC sur toute la semaine) `FUCCONS` / `FUCPROD` |
        | Attribut      | **DATEDEBUTFU**     | Date de début d’application du FU. Date min de début d'application des FU quotidiens s'il s'agit d'un FU hebdomadaire sur un site traité en index quotidiens Linky |
        | Attribut      | **DATEFINFU**       | Date de fin d’application du FU. Date max de fin d'application des FU quotidiens s'il s'agit d'un FU hebdomadaire sur un site traité en index quotidiens Linky |
        """
    )
    return


@app.cell
def __(data_dir, load_csv_flux_data):
    _header_columns = ["IDFLUX", "NOMFLUX", "EICCODE", "BGCSTART", "BGCID", "VERSION", "BGCAGE", "DATEGENERATION", "BGCAge", "BGCAgeVersion"]
    _data_columns = ["PDM_CODE", "IDENT_EXTERNE", "SISOURCE", "CENTRE", "SSPROFIL", "USAGEFACTOR", "STARTTIME", "STOPTIME", "VAL", "FUEXTREME", "DATE_CALCUL", "PS", "METHODE", "DATEDEBUTFU", "DATEFINFU"]

    # Concatenate all dataframes
    s518_df = load_csv_flux_data("S518", _header_columns, _data_columns, data_dir)

    # Display final dataframe
    s518_df
    return s518_df,


@app.cell(hide_code=True)
def __(mo):
    mo.md(
        r"""
        # S507

        ## Entête

        | Type de champ | Nom du champ                   | Définition                                                                                          |
        |---------------|--------------------------------|-----------------------------------------------------------------------------------------------------|
        | Élément       | **Titre du rapport**           | « R03 : Liste des points de mesure par RE »                                                         |
        | Élément       | **Code EIC du domaine GRD**    | Code EIC du domaine GRD (Il s’agit du code en Y)                                                    |
        | Élément       | **Code EIC RE**                | Code EIC RE (il s’agit du code en X)                                                                |
        | Élément       | **Date Début BGC**             | Samedi de début de période BGC : AAMMJJ                                                             |
        | Élément       | **Identifiant BGC**            | Identifiant du BGC utilisé pour le Rapport                                                          |
        | Élément       | **Date de génération du rapport** | Date système AAAAMMJJHHMMSS                                                                      |
        | Élément       | **BGCAge**                     | Âge de publication du BGC (sous forme S1, M1, M3, M6, M12, M14) (uniquement pour le flux S507)      |
        | Élément       | **BGCAgeVersion**              | Numéro d’incrément de la version de l’âge du bilan publié (uniquement pour le flux S507)            |
        """
    )
    return


@app.cell(hide_code=True)
def __(mo):
    mo.md(
        r"""
        ## Contenu

        | Type de champ | Nom du champ                  | Définition                                                                                                                                                                                                                                                                                                                                                                 |
        |---------------|-------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
        | Élément       | **Identifiant du Point de Mesure** | N° PDC ou n° PDL ou n° PADT ou n° PRM identifiant le point de mesure dans le SI Source, ou Identifiant de la NEB dans le cas d’une NEB RE-Site.                                                                                                                                                                                                                            |
        | Élément       | **Mode de Traitement Appliqué**     | « PROFILE » pour profilé, « TR » pour télé relevé, ou « NEB » dans le cas d’une NEB RE-Site. Cette information explicite le type d’agrégat dans lequel le site est pris en compte dans le BGC associé au flux S507 publié.                                                                                                                                                 |
        | Élément       | **Système Source**                  | Code du SI source auquel est rattaché le PDM (COF, CLI, DIS, FEL, GCP, SGE, COS, GIN) ou « STM » dans le cas d’un contrat NEB.<br><br>Le code **"COF"** est utilisé pour les points consommateurs associés aux producteurs participant à une opération d'autoconsommation collective. Ces points consommateurs se voient attribuer l'énergie produite qui est autoconsommée dans le cadre de l'opération. |
        | Élément       | **Type de Compte**                  | « CONS » pour point de mesure consommateur (soutirage) ou dans le cas d’une NEB RE-Site.<br>« PROD » pour point de mesure producteur (injection).                                                                                                                                                                                                                          |
        | Élément       | **Code commune**                    | Actuellement code INSEE sur 5 caractères numériques.<br>Champ vide dans le cas d’une NEB RE-Site.                                                                                                                                                                                                                                                                          |
        | Élément       | **Profil**                          | Code profil. Non renseigné si Télé relevé.<br>Champ vide dans le cas d’une NEB RE-Site.                                                                                                                                                                                                                                                                                    |
        | Élément       | **Date de début**                   | Début d’activité du PDM pour ce RE dans la période (généralement samedi de début de période BGC) ou date de début de la NEB dans le cas d’une NEB RE-Site.                                                                                                                                                                                                                |
        | Élément       | **Date de fin**                     | Fin d’activité du PDM pour ce RE dans la période (généralement vendredi de fin de période BGC) ou date de fin de la NEB dans le cas d’une NEB RE-Site.                                                                                                                                                                                                                    |
        | Élément       | **Message**                         | Libellé d’anomalie le cas échéant ou site concerné par la NEB dans le cas d’une NEB RE-Site.                                                                                                                                                                                                                                                                               |
        | Élément       | **Code EIC Fournisseur**            | Code EIC du titulaire du contrat (en soutirage ou injection).<br><br>**NB :** le champ sera vide pour les titulaires de contrats CARD/CAE et pour les NEB RE-site.                                                                                                                                                                                                         |
        | Élément       | **Tension**                         | Pour un point de mesure en soutirage télé relevé et en soutirage profilé.<br>Champ vide en injection, pour les NEB RE-site et en cas d’éléments manquants.                                                                                                                                                                                                                 |
        | Élément       | **Mode de Traitement Prévu**        | Pour un point de mesure en soutirage ou injection (télé relevé et profilé), ce champ fait référence au Mode de traitement attribué a priori au point selon ses caractéristiques contractuelles selon les directives de la CRE : **CdC** ou **IdX**.<br><br>Ce champ permet de repérer les sites dont le mode de traitement prévu est ‘CdC’ mais qui sont profilés dans le BGC (« PROFILE » dans le champ Mode de Traitement Appliqué). C’est le cas des sites dont aucun point de courbe n’a pu être collecté depuis sa mise en service et dont l’énergie est alors valorisée en utilisant les modalités du profilage.<br><br>Champ vide en cas d’éléments manquants. |
        | Élément       | **Calendrier Fournisseur**          | Code du calendrier fournisseur : « FP000001 » et « FC000001 ».<br>Champ vide en injection et pour les NEB RE-site.                                                                                                                                                                                                                                                        |
        | Élément       | **Puissance Souscrite**             | Valeur de la puissance souscrite en kVA pour les sites en BT et en kW pour les sites en HTA. Présent en soutirage et vide en injection et pour les NEB RE-site.                                                                                                                                                                                                           |
        | Élément       | **Type de Production**              | Libellé de la filière de production :<br>Pour un point de mesure en injection, ajout du libellé de la filière de production.<br>Champ vide en soutirage.                                                                                                                                                                                                                   |
        | Élément       | **Numéro de contrat**               | Numéro de contrat pour les contrats de type CARD-S, AUX, CSC, IMPL, CARD-I, CRAE, CSD, CSD BTSUP et CSD HTA.<br>Champ vide pour les autres types de contrat et en cas d’éléments manquants.                                                                                                                                                                                |
        | Élément       | **Participation ACC**               | Ce champ permet d’identifier les PRM participant à une opération d’ACC (Autoconsommation Collective). La valeur est alors renseignée à « ACC ».<br>Champ vide pour les PRM ne participant pas à une opération d’ACC sur la période.                                                                                                                                        |

        """
    )
    return


@app.cell(hide_code=True)
def __(mo):
    mo.md(
        r"""
        Dans notre cas, en soutirage, on ne dispose pas des 2 dernières valeures :

        | Type de champ | Nom du champ           | Définition                                                                                                                                                                                                                                                    |
        |---------------|------------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
        | Élément       | **Numéro de contrat**  | Numéro de contrat pour les contrats de type CARD-S, AUX, CSC, IMPL, CARD-I, CRAE, CSD, CSD BTSUP et CSD HTA<br>Champ vide pour les autres types de contrat et en cas d’éléments manquants.                                                                     |
        | Élément       | **Participation ACC**  | Ce champ permet d’identifier les PRM participant à une opération d’ACC (Autoconsommation Collective), La valeur est alors renseignée à « ACC ».<br>Champs vide pour les PRM ne participant pas à une opération d’ACC sur la période.                           |
        """
    )
    return


@app.cell
def __(Path, data_dir):
    def rename_txt_to_csv(directory: Path):
        for _file in directory.glob("*.txt"):
            _file.rename(_file.with_suffix(".csv"))

    rename_txt_to_csv(data_dir/"S507")
    return rename_txt_to_csv,


@app.cell(hide_code=True)
def __(data_dir, load_csv_flux_data):
    _header_columns = ["Titre du rapport",
                       "Code EIC du domaine GRD",
                       "Code EIC RE",
                       "Date Début BGC",
                       "Identifiant BGC",
                       "Date de génération du rapport",
                       "BGCAge",
                       "BGCAgeVersion"]
    _data_columns = ["Identifiant du Point de Mesure",
                     "Mode de Traitement Appliqué",
                     "Système Source",
                     "Type de Compte",
                     "Code commune",
                     "Profil",
                     "Date de début",
                     "Date de fin",
                     "Message",
                     "Code EIC Fournisseur",
                     "Tension",
                     "Mode de Traitement Prévu",
                     "Calendrier Fournisseur",
                     "Puissance Souscrite",
                     "Type de Production",]
                     # "Numéro de contrat",
                     # "Participation ACC"]
    s507_df = load_csv_flux_data("S507", _header_columns, _data_columns, data_dir)
    s507_df
    return s507_df,


@app.cell
def __(data_dir, load_xml_flux_data):
    s521_df = load_xml_flux_data('S521', data_dir)
    s521_df
    return s521_df,


if __name__ == "__main__":
    app.run()
