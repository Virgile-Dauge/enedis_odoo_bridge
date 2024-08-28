import marimo

__generated_with = "0.8.0"
app = marimo.App(width="medium")


@app.cell
async def __():
    from extract_enedis_data import app
    # execute the notebook
    eed = await app.embed()
    return app, eed


@app.cell
def __(eed):
    eed.output
    return


@app.cell
def __(eed):
    eed.defs['consos']
    return


if __name__ == "__main__":
    app.run()
