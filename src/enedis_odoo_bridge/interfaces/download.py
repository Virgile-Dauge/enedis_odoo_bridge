import marimo

__generated_with = "0.7.5"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def download_trigger():
    import marimo as mo
    from pathlib import Path
    from enedis_odoo_bridge.utils import load_prefixed_dotenv

    env = load_prefixed_dotenv(prefix='ENEDIS_ODOO_BRIDGE_')
    button = mo.ui.run_button(label="Mise à jour des flux Enedis")
    data_path = Path("~/data/flux_enedis/").expanduser()
    mo.md(f"""
          # Téléchargement des Flux Enedis :
          **Serveur sFTP distant :** {env['FTP_ADDRESS']}\n
          **Dossier local :** {data_path}\n

          {button}
          """)
    return Path, button, data_path, env, load_prefixed_dotenv, mo


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
        required =  ['FTP_ADDRESS', 'FTP_USER', 'FTP_PASSWORD',]+[f'FTP_{k}_DIR' for k in tasks]
        config = check_required(config, required)
        completed_tasks = {}

        transport = paramiko.Transport((config['FTP_ADDRESS'], 22))
        transport.connect(username=config['FTP_USER'], password=config['FTP_PASSWORD'])
        sftp = paramiko.SFTPClient.from_transport(transport)

        local_files = []
        for type in tasks:
            distant = '/flux_enedis/' + str(config[f'FTP_{type}_DIR'])
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
def download_status(button, data_path, download_new_files, env, mo):
    from enedis_odoo_bridge.utils import recursively_decrypt_zip_files
    mo.stop(not button.value)

    files = download_new_files(config=env, local=data_path, tasks=['R15', 'F15', 'R151', 'C15'])
    decrypted_files = recursively_decrypt_zip_files(directory=data_path, 
                                                      key=bytes.fromhex(env['AES_KEY']),
                                                      iv=bytes.fromhex(env['AES_IV']),
                                                      prefix='decrypted_',
                                                      remove_encrypted=True)
    return decrypted_files, files, recursively_decrypt_zip_files


if __name__ == "__main__":
    app.run()
