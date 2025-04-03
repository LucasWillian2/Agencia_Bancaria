from flask import Flask, render_template, send_file
from io import BytesIO
import psycopg2
import os
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from datetime import datetime

load_dotenv()

app = Flask(__name__)

def get_db_connection():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        port=os.getenv('DB_PORT')
    )
    return conn

# Rota principal
@app.route('/')
def index():
    return render_template('index.html')

# Visualização de clientes por bairro
@app.route('/clientes')
def clientes_por_bairro():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
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
    """)
    
    dados = cur.fetchall()
    conn.close()
    return render_template('clientes.html', dados=dados)

# Geração do relatório PDF
@app.route('/relatorio-emprestimos')
def relatorio_emprestimos():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
    WITH totais_mensais AS (
        SELECT 
            TO_CHAR(data_empr, 'YYYY') AS ano,
            TO_CHAR(data_empr, 'MM') AS mes_numero,
            TO_CHAR(data_empr, 'Month') AS mes_nome,
            SUM(valor) AS total_emprestado,
            MAX(valor) AS maior_emprestimo
        FROM emprestimo
        GROUP BY ano, mes_numero, mes_nome
    ),
    maiores_emprestimos AS (
        SELECT 
            TO_CHAR(e.data_empr, 'YYYY') AS ano,
            TO_CHAR(e.data_empr, 'MM') AS mes,
            e.num_empr,
            c.num_conta,
            cl.nome_cliente,
            e.valor
        FROM emprestimo e
        JOIN tomador t ON e.num_empr = t.num_empr
        JOIN cliente cl ON t.nome_cliente = cl.nome_cliente
        LEFT JOIN depositante d ON t.nome_cliente = d.nome_cliente
        LEFT JOIN conta c ON d.num_conta = c.num_conta
    )
    SELECT 
        tm.ano,
        tm.mes_nome,
        tm.total_emprestado,
        me.num_empr,
        me.nome_cliente,
        me.num_conta,
        me.valor
    FROM totais_mensais tm
    LEFT JOIN maiores_emprestimos me ON 
        tm.ano = me.ano AND 
        tm.mes_numero = me.mes AND
        tm.maior_emprestimo = me.valor
    ORDER BY tm.ano, tm.mes_numero;
    """)
    
    dados = cur.fetchall()
    conn.close()

    # Criar PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    styles = getSampleStyleSheet()
    elementos = []
    
    # Cabeçalho
    elementos.append(Paragraph("Relatório de Empréstimos Mensais", styles['Title']))
    elementos.append(Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal']))
    elementos.append(Spacer(1, 24))
    
    # Tabela
    tabela_dados = [
        ['Ano', 'Mês', 'Total (R$)', 'Maior Empréstimo', 'Cliente', 'Conta']
    ]
    
    for linha in dados:
        tabela_dados.append([
            linha[0],
            linha[1].strip(),
            f"{linha[2]:,.2f}",
            f"{linha[6]:,.2f} (Nº {linha[3]})",
            linha[4],
            linha[5] if linha[5] else 'N/A'
        ])
    
    estilo = TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('BOTTOMPADDING', (0,0), (-1,0), 12),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor('#f8f9fa')),
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ])
    
    tabela = Table(tabela_dados)
    tabela.setStyle(estilo)
    elementos.append(tabela)
    
    doc.build(elementos)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f"relatorio_emprestimos_{datetime.now().strftime('%Y%m%d')}.pdf",
        mimetype='application/pdf'
    )

# Rota para mostrar o total de empréstimos
@app.route('/total-emprestimos')
def total_emprestimos():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT SUM(valor) AS total_emprestimos FROM emprestimo;")
    total = cur.fetchone()[0]
    conn.close()
    
    return render_template('total_emprestimos.html', total=total)

# Rota para mostrar clientes com conta em todas agências do Brooklyn
@app.route('/clientes-brooklyn')
def clientes_brooklyn():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
    SELECT DISTINCT d.nome_cliente
    FROM depositante d
    JOIN conta c ON d.num_conta = c.num_conta
    JOIN agencia a ON c.nome_agencia = a.nome_agencia
    WHERE a.nome_agencia = 'Agência Brooklyn' AND a.cidade_agencia = 'Nova Iorque'
    GROUP BY d.nome_cliente
    HAVING COUNT(DISTINCT c.nome_agencia) = (
        SELECT COUNT(*) 
        FROM agencia 
        WHERE nome_agencia = 'Agência Brooklyn' AND cidade_agencia = 'Nova Iorque'
    );
    """)
    
    clientes = cur.fetchall()
    conn.close()
    
    return render_template('clientes_brooklyn.html', clientes=clientes)

if __name__ == '__main__':
    app.run(debug=True)