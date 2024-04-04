import zipfile
from pathlib import Path

def unzip(zip_path: str) -> Path:
    """
    Extracts the contents of the given zip file to a specified directory.

    Parameters:
    zip_path (str): The path to the zip file to be extracted.

    Returns:
    Path: The path to the directory where the contents of the zip file were extracted.

    Raises:
    FileNotFoundError: If the specified zip file does not exist.

    This function uses the built-in `zipfile` module to extract the contents of the zip file to a specified directory. It first creates the specified directory if it does not already exist. Then, it extracts the contents of the zip file to that directory.

    Example:
    ```python
    extracted_dir = unzip('/path/to/myfile.zip')
    print(extracted_dir)  # Output: '/path/to/myfile/'
    ```
    """
    if not Path(zip_path).exists():
        raise FileNotFoundError(f'File {zip_path} not found.')
    
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        out = Path(zip_path).parent.joinpath(Path(zip_path).stem)
        #print(f'creating {out} directory and extracting')
        out.mkdir(exist_ok=True)
        zip_ref.extractall(out)
        return out