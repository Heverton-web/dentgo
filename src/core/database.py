"""
Database Core — DentGo
Padrão-Ouro Canônico: SQLite em modo WAL (alta concorrência, integridade ACID pura).
Lei Inviolável #11 do Ecossistema AIDD.
"""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

DB_PATH = Path(__file__).resolve().parent.parent.parent / "app.db"


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    target = db_path or DB_PATH
    conn = sqlite3.connect(str(target), timeout=30.0)
    conn.row_factory = sqlite3.Row
    # Ativa modo WAL e foreign keys para alta concorrencia e integridade
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA busy_timeout=5000;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_db(db_path: Optional[Path] = None) -> None:
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
            -- Marcas homologadas
            CREATE TABLE IF NOT EXISTS marcas (
                id TEXT PRIMARY KEY,
                nome TEXT NOT NULL UNIQUE,
                slug TEXT NOT NULL UNIQUE,
                ativo INTEGER DEFAULT 1,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            );

            -- Conexoes proteticas canônicas (CM, HE, HI)
            CREATE TABLE IF NOT EXISTS conexoes_proteticas (
                id TEXT PRIMARY KEY,
                tipo TEXT NOT NULL, -- CM, HE, HI
                descricao TEXT NOT NULL,
                marca_id TEXT NOT NULL REFERENCES marcas(id) ON DELETE CASCADE,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            );

            -- Produtos canônicos (Implantes e Componentes)
            CREATE TABLE IF NOT EXISTS produtos (
                id TEXT PRIMARY KEY,
                tipo TEXT NOT NULL, -- 'implante' ou 'componente'
                marca_id TEXT NOT NULL REFERENCES marcas(id) ON DELETE CASCADE,
                conexao_id TEXT NOT NULL REFERENCES conexoes_proteticas(id) ON DELETE CASCADE,
                nome TEXT NOT NULL,
                sku TEXT NOT NULL UNIQUE,
                diametro REAL,      -- ex: 3.5, 3.75, 4.0, 4.3
                comprimento REAL,   -- ex: 8.5, 10.0, 11.5, 13.0
                altura_cinta REAL,  -- ex: 1.5, 2.5, 3.5 (para munhões/pilares)
                angulacao REAL DEFAULT 0.0, -- ex: 0.0, 17.0, 30.0
                categoria TEXT NOT NULL, -- 'munhao', 'mini_pilar', 'cicatrizador', 'transferente', 'analogo', 'implante'
                imagem_url TEXT,
                ativo INTEGER DEFAULT 1,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            );

            -- Distribuidores / Lojistas autorizados
            CREATE TABLE IF NOT EXISTS distribuidores (
                id TEXT PRIMARY KEY,
                razao_social TEXT NOT NULL,
                nome_fantasia TEXT NOT NULL,
                cnpj TEXT NOT NULL UNIQUE,
                afe_anvisa TEXT NOT NULL, -- Autorizacao de Funcionamento de Empresa
                alvara_sanitario TEXT NOT NULL,
                latitude REAL NOT NULL,
                longitude REAL NOT NULL,
                endereco TEXT NOT NULL,
                whatsapp TEXT NOT NULL,
                ativo INTEGER DEFAULT 1,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            );

            -- Inventário hiperlocal (Multi-location)
            CREATE TABLE IF NOT EXISTS estoque_distribuidor (
                id TEXT PRIMARY KEY,
                distribuidor_id TEXT NOT NULL REFERENCES distribuidores(id) ON DELETE CASCADE,
                produto_id TEXT NOT NULL REFERENCES produtos(id) ON DELETE CASCADE,
                preco REAL NOT NULL,
                quantidade INTEGER NOT NULL DEFAULT 0,
                disponivel_flash INTEGER DEFAULT 1, -- Pronta entrega em 2h
                atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(distribuidor_id, produto_id)
            );

            -- Usuários / Compradores (Dentistas e Laboratórios)
            CREATE TABLE IF NOT EXISTS usuarios (
                id TEXT PRIMARY KEY,
                nome TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                cpf TEXT NOT NULL UNIQUE,
                cro_numero TEXT NOT NULL,
                cro_uf TEXT NOT NULL,
                cro_status TEXT DEFAULT 'PENDENTE', -- 'ATIVO', 'PENDENTE', 'SUSPENSO'
                tipo_usuario TEXT DEFAULT 'DENTISTA', -- 'DENTISTA', 'LABORATORIO', 'CLINICA'
                whatsapp TEXT NOT NULL,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            );

            -- Pedidos Transacionais
            CREATE TABLE IF NOT EXISTS pedidos (
                id TEXT PRIMARY KEY,
                comprador_id TEXT NOT NULL REFERENCES usuarios(id),
                distribuidor_id TEXT NOT NULL REFERENCES distribuidores(id),
                status TEXT NOT NULL DEFAULT 'CRIADO', -- CRIADO, PAGO, SEPARANDO, DESPACHADO, EM_ROTA, ENTREGUE, CANCELADO
                modalidade_entrega TEXT NOT NULL, -- 'FLASH_2H', 'CHEGA_HOJE', 'PROGRAMADO'
                taxa_produtos REAL NOT NULL,
                taxa_servico REAL NOT NULL DEFAULT 9.90,
                taxa_entrega REAL NOT NULL,
                total REAL NOT NULL,
                take_rate_distribuidor REAL NOT NULL, -- 4.5% do total de produtos
                pin_entrega TEXT NOT NULL, -- 4 digitos para entrega segura
                dest_latitude REAL NOT NULL,
                dest_longitude REAL NOT NULL,
                dest_endereco TEXT NOT NULL,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            );

            -- Itens do Pedido
            CREATE TABLE IF NOT EXISTS itens_pedido (
                id TEXT PRIMARY KEY,
                pedido_id TEXT NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
                produto_id TEXT NOT NULL REFERENCES produtos(id),
                quantidade INTEGER NOT NULL,
                preco_unitario REAL NOT NULL
            );

            -- Notícias e Radar Odonto (Jornal Vivo)
            CREATE TABLE IF NOT EXISTS radar_noticias (
                id TEXT PRIMARY KEY,
                titulo TEXT NOT NULL,
                resumo TEXT NOT NULL,
                fonte_nome TEXT NOT NULL,
                fonte_url TEXT NOT NULL,
                marca_relacionada TEXT,
                categoria TEXT NOT NULL, -- 'LANCAMENTO', 'ESTUDO', 'MERCADO', 'RECALL'
                data_publicacao TEXT NOT NULL,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            );

            -- Índices determinísticos de alta performance
            CREATE INDEX IF NOT EXISTS idx_produtos_busca ON produtos(marca_id, conexao_id, categoria, diametro);
            CREATE INDEX IF NOT EXISTS idx_estoque_busca ON estoque_distribuidor(distribuidor_id, produto_id, quantidade);
            CREATE INDEX IF NOT EXISTS idx_pedidos_status ON pedidos(status, comprador_id, distribuidor_id);
        """)
    conn.close()
