import marimo

__generated_with = "0.9.8"
app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo
    import pandas as pd
    import numpy as np
    import os
    import paramiko
    from datetime import date
    from pathlib import Path

    from enedis_odoo_bridge.utils import load_prefixed_dotenv
    from enedis_odoo_bridge.utils import download_decrypt_extract as _dl, check_required as _check_required

    from enedis_odoo_bridge.enedis_flux_engine import process_flux

    import logging
    logging.getLogger("paramiko.transport").setLevel(logging.ERROR)
    logger = logging.getLogger('enedis_odoo_bridge')

    def download_with_marimo_progress(
        config: dict[str, str], 
        tasks: list[str], 
        local: Path,
        force: bool = False
    ) -> list[tuple[str, str]]:
        """
        Downloads, decrypts, and extracts new files from the SFTP server, skipping files that have already been processed.
        Uses a Marimo progress bar for progress tracking.

        Parameters:
        config (dict[str, str]): Configuration dictionary containing SFTP details, key, and IV.
        tasks (list[str]): List of directory types to process (e.g., ['R15', 'C15']).
        local (Path): The local root path to save extracted files.
        force (bool): If True, reprocess all files, even if they've been processed before.

        Returns:
        list[tuple[str, str]]: A list of tuples containing (zip_name, task_type) of newly processed files.
        """
        required = ['FTP_ADDRESS', 'FTP_USER', 'FTP_PASSWORD', 'AES_KEY', 'AES_IV'] + [f'FTP_{k}_DIR' for k in tasks]
        config = _check_required(config, required)

        key = bytes.fromhex(config['AES_KEY'])
        iv = bytes.fromhex(config['AES_IV'])

        csv_path = local / "processed_zips.csv"
        if force and csv_path.exists():
            csv_path.unlink()
        
        if csv_path.exists():
            df = pd.read_csv(csv_path)
            processed_zips = set(df['zip_name'])
        else:
            df = pd.DataFrame(columns=['zip_name', 'flux'])
            processed_zips = set()

        transport = paramiko.Transport((config['FTP_ADDRESS'], 22))
        transport.connect(username=config['FTP_USER'], password=config['FTP_PASSWORD'])
        sftp = paramiko.SFTPClient.from_transport(transport)

        newly_processed_files = []

        try:
            current_overall = 0
            for task_type in tasks:
                distant = '/flux_enedis/' + str(config[f'FTP_{task_type}_DIR'])
                local_dir = local.joinpath(task_type)
                local_dir.mkdir(parents=True, exist_ok=True)

                files_to_process = [f for f in sftp.listdir(distant) if f not in processed_zips]
                with mo.status.progress_bar(total=len(files_to_process),remove_on_exit=True) as bar:
                    for file_name in files_to_process:
                        bar.update(
                            title=f"Processing {task_type}:",
                            subtitle=file_name)

                        remote_file_path = os.path.join(distant, file_name)
                        output_path = local_dir / file_name.replace('.zip', '')
                        
                        success = _dl(sftp, remote_file_path, output_path, key, iv)
                        
                        if success:
                            newly_processed_files.append((file_name, task_type))
                            df = pd.concat([df, pd.DataFrame({'zip_name': [file_name], 'flux': [task_type]})], ignore_index=True)
                        
                        current_overall += 1

        except Exception as e:
            logger.error(f"Failed to process files from {distant}: {e}")

        finally:
            sftp.close()
            transport.close()

        df.to_csv(csv_path, index=False)

        return newly_processed_files

    env = load_prefixed_dotenv(prefix='ENEDIS_ODOO_BRIDGE_')
    flux_path = Path('~/data/flux_enedis_v2/').expanduser()
    flux_path.mkdir(parents=True, exist_ok=True)
    return (
        Path,
        date,
        download_with_marimo_progress,
        env,
        flux_path,
        load_prefixed_dotenv,
        logger,
        logging,
        mo,
        np,
        os,
        paramiko,
        pd,
        process_flux,
    )


@app.cell
def __(download_with_marimo_progress, env, flux_path, mo):
    mo.md("# Downloading and processing files")

    _processed = download_with_marimo_progress(env, ['R15', 'C15', 'F15', 'F12'], flux_path)

    mo.md(f"Processed #{len(_processed)} files.")
    return


@app.cell
def __(flux_path, process_flux):
    f15 = process_flux('F15', flux_path / 'F15')
    f15
    return (f15,)


@app.cell
def __(flux_path, process_flux):
    f12 = process_flux('F12', flux_path / 'F12')
    f12
    return (f12,)


@app.cell
def __(flux_path, process_flux):
    R15 = process_flux('R15', flux_path / 'R15')
    R15
    return (R15,)


@app.cell
def __(flux_path, process_flux):
    C15 = process_flux('C15', flux_path / 'C15')
    C15
    return (C15,)


if __name__ == "__main__":
    app.run()
