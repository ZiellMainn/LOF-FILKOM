import os
import sqlite3

import click
from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    os.makedirs(os.path.dirname(current_app.config["DATABASE"]), exist_ok=True)
    db = get_db()
    schema = os.path.join(os.path.dirname(current_app.root_path), "schema.sql")
    with open(schema, encoding="utf-8") as f:
        db.executescript(f.read())
    db.commit()


@click.command("init-db")
def init_db_command():
    """Membuat tabel (data lama tetap aman)."""
    init_db()
    click.echo("Basis data siap.")


@click.command("seed")
@click.option("--reset", is_flag=True, help="Hapus basis data lama sebelum mengisi data demo.")
def seed_command(reset):
    """Mengisi data demo (akun, kategori, lokasi, contoh laporan)."""
    from .seed import isi_data_demo
    if reset and os.path.exists(current_app.config["DATABASE"]):
        os.remove(current_app.config["DATABASE"])
    init_db()
    isi_data_demo(get_db())
    click.echo("Data demo terisi. Lihat README untuk akun demo.")


def register(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_command)
