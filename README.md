# Sistema Bancário

Aplicação para gerenciamento de agências bancárias com:
- Visualização de clientes por bairro
- Relatório de empréstimos em PDF

## 📦 Estrutura do Banco de Dados

### 1. Criação das Tabelas
'''sql
-- Tabela Agência
CREATE TABLE agencia (
    nome_agencia VARCHAR(50) PRIMARY KEY,
    cidade_agencia VARCHAR(50) NOT NULL,
    ativos NUMERIC(15,2) NOT NULL
);

-- Tabela Cliente
CREATE TABLE cliente (
    nome_cliente VARCHAR(50) PRIMARY KEY,
    endereco_cliente VARCHAR(100) NOT NULL,
    cidade_cliente VARCHAR(50) NOT NULL
);

-- Tabela Empréstimo
CREATE TABLE emprestimo (
    num_empr VARCHAR(10) PRIMARY KEY,
    nome_agencia VARCHAR(50) NOT NULL REFERENCES agencia(nome_agencia),
    valor NUMERIC(15,2) NOT NULL,
    data_empr DATE NOT NULL DEFAULT CURRENT_DATE
);

-- Tabela Conta
CREATE TABLE conta (
    num_conta VARCHAR(10) PRIMARY KEY,
    nome_agencia VARCHAR(50) NOT NULL REFERENCES agencia(nome_agencia),
    saldo NUMERIC(15,2) NOT NULL
);

-- Tabela Tomador (relacionamento)
CREATE TABLE tomador (
    nome_cliente VARCHAR(50) REFERENCES cliente(nome_cliente),
    num_empr VARCHAR(10) REFERENCES emprestimo(num_empr),
    PRIMARY KEY (nome_cliente, num_empr)
);

-- Tabela Depositante (relacionamento)
CREATE TABLE depositante (
    nome_cliente VARCHAR(50) REFERENCES cliente(nome_cliente),
    num_conta VARCHAR(10) REFERENCES conta(num_conta),
    PRIMARY KEY (nome_cliente, num_conta)
);
'''
### 2.CRIAÇÃO DOS DADOS (EXEMPLO) 

'''
-- Agências
INSERT INTO agencia (nome_agencia, cidade_agencia, ativos) VALUES
('Agência Centro', 'São Paulo', 2500000.00),
('Agência Norte', 'Rio de Janeiro', 1800000.00),
('Agência Sul', 'Porto Alegre', 1200000.00);

-- Clientes
INSERT INTO cliente (nome_cliente, endereco_cliente, cidade_cliente) VALUES
('João Silva', 'Avenida Paulista, 1000, Bela Vista', 'São Paulo'),
('Maria Oliveira', 'Rua do Ouvidor, 50, Centro', 'Rio de Janeiro'),
('Carlos Pereira', 'Avenida Borges, 300, Centro', 'Porto Alegre');

-- Contas
INSERT INTO conta (num_conta, nome_agencia, saldo) VALUES
('CC001', 'Agência Centro', 12500.00),
('CC002', 'Agência Norte', 8500.50),
('CC003', 'Agência Sul', 15000.00);

-- Empréstimos
INSERT INTO emprestimo (num_empr, nome_agencia, valor, data_empr) VALUES
('EMP001', 'Agência Centro', 10000.00, '2023-01-15'),
('EMP002', 'Agência Norte', 7500.00, '2023-02-20'),
('EMP003', 'Agência Sul', 15000.00, '2023-03-10');

-- Relacionamentos
INSERT INTO depositante (nome_cliente, num_conta) VALUES
('João Silva', 'CC001'),
('Maria Oliveira', 'CC002'),
('Carlos Pereira', 'CC003');

INSERT INTO tomador (nome_cliente, num_empr) VALUES
('João Silva', 'EMP001'),
('Maria Oliveira', 'EMP002'),
('Carlos Pereira', 'EMP003');
'''

### 3.INSERÇÃO DE DADOS (EXEMPLO) 

'''
-- Agências
INSERT INTO agencia (nome_agencia, cidade_agencia, ativos) VALUES
('Agência Centro', 'São Paulo', 2500000.00),
('Agência Norte', 'Rio de Janeiro', 1800000.00),
('Agência Sul', 'Porto Alegre', 1200000.00);

-- Clientes
INSERT INTO cliente (nome_cliente, endereco_cliente, cidade_cliente) VALUES
('João Silva', 'Avenida Paulista, 1000, Bela Vista', 'São Paulo'),
('Maria Oliveira', 'Rua do Ouvidor, 50, Centro', 'Rio de Janeiro'),
('Carlos Pereira', 'Avenida Borges, 300, Centro', 'Porto Alegre');

-- Contas
INSERT INTO conta (num_conta, nome_agencia, saldo) VALUES
('CC001', 'Agência Centro', 12500.00),
('CC002', 'Agência Norte', 8500.50),
('CC003', 'Agência Sul', 15000.00);

-- Empréstimos
INSERT INTO emprestimo (num_empr, nome_agencia, valor, data_empr) VALUES
('EMP001', 'Agência Centro', 10000.00, '2023-01-15'),
('EMP002', 'Agência Norte', 7500.00, '2023-02-20'),
('EMP003', 'Agência Sul', 15000.00, '2023-03-10');

-- Relacionamentos
INSERT INTO depositante (nome_cliente, num_conta) VALUES
('João Silva', 'CC001'),
('Maria Oliveira', 'CC002'),
('Carlos Pereira', 'CC003');

INSERT INTO tomador (nome_cliente, num_empr) VALUES
('João Silva', 'EMP001'),
('Maria Oliveira', 'EMP002'),
('Carlos Pereira', 'EMP003');
'''

### 4.CONSULTAS PRINCIPAIS --

'''
WITH enderecos AS (
    SELECT 
        nome_cliente,
        cidade_cliente,
        CASE
            WHEN endereco_cliente ~ '^[^,]+,[^,]+,[^,]+$' THEN 
                TRIM(SPLIT_PART(endereco_cliente, ',', 3))
            WHEN endereco_cliente ~ '^[^,]+,[^,]+$' THEN 
                TRIM(SPLIT_PART(endereco_cliente, ',', 2))
            ELSE 'Bairro não identificado'
        END AS bairro
    FROM cliente
)
SELECT 
    cidade_cliente,
    bairro,
    COUNT(*) as total_clientes,
    STRING_AGG(nome_cliente, ', ' ORDER BY nome_cliente) as clientes
FROM enderecos
GROUP BY cidade_cliente, bairro
ORDER BY cidade_cliente, total_clientes DESC;

-- 5.RELATORIO DE EMPRESTIMOS MENSAIS --

WITH dados_mensais AS (
    SELECT 
        TO_CHAR(data_empr, 'YYYY') AS ano,
        TO_CHAR(data_empr, 'MM') AS mes_num,
        TO_CHAR(data_empr, 'Month') AS mes_nome,
        SUM(valor) AS total_emprestado,
        MAX(valor) AS maior_emprestimo
    FROM emprestimo
    GROUP BY ano, mes_num, mes_nome
),
maiores_emprestimos AS (
    SELECT 
        TO_CHAR(e.data_empr, 'YYYY') AS ano,
        TO_CHAR(e.data_empr, 'MM') AS mes,
        e.num_empr,
        c.num_conta,
        cl.nome_cliente,
        e.valor,
        a.nome_agencia
    FROM emprestimo e
    JOIN tomador t ON e.num_empr = t.num_empr
    JOIN cliente cl ON t.nome_cliente = cl.nome_cliente
    LEFT JOIN depositante d ON t.nome_cliente = d.nome_cliente
    LEFT JOIN conta c ON d.num_conta = c.num_conta
    JOIN agencia a ON e.nome_agencia = a.nome_agencia
)
SELECT 
    dm.ano,
    dm.mes_nome,
    dm.total_emprestado,
    me.num_empr,
    me.nome_cliente,
    me.num_conta,
    me.valor,
    me.nome_agencia
FROM dados_mensais dm
LEFT JOIN maiores_emprestimos me ON 
    dm.ano = me.ano AND 
    dm.mes_num = me.mes AND
    dm.maior_emprestimo = me.valor
ORDER BY dm.ano, dm.mes_num;
'''

### 🚀 COMO EXECUTAR 

'''
-- 1-CRIE O BANCO DE DADOS 

createdb agencia_bancaria

-- 2-IMPORTE A ESTRUTURA 

psql -U seu_usuario -d agencia_bancaria -f database.sql

-- 3-INSTALE AS DEPENDÊNCIAS 

pip install -r requirements.txt

-- 4-CONFIGURE O .env:

DB_HOST=localhost
DB_NAME=agencia_bancaria
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_PORT=5432

-- 5-EXECUTE A APLICAÇÃO

python app.py

-- Acesse: http://localhost:5000 --

#   A g e n c i a _ B a n c a r i a 
'''
 
 
