import marimo

__generated_with = "0.8.4"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
async def __():
    import marimo as mo
    from extract_enedis_data import app
    # execute the notebook
    with mo.status.spinner(title="Extraction des données Enedis...") as _spinner:
      eed = await app.embed()
      _spinner.update("Extraction terminée")
    eed.output
    return app, eed, mo


@app.cell
def __():
    #eed.defs
    return


@app.cell
def __(eed):
    taxes = eed.defs['taxes']
    taxes
    return taxes,


@app.cell
def __(mo):
    coef_turpe = mo.ui.slider(start=-20, stop=20, label="Modificateur du Turpe")
    coef_prod = mo.ui.slider(start=-20, stop=20, label="Coef du prix prod")
    coef_turpe, coef_prod
    return coef_prod, coef_turpe


@app.cell
def __(mo):
    mo.md(
        r"""
        # Marge ?

        Prochaine étape, il faudrait par pdl, savoir par mois, quelle est la marge. Pour plus de détails, on va séparer entre les abonnements et les consos : 

        $m_{fix} = abonnement - turpe_{fix} + cta$ 

        $m_{var} = kwh_{base} \times tarif_{base} + - prod - turpe_{var}$

        $kwh_{base} \times tarif_{base}$
        """
    )
    return


@app.cell
def __():
    return


if __name__ == "__main__":
    app.run()
