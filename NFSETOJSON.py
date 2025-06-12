from flask import Flask, request, Response
import fitz  
import base64
import requests
import json
from typing import Optional, Dict, Any
 
JSON_TEMPLATE = {
    "sucesso": True,
    "mensagem": "",
    "dados": {
        "nota": {
            "tomador": {
                "documento": "", "im": "", "ie": "", "nome": "", "logradouro": "",
                "numero": "", "bairro": "", "complemento": "", "cidade": "",
                "uf": "", "cep": "", "pais": "", "telefone": "", "email": "", "cidadeCodigo": ""
            },
            "prestador": {
                "documento": "", "im": "", "ie": "", "nome": "", "logradouro": "",
                "numero": "", "bairro": "", "complemento": "", "cidade": "",
                "uf": "", "cep": "", "pais": "", "telefone": "", "email": "", "cidadeCodigo": ""
            },
            "tipo": "inbox",
            "origem": "download",
            "numero": "", "chave": "", "emissaoData": "", "numeroRps": "", "serie": "",
            "municipioCodigo": "", "servicoCodigo": "", "descricaoServico": "",
            "descricao": "", "servicoValor": "", "issAliquota": "", "issValor": "",
            "pisRetido": "", "cofinsRetido": "", "inssRetido": "", "irfRetido": "",
            "csllRetido": "", "deducaoValor": "", "totalValor": ""
        },
        "arquivo": {
            "nome": "",
            "tipo": "pdf"
        }
    }
}
 
app = Flask(__name__)
LLAMA_API_URL = "http://dns.auditto.com.br:11434/api/generate"
 
def manter_ordem_json(template: Dict, dados: Dict) -> Dict:
    resultado = {}
    for key in template:
        if key in dados:
            if isinstance(template[key], dict):
                resultado[key] = manter_ordem_json(template[key], dados.get(key, {}))
            else:
                resultado[key] = dados[key]
        else:
            resultado[key] = template[key]
    return resultado
 
def processar_nfse(texto_pdf: str) -> Optional[str]:
    prompt = f"""
RETORNE APENAS O JSON, sem nenhum texto adicional.
Use esta estrutura exata, preenchendo os campos com os dados do texto:

{json.dumps(JSON_TEMPLATE, indent=4, ensure_ascii=False)}

REGRAS:
1. Mantenha a estrutura exata do JSON
2. Preencha os campos com os dados encontrados no texto. NÃO confunda os dados do TOMADOR com os do PRESTADOR. Eles são entidades **distintas**.
3. Os dados do PRESTADOR e do TOMADOR devem ser extraídos separadamente. NÃO copie os dados de um para o outro.
4. Mantenha campos vazios ("") se não encontrar a informação
5. Para endereço separe corretamente:
   - logradouro: apenas o nome da rua/avenida
   - numero: traga apenas o numero do endereço
   - complemento: sala, andar, casa, apartamento, bloco
   - bairro: apenas o nome do bairro
   - cidade: apenas o nome da cidade
6. No campo `servicoCodigo` use apenas o código do serviço sem a descrição
7. No campo `descricaoServico` use apenas a descrição sem o código
8. No campo `descricao` use a descrição completa da nota
9. Se algum campo estiver como não informado substitua por ""
10. No campo `emissaoData` use apenas a data, sem hora
11. NÃO INCLUA NENHUM TEXTO ANTES OU DEPOIS DO JSON


TEXTO DA NFSe:
\"\"\"{texto_pdf}\"\"\"
"""
    try:
        print("\n=== Enviando requisição para API LLaMA ===")
        response = requests.post(
            LLAMA_API_URL,
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False,
                "format": "json"  
            },
            timeout=30
        )
        response.raise_for_status()
        
        resposta = response.json().get("response", "").strip()
        print("\n=== Resposta bruta da API LLaMA ===")
        print(resposta)
        
        return resposta
        
    except requests.exceptions.Timeout:
        print("Timeout ao conectar com a API LLaMA")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Erro na requisição LLaMA: {e}")
        return None
    except Exception as e:
        print(f"Erro inesperado ao processar resposta LLaMA: {e}")
        return None
 
def extrair_json_valido(resposta: str) -> Dict[str, Any]:
    try:
        resposta = resposta.strip()
        
        inicio_json = resposta.find('{"sucesso":')
        if inicio_json == -1:
            inicio_json = resposta.find('{')
        
        fim_json = resposta.rfind('}') + 1
        
        if inicio_json != -1 and fim_json > inicio_json:
            json_str = resposta[inicio_json:fim_json]
            print("\n=== JSON encontrado na resposta ===")
            print(json_str)
            
            try:
                dados_json = json.loads(json_str)
                resultado = json.loads(json.dumps(JSON_TEMPLATE))
                
                def mesclar_dicts(template: Dict, dados: Dict) -> Dict:
                    for key, value in dados.items():
                        if key in template:
                            if isinstance(value, dict) and isinstance(template[key], dict):
                                template[key] = mesclar_dicts(template[key], value)
                            elif value:  
                                template[key] = value
                    return template
                
                resultado = mesclar_dicts(resultado, dados_json)
                
                print("\n=== JSON após mesclagem ===")
                print(json.dumps(resultado, indent=2))
                
                return resultado
            except json.JSONDecodeError as e:
                print(f"Erro ao decodificar JSON: {e}")
                print("JSON problemático:", json_str)
                return dict(JSON_TEMPLATE)
        
        print("Não foi possível encontrar JSON válido na resposta")
        return dict(JSON_TEMPLATE)
    except Exception as e:
        print(f"Erro inesperado ao processar JSON: {e}")
        return dict(JSON_TEMPLATE)
 
def criar_json_erro(mensagem: str) -> Dict[str, Any]:
    erro = dict(JSON_TEMPLATE)
    erro["sucesso"] = False
    erro["mensagem"] = mensagem
    return erro
 
@app.route('/generate', methods=['POST'])
def generate():
    if 'file' not in request.files:
        return Response(
            json.dumps(criar_json_erro('Arquivo PDF não enviado'), indent=2),
            mimetype='application/json'
        ), 400

    pdf_file = request.files['file']
    export_base64 = request.form.get('export_base64', 'false').lower() == 'true'

    try:
        pdf_bytes = pdf_file.read()

        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8') if export_base64 else ""
        
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        texto_extraido = " ".join(page.get_text() for page in doc)
        doc.close()

        if not texto_extraido.strip():
            return Response(
                json.dumps(criar_json_erro('PDF não contém texto extraível'), indent=2),
                mimetype='application/json'
            ), 400

        print("Texto extraído do PDF:")
        print(texto_extraido[:1000])

    except Exception as e:
        print(f"Erro ao processar PDF: {str(e)}")
        return Response(
            json.dumps(criar_json_erro(f'Erro ao processar PDF: {str(e)}'), indent=2),
            mimetype='application/json'
        ), 500

    print("\nEnviando texto para processamento LLaMA...")
    resposta_llama = processar_nfse(texto_extraido)
    if not resposta_llama:
        print("Falha na resposta da API LLaMA")
        return Response(
            json.dumps(criar_json_erro('Falha ao processar NFSe com a LLaMA'), indent=2),
            mimetype='application/json'
        ), 500

    print("\nResposta LLaMA COMPLETA:")
    print(resposta_llama)

    print("\nExtraindo JSON válido...")
    dados_json = extrair_json_valido(resposta_llama)
    print("\nJSON final a ser enviado:")
    print(json.dumps(dados_json, indent=2))

    if export_base64:
        
        dados_json['dados']['arquivo']['base64'] = pdf_base64

    return Response(
        json.dumps(dados_json, indent=2),
        mimetype='application/json'
    )
 
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5050))
    app.run(debug=False, port=port, host='0.0.0.0')
 
 