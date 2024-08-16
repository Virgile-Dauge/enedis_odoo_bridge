import marimo

__generated_with = "0.7.17"
app = marimo.App(width="medium")


@app.cell
def __():
    import marimo as mo

    return mo,


@app.cell
def __():
    from enedis_odoo_bridge.odoo import get_valid_subscriptions_pdl
    from enedis_odoo_bridge.utils import load_prefixed_dotenv

    env = load_prefixed_dotenv(prefix='ENEDIS_ODOO_BRIDGE_')
    get_valid_subscriptions_pdl(env)
    return env, get_valid_subscriptions_pdl, load_prefixed_dotenv


if __name__ == "__main__":
    app.run()
