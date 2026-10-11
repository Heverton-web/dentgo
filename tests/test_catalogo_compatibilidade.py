"""
Testes Unitários & BDD do Catálogo e Compatibilidade — DentGo
TDD Estrito: Red-Green-Refactor sob o Ecossistema AIDD.
"""

import sqlite3
import pytest
from pathlib import Path
from src.core.database import init_db, get_connection
from src.modules.catalogo_compatibilidade.service import (
    seed_marcas_canonicas,
    listar_marcas,
    buscar_produtos_cirurgicos,
    buscar_distribuidores_proximos_com_estoque,
    calcular_distancia_haversine,
)


@pytest.fixture
def db_teste(tmp_path: Path):
    db_file = tmp_path / "teste_dentgo.db"
    init_db(db_file)

    # Injeta fixtures cirurgicas reais
    conn = get_connection(db_file)
    with conn:
        # Marcas
        conn.execute("INSERT INTO marcas (id, nome, slug) VALUES ('conexao', 'Conexão Implantes', 'conexao')")
        conn.execute("INSERT INTO marcas (id, nome, slug) VALUES ('straumann', 'Straumann', 'straumann')")
        
        # Conexões
        conn.execute("INSERT INTO conexoes_proteticas (id, tipo, descricao, marca_id) VALUES ('c1', 'CM', 'Cone Morse Universal', 'conexao')")
        conn.execute("INSERT INTO conexoes_proteticas (id, tipo, descricao, marca_id) VALUES ('c2', 'HE', 'Hexágono Externo Standard', 'conexao')")

        # Produtos
        conn.execute("""
            INSERT INTO produtos (id, tipo, marca_id, conexao_id, nome, sku, diametro, comprimento, categoria)
            VALUES ('prod-1', 'implante', 'conexao', 'c1', 'Implante Flash CM 3.5x10', 'CX-FL-3510', 3.5, 10.0, 'implante')
        """)
        conn.execute("""
            INSERT INTO produtos (id, tipo, marca_id, conexao_id, nome, sku, diametro, altura_cinta, angulacao, categoria)
            VALUES ('prod-2', 'componente', 'conexao', 'c1', 'Munhão Angulado 17° CM 3.5 Cinta 2.5mm', 'CX-MN-17-3525', 3.5, 2.5, 17.0, 'munhao')
        """)

        # Distribuidores em SP (Dist 1: Pinheiros, Dist 2: Campinas)
        conn.execute("""
            INSERT INTO distribuidores (id, razao_social, nome_fantasia, cnpj, afe_anvisa, alvara_sanitario, latitude, longitude, endereco, whatsapp)
            VALUES ('dist-sp', 'Dental Pinheiros LTDA', 'Dental Pinheiros SP', '11.222.333/0001-44', 'AFE-889900', 'ALV-123', -23.5614, -46.6924, 'Rua dos Pinheiros 100', '11999990000')
        """)
        conn.execute("""
            INSERT INTO distribuidores (id, razao_social, nome_fantasia, cnpj, afe_anvisa, alvara_sanitario, latitude, longitude, endereco, whatsapp)
            VALUES ('dist-campinas', 'Dental Campinas LTDA', 'Dental Campinas', '44.555.666/0001-77', 'AFE-112233', 'ALV-456', -22.9099, -47.0626, 'Av Brasil 500', '19999990000')
        """)

        # Estoque
        conn.execute("""
            INSERT INTO estoque_distribuidor (id, distribuidor_id, produto_id, preco, quantidade, disponivel_flash)
            VALUES ('est-1', 'dist-sp', 'prod-1', 185.00, 15, 1)
        """)
        conn.execute("""
            INSERT INTO estoque_distribuidor (id, distribuidor_id, produto_id, preco, quantidade, disponivel_flash)
            VALUES ('est-2', 'dist-sp', 'prod-2', 92.50, 8, 1)
        """)
        conn.execute("""
            INSERT INTO estoque_distribuidor (id, distribuidor_id, produto_id, preco, quantidade, disponivel_flash)
            VALUES ('est-3', 'dist-campinas', 'prod-1', 180.00, 50, 0)
        """)

    conn.close()
    return db_file


def test_seed_marcas_canonicas(tmp_path: Path, monkeypatch):
    db_file = tmp_path / "teste_seed.db"
    init_db(db_file)
    monkeypatch.setattr("src.modules.catalogo_compatibilidade.service.get_connection", lambda: get_connection(db_file))

    seed_marcas_canonicas()
    marcas = listar_marcas()
    assert len(marcas) == 10
    slugs = [m["slug"] for m in marcas]
    assert "conexao-implantes" in slugs
    assert "straumann" in slugs
    assert "titanium-fix" in slugs


def test_busca_cirurgica_por_conexao_e_diametro(db_teste: Path, monkeypatch):
    monkeypatch.setattr("src.modules.catalogo_compatibilidade.service.get_connection", lambda: get_connection(db_teste))

    # Busca exclusivamente Cone Morse (CM) com diametro 3.5
    produtos = buscar_produtos_cirurgicos(tipo_conexao="CM", diametro=3.5)
    assert len(produtos) == 2

    # Filtra apenas munhão angulado 17°
    munhoes = buscar_produtos_cirurgicos(tipo_conexao="CM", categoria="munhao", angulacao=17.0)
    assert len(munhoes) == 1
    assert munhoes[0]["sku"] == "CX-MN-17-3525"
    assert munhoes[0]["menor_preco"] == 92.50


def test_busca_geografica_proximidade_last_mile(db_teste: Path, monkeypatch):
    monkeypatch.setattr("src.modules.catalogo_compatibilidade.service.get_connection", lambda: get_connection(db_teste))

    # Cirurgiao opera na Av Paulista (-23.5615, -46.6560)
    paulista_lat = -23.5615
    paulista_lon = -46.6560

    # Busca distribuidores num raio de 10 km (deve achar Pinheiros, mas descartar Campinas)
    proximos = buscar_distribuidores_proximos_com_estoque(
        produto_id="prod-1",
        cliente_lat=paulista_lat,
        cliente_lon=paulista_lon,
        raio_km=10.0,
    )

    assert len(proximos) == 1
    assert proximos[0]["id"] == "dist-sp"
    assert proximos[0]["distancia_km"] < 5.0
    assert proximos[0]["disponivel_flash"] == 1
    assert proximos[0]["eta_minutos"] <= 40
