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


@app.cell(hide_code=True)
def __(data_dir):
    import pandas as pd

    _header_columns = ["IDFLUX", "NOMFLUX", "EICCODE", "BGCSTART", "BGCID", "VERSION", "BGCAGE", "DATEGENERATION", "BGCAge", "BGCAgeVersion"]
    _data_columns = ["PDM_CODE", "IDENT_EXTERNE", "SISOURCE", "CENTRE", "SSPROFIL", "USAGEFACTOR", "STARTTIME", "STOPTIME", "VAL", "FUEXTREME", "DATE_CALCUL", "PS", "METHODE", "DATEDEBUTFU", "DATEFINFU"]

    # List to store dataframes
    _dataframes = []

    # Loop through all CSV files
    for _file in (data_dir / "S518").glob("*.csv"):
        # First, read the file to extract the header row
        _header_df = pd.read_csv(_file, sep=';', nrows=1, names=_header_columns)
        _header_values = _header_df.iloc[0].tolist()
        # Now, read the data (skipping the header row)
        _df = pd.read_csv(_file, sep=';', skiprows=1, header=None)
        
        # Assign data columns to the DataFrame
        _df.columns = _data_columns
        
        # Add the header values as new columns in the DataFrame
        for i, col_name in enumerate(_header_columns):
            _df[col_name] = _header_values[i]
        
        # Append the DataFrame to the list
        _dataframes.append(_df)

    # Concatenate all dataframes
    s518_df = pd.concat(_dataframes, ignore_index=True)

    # Display final dataframe
    s518_df
    return col_name, i, pd, s518_df


if __name__ == "__main__":
    app.run()
