"""
Testes E2E e Unitários de Toda a Suíte de Domínio — DentGo
TDD Red-Green: Cobertura Completa das Leis do Ecossistema.
"""

import pytest
from pathlib import Path
from src.core.database import init_db, get_connection
from src.modules.autenticacao_cro.service import cadastrar_comprador, verificar_habilitacao_cirurgica
from src.modules.checkout_split.service import criar_pedido, obter_pedido
from src.modules.telemetria_logistica.service import obter_telemetria_entrega, confirmar_entrega_com_pin
from src.modules.radar_noticias.service import seed_noticias_iniciais, listar_radar_noticias


@pytest.fixture
def db_suite_completa(tmp_path: Path):
    db_file = tmp_path / "dentgo_suite.db"
    init_db(db_file)

    conn = get_connection(db_file)
    with conn:
        conn.execute("INSERT INTO marcas (id, nome, slug) VALUES ('cx', 'Conexão', 'conexao')")
        conn.execute("INSERT INTO conexoes_proteticas (id, tipo, descricao, marca_id) VALUES ('c1', 'CM', 'Cone Morse', 'cx')")
        conn.execute("""
            INSERT INTO produtos (id, tipo, marca_id, conexao_id, nome, sku, diametro, categoria)
            VALUES ('prod-10', 'implante', 'cx', 'c1', 'Implante Flash CM 3.5', 'SKU-10', 3.5, 'implante')
        """)
        conn.execute("""
            INSERT INTO distribuidores (id, razao_social, nome_fantasia, cnpj, afe_anvisa, alvara_sanitario, latitude, longitude, endereco, whatsapp)
            VALUES ('dist-1', 'Dental SP', 'Dental SP', '12.345.678/0001-90', 'AFE-999', 'ALV-999', -23.5505, -46.6333, 'Centro SP', '11988887777')
        """)
        conn.execute("""
            INSERT INTO estoque_distribuidor (id, distribuidor_id, produto_id, preco, quantidade, disponivel_flash)
            VALUES ('est-10', 'dist-1', 'prod-10', 200.00, 10, 1)
        """)
    conn.close()
    return db_file


def test_fluxo_autenticacao_e_trava_cro(db_suite_completa: Path, monkeypatch):
    monkeypatch.setattr("src.modules.autenticacao_cro.service.get_connection", lambda: get_connection(db_suite_completa))

    # Cadastro de dentista valido
    user = cadastrar_comprador(
        nome="Dr. Lucas Cirurgiao",
        email="lucas@clinica.com",
        cpf="123.456.789-00",
        cro_numero="123456",
        cro_uf="SP",
        whatsapp="11977776666",
    )
    assert user["cro_status"] == "ATIVO"
    assert verificar_habilitacao_cirurgica(user["id"]) is True

    # Rejeita CRO com UF invalida
    with pytest.raises(ValueError):
        cadastrar_comprador(
            nome="Falso",
            email="falso@email.com",
            cpf="111.222.333-44",
            cro_numero="999",
            cro_uf="XX",
            whatsapp="11900000000",
        )


def test_fluxo_checkout_split_e_telemetria(db_suite_completa: Path, monkeypatch):
    monkeypatch.setattr("src.modules.autenticacao_cro.service.get_connection", lambda: get_connection(db_suite_completa))
    monkeypatch.setattr("src.modules.checkout_split.service.get_connection", lambda: get_connection(db_suite_completa))
    monkeypatch.setattr("src.modules.telemetria_logistica.service.get_connection", lambda: get_connection(db_suite_completa))

    # 1. Cria comprador habilitado
    user = cadastrar_comprador(
        nome="Dra. Roberta Santos",
        email="roberta@odonto.com",
        cpf="987.654.321-11",
        cro_numero="98765",
        cro_uf="SP",
        whatsapp="11966665555",
    )

    # 2. Executa checkout de 2 implantes
    resultado = criar_pedido(
        comprador_id=user["id"],
        distribuidor_id="dist-1",
        itens=[{"produto_id": "prod-10", "quantidade": 2}],
        modalidade_entrega="FLASH_2H",
        dest_latitude=-23.5615,
        dest_longitude=-46.6560,
        dest_endereco="Av Paulista, 1000",
        taxa_entrega=15.00,
    )

    assert resultado["status"] == "PAGO"
    ped_id = resultado["pedido_id"]
    fin = resultado["financeiro"]

    # Validacao do Split: 2 x R$ 200 = R$ 400.00
    assert fin["total_produtos"] == 400.00
    assert fin["taxa_servico"] == 9.90
    assert fin["taxa_entrega"] == 15.00
    assert fin["total_geral"] == 424.90
    # 4.5% de R$ 400.00 = R$ 18.00
    assert fin["comissao_dentgo"] == 18.00
    assert fin["repasse_distribuidor"] == 382.00

    # 3. Telemetria de Entrega ao Vivo
    telemetria = obter_telemetria_entrega(ped_id)
    assert telemetria["status"] == "PAGO"
    assert telemetria["distancia_restante_km"] > 0
    assert telemetria["eta_minutos"] > 0

    # 4. Validacao do PIN de Entrega
    pin_correto = resultado["pin_entrega"]
    assert confirmar_entrega_com_pin(ped_id, "0000") is False
    assert confirmar_entrega_com_pin(ped_id, pin_correto) is True

    # Verifica status atualizado para ENTREGUE
    pedido_final = obter_pedido(ped_id)
    assert pedido_final["status"] == "ENTREGUE"


def test_radar_noticias_jornal_vivo(db_suite_completa: Path, monkeypatch):
    monkeypatch.setattr("src.modules.radar_noticias.service.get_connection", lambda: get_connection(db_suite_completa))

    seed_noticias_iniciais()
    noticias = listar_radar_noticias()
    assert len(noticias) >= 3

    # Testa busca com filtro por marca
    conexao_news = listar_radar_noticias(marca="conexao")
    assert len(conexao_news) == 1
    assert "In-Lego" in conexao_news[0]["titulo"]
    assert conexao_news[0]["fonte_url"] == "https://dentalpress.com.br/noticias/conexao-in-lego"
