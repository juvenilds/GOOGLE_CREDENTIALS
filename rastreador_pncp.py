import requests
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

ID_DA_PLANILHA = "17jJ6F2ZbV4xA9szQzXEa6eAWnDCj5c8JfB0akSCaeno" 
ESCOPOS = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def conectar_planilha():
    credenciais = Credentials.from_service_account_file("credenciais.json", scopes=ESCOPOS)
    cliente = gspread.authorize(credenciais)
    return cliente.open_by_key(ID_DA_PLANILHA).get_sheet1()

MUNICIPIOS_ALVO = [
    "Águas Formosas", "Ataléia", "Caraí", "Crisólita", "Frei Gaspar", 
    "Fronteira dos Vales", "Itaipé", "Malacacheta", "Nanuque", "Pavão", 
    "Pescador", "Santa Helena de Minas", "Serra dos Aimorés", "Setubinha", 
    "Umburatiba", "Carlos Chagas", "Teófilo Otoni", "Ladainha", "Novo Cruzeiro", 
    "Poté", "Bertópolis", "Campanário", "Catuji", "Franciscópolis", 
    "Itambacuri", "Machacalis", "Novo Oriente de Minas", "Ouro Verde de Minas"
]

PALAVRAS_CHAVE_OBRAS = ["pavimentacao", "reforma", "construcao", "bloquete", "calcamento", "drenagem", "infraestrutura"]

def buscar_licitacoes_pncp():
    data_hoje = datetime.now().strftime("%Y%m%d")
    url = f"https://pncp.gov.br/api/consulta/v1/contratacoes?dataPublicacao={data_hoje}&uf=MG&pagina=1"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return response.json().get("data", [])
        return []
    except Exception as e:
        print(f"Erro ao conectar na API do PNCP: {e}")
        return []

def filtrar_e_salvar():
    sheet = conectar_planilha()
    links_existentes = sheet.col_values(6) 
    publicacoes = buscar_licitacoes_pncp()
    novos_registros = 0
    
    for item in publicacoes:
        nome_orgao = item.get("orgaoEntidade", {}).get("razaoSocial", "")
        objeto = item.get("objeto", "")
        valor_estimado = item.get("valorTotalEstimado", 0.0)
        link_edital = item.get("linkSistemaOrigem", "")
        numero_processo = item.get("numeroContratacao", "")
        
        municipio_detectado = None
        for mun in MUNICIPIOS_ALVO:
            if mun.lower() in nome_orgao.lower():
                municipio_detectado = mun
                break
                
        if municipio_detectado:
            objeto_limpo = objeto.lower()
            e_obra = any(palavra in objeto_limpo for palabra in PALAVRAS_CHAVE_OBRAS)
            
            if e_obra and link_edital not in links_existentes:
                data_captura = datetime.now().strftime("%d/%m/%Y %H:%M")
                nova_linha = [
                    data_captura,
                    municipio_detectado,
                    numero_processo,
                    objeto,
                    valor_estimado,
                    link_edital,
                    False,
                    ""
                ]
                sheet.append_row(nova_linha)
                links_existentes.append(link_edital)
                novos_registros += 1
                print(f"✓ Nova obra: {municipio_detectado}")

    print(f"Processo concluído. {novos_registros} novas linhas.")

if __name__ == "__main__":
    filtrar_e_salvar()
