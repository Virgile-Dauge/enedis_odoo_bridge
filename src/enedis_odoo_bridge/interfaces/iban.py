import marimo

__generated_with = "0.8.4"
app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo
    return mo,


@app.cell
def __():
    return


@app.cell
def __(mo):
    mo.md(
        r"""
        https://fr.wikipedia.org/wiki/International_Bank_Account_Number

        1. Enlever les caractères indésirables (espaces, tirets),
        2. Déplacer les 4 premiers caractères à la fin du compte,
        3. Remplacer les lettres par des chiffres au moyen d'une table de conversion (A=10, B=11, C=12 etc.),
        4. Diviser le nombre ainsi obtenu par 97,
        5. Si le reste n'est pas égal à 1 l'IBAN est incorrect : modulo de 97 égal à 1.
        S'il y a trop de chiffres (plus de 30) il est possible que votre machine ne puisse pas faire un si gros calcul. Dans ce cas, prendre les n(n) premiers (disons les 10 premiers chiffres par exemple). Calculer ce nombre modulo 97 et le remplacer par le reste au début des autres chiffres. Refaire le modulo du nouveau nombre obtenu.
        """
    )
    return


@app.cell
def __():
    import re

    def verif_iban(iban: str) -> bool:
        # 1. Enlever les caractères indésirables (espaces, tirets),
        alphanum = re.sub(r'[^a-zA-Z0-9]', '', iban)

        # 2. Déplacer les 4 premiers caractères à la fin du compte,
        rearranged_iban = alphanum[4:] + alphanum[:4]

        #3. Remplacer les lettres par des chiffres au moyen d'une table de conversion (A=10, B=11, C=12 etc.),
        converted_iban = ''.join([str(ord(char) - 55) if char.isalpha() else char for char in rearranged_iban])

        # 4. Diviser le nombre ainsi obtenu par 97,
        modulo = int(converted_iban) % 97

        # 5. Si le reste est égal à 1 l'IBAN est correct :
        return modulo == 1
        
    _chaine = "GB87 BARC 2065 8244 9AS6 55"
    resultat = verif_iban(_chaine)
    resultat
    return re, resultat, verif_iban


if __name__ == "__main__":
    app.run()
