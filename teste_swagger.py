from flask import Flask, jsonify, request
import fitz
import requests
import json
from typing import Dict
from flasgger import Swagger

app = Flask(__name__)
LLAMA_API_URL = "http://dns.auditto.com.br:11434/v1/chat/completions"

# Configuração do Swagger
app.config['SWAGGER'] = {
    'title': 'Minha API de conversão de NFSE to Json',
    'uiversion': 3
}
swagger = Swagger(app)

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

def nfse_to_json(pdf_content):
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
    try:
        pdf = fitz.open(stream=pdf_content, filetype="pdf")
        texto = ""
        for page in pdf:
            texto += page.get_text()

        prompt = f"""
RETORNE APENAS O JSON, sem nenhum texto adicional.
O JSON deve ser válido, sem comentários, sem vírgulas a mais ou a menos.
Use esta estrutura exata, preenchendo os campos com os dados do texto:

{json.dumps(JSON_TEMPLATE, ensure_ascii=False, indent=4)}
REGRAS:
1. Mantenha a estrutura exata do  JSON, não traga em ordem alfabética, mantenha a ordem do template.
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
\"\"\"{texto}\"\"\"
"""
        response = requests.post(
            LLAMA_API_URL,
            json={
                "model": "llama3",
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "format": "json"
            },
            timeout=30
        )
        response.raise_for_status()
        resposta_llama = response.json()
        json_llama = resposta_llama["choices"][0]["message"]["content"]

        # Debug: ver o que o Llama retornou
        print("Resposta Llama:", json_llama)

        #tentar carregar o JSON, se falhar, retorna erro detalhado
        try:
            dados_llama = json.loads(json_llama)
        except Exception as e:
            #tentar formatar o JSON bruto para facilitar a visualização
            try:
                json_llama_formatado = json.dumps(json.loads(json_llama), indent=4, ensure_ascii=False)
            except Exception:
                json_llama_formatado = json_llama  #caso não consiga, mostrar como veio
            return {
                "sucesso": False,
                "mensagem": f"JSON inválido retornado pelo Llama: {str(e)}",
                "json_llama": json_llama_formatado
            }

        #garantir a ordem do template
        return manter_ordem_json(JSON_TEMPLATE, dados_llama)
    except Exception as e:
        return {"sucesso": False, "mensagem": f"Erro ao processar: {str(e)}"}

@app.route('/nfsetojson', methods=['POST'])
def converter_nfse():
    """
    Converte um arquivo NFSE (PDF) para JSON
    ---
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: Arquivo NFSE em PDF
    responses:
      200:
        description: JSON convertido
        examples:
          application/json: { "sucesso": True, "mensagem": "", "dados": { ... } }
    """
    file = request.files.get('file')
    if not file:
        return jsonify({'erro': 'Arquivo não enviado'}), 400
    pdf_content = file.read()
    resultado = nfse_to_json(pdf_content)
    # Retornar o JSON formatado e na ordem correta
    return app.response_class(
        response=json.dumps(resultado, ensure_ascii=False, indent=4),
        status=200,
        mimetype='application/json'
    )

if __name__ == '__main__':
    app.run(debug=True, port=5050)