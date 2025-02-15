from flask import Flask, request, send_from_directory
from twilio.twiml.messaging_response import MessagingResponse
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import re
import uuid
from sklearn.linear_model import LinearRegression

app = Flask(__name__)
app.config['STATIC_FOLDER'] = os.path.join(os.getcwd(), 'static')

# Configuração inicial
if not os.path.exists(app.config['STATIC_FOLDER']):
    os.makedirs(app.config['STATIC_FOLDER'])

plt.switch_backend('Agg')  # Configuração para servidor

# Estrutura de dados
class FinancialData:
    def __init__(self):
        self.transactions = pd.DataFrame(columns=[
            'Data', 'Categoria', 'Descrição', 'Valor', 'Tipo', 'Conta'
        ])
        self.accounts = []
        self.budgets = {}
        self.investment_profile = None

# IA Financeira
class FinancialAgent:
    def __init__(self):
        self.model = LinearRegression()
        self.categories = {
            'alimentação': ['mercado', 'restaurante', 'comida'],
            'transporte': ['uber', 'gasolina', 'estacionamento'],
            'entretenimento': ['cinema', 'streaming', 'jogos']
        }

    def analyze_spending(self, df):
        analysis = {}
        df['Data'] = pd.to_datetime(df['Data'])
        
        # Análise mensal
        monthly = df.groupby([df['Data'].dt.month, 'Tipo'])['Valor'].sum().unstack()
        analysis['monthly_trend'] = monthly.to_dict()
        
        # Principais categorias
        expenses = df[df['Tipo'] == 'Despesa']
        analysis['top_categories'] = expenses.groupby('Categoria')['Valor'].sum().nlargest(3).to_dict()
        
        return analysis

    def generate_chart(self, df, chart_type):
        filename = f"{uuid.uuid4()}.png"
        filepath = os.path.join(app.config['STATIC_FOLDER'], filename)
        
        try:
            if chart_type == 'expenses':
                expenses = df[df['Tipo'] == 'Despesa']
                data = expenses.groupby('Categoria')['Valor'].sum()
                plt.figure(figsize=(8, 8))
                data.plot.pie(autopct='%1.1f%%')
                plt.title('Distribuição de Gastos')
            
            elif chart_type == 'monthly_trend':
                df['Mês'] = pd.to_datetime(df['Data']).dt.month
                monthly_data = df.groupby(['Mês', 'Tipo'])['Valor'].sum().unstack()
                monthly_data.plot(kind='bar')
                plt.title('Receitas vs Despesas por Mês')
            
            plt.tight_layout()
            plt.savefig(filepath)
            plt.close()
            return filename
        except Exception as e:
            print(f"Erro ao gerar gráfico: {str(e)}")
            return None

# Inicialização
data_manager = FinancialData()
financial_ai = FinancialAgent()

# Rotas
@app.route('/static/<filename>')
def serve_static(filename):
    return send_from_directory(app.config['STATIC_FOLDER'], filename)

@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.form.get("Body").strip().lower()
    response = MessagingResponse()
    
    try:
        # Comandos de gráficos
        if 'gráfico' in body:
            chart_type = 'expenses' if 'gastos' in body else 'monthly_trend'
            filename = financial_ai.generate_chart(data_manager.transactions, chart_type)
            
            if filename:
                chart_url = f"{request.url_root}static/{filename}"
                msg = response.message("📊 Gráfico gerado:")
                msg.media(chart_url)
            else:
                response.message("⚠️ Dados insuficientes para gerar o gráfico")
        
        # Comandos anteriores (transações, contas, etc.)
        elif 'nova conta' in body:
            bank = body.split('nova conta no ')[-1].strip()
            if bank not in data_manager.accounts:
                data_manager.accounts.append(bank)
                response.message(f"🏦 Conta {bank} cadastrada!")
            else:
                response.message(f"⚠️ Conta {bank} já existe")
        
        # ... (Outros comandos anteriores mantidos)
        
        else:
            response.message(process_message(body))
    
    except Exception as e:
        response.message(f"⚠️ Erro: {str(e)}")
    
    return str(response)

def process_message(message):
    # Lógica de processamento de mensagens
    if 'saldo' in message:
        return calculate_balance()
    
    elif 'relatório' in message:
        generate_report()
        return "📊 Relatório gerado em 'financas.xlsx'"
    
    # ... (Outras funções mantidas)
    
    return "🤖 Comando não reconhecido. Tente 'Ajuda'"

def calculate_balance():
    receitas = data_manager.transactions[data_manager.transactions['Tipo'] == 'Receita']['Valor'].sum()
    despesas = data_manager.transactions[data_manager.transactions['Tipo'] == 'Despesa']['Valor'].sum()
    return f"💰 Saldo Total: R${receitas - despesas:.2f}"

def generate_report():
    data_manager.transactions.to_excel("financas.xlsx", index=False)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))