from flask import Flask, jsonify, request
import fitz
import requests
import json
from typing import Dict
from flasgger import Swagger
import xml.etree.ElementTree as ET


app = Flask(__name__)
LLAMA_API_URL = "http://dns.auditto.com.br:11434/v1/chat/completions"

# Configuração do Swagger
app.config['SWAGGER'] = {
    'title': 'Minha API de conversão de CTE to Json',
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


def cte_to_json(xml_content):
    JSON_TEMPLATE = {
        "cteProc": {
            "versao": "",
            "CTe": {
                "infCte": {
                    "versao": "",
                    "Id": "",
                    "ide": {
                        "cUF": "",
                        "cCT": "",
                        "CFOP": "",
                        "natOp": "",
                        "mod": "",
                        "serie": "",
                        "nCT": "",
                        "dhEmi": "",
                        "tpImp": "",
                        "tpEmis": "",
                        "cDV": "",
                        "tpAmb": "",
                        "tpCTe": "",
                        "procEmi": "",
                        "verProc": "",
                        "cMunEnv": "",
                        "xMunEnv": "",
                        "UFEnv": "",
                        "modal": "",
                        "tpServ": "",
                        "cMunIni": "",
                        "xMunIni": "",
                        "UFIni": "",
                        "cMunFim": "",
                        "xMunFim": "",
                        "UFFim": "",
                        "retira": "",
                        "indIEToma": "",
                        "toma3": {
                            "toma": ""
                        }
                    },
                    "compl": {
                        "xCaracAd": "",
                        "xCaracSer": "",
                        "xEmi": "",
                        "Entrega": {
                            "comData": {
                                "tpPer": "",
                                "dProg": ""
                            },
                            "comHora": {
                                "tpHor": "",
                                "hProg": ""
                            }
                        },
                        "xObs": ""
                    },
                    "emit": {
                        "CNPJ": "",
                        "IE": "",
                        "xNome": "",
                        "xFant": "",
                        "enderEmit": {
                            "xLgr": "",
                            "nro": "",
                            "xCpl": "",
                            "xBairro": "",
                            "cMun": "",
                            "xMun": "",
                            "CEP": "",
                            "UF": "",
                            "fone": ""
                        },
                        "CRT": ""
                    },
                    "rem": {
                        "CNPJ": "",
                        "IE": "",
                        "xNome": "",
                        "xFant": "",
                        "fone": "",
                        "enderReme": {
                            "xLgr": "",
                            "nro": "",
                            "xCpl": "",
                            "xBairro": "",
                            "cMun": "",
                            "xMun": "",
                            "CEP": "",
                            "UF": "",
                            "cPais": "",
                            "xPais": ""
                        },
                        "email": ""
                    },
                    "exped": {
                        "CNPJ": "",
                        "IE": "",
                        "xNome": "",
                        "fone": "",
                        "enderExped": {
                            "xLgr": "",
                            "nro": "",
                            "xCpl": "",
                            "xBairro": "",
                            "cMun": "",
                            "xMun": "",
                            "CEP": "",
                            "UF": "",
                            "cPais": "",
                            "xPais": ""
                        },
                        "email": ""
                    },
                    "dest": {
                        "CNPJ": "",
                        "IE": "",
                        "xNome": "",
                        "fone": "",
                        "enderDest": {
                            "xLgr": "",
                            "nro": "",
                            "xCpl": "",
                            "xBairro": "",
                            "cMun": "",
                            "xMun": "",
                            "CEP": "",
                            "UF": "",
                            "cPais": "",
                            "xPais": ""
                        },
                        "email": ""
                    },
                    "vPrest": {
                        "vTPrest": "",
                        "vRec": "",
                        "Comp": [
                            {
                                "xNome": "",
                                "vComp": ""
                            }
                        ]
                    },
                    "imp": {
                        "ICMS": {
                            "ICMS00": {
                                "CST": "",
                                "vBC": "",
                                "pICMS": "",
                                "vICMS": ""
                            }
                        },
                        "vTotTrib": ""
                    },
                    "infCTeNorm": {
                        "infCarga": {
                            "vCarga": "",
                            "proPred": "",
                            "infQ": [
                                {
                                    "cUnid": "",
                                    "tpMed": "",
                                    "qCarga": ""
                                }
                            ],
                            "vCargaAverb": ""
                        },
                        "infDoc": {
                            "infNFe": {
                                "chave": ""
                            }
                        },
                        "infModal": {
                            "versaoModal": "",
                            "rodo": {
                                "RNTRC": "",
                                "occ": {
                                    "nOcc": "",
                                    "dEmi": "",
                                    "emiOcc": {
                                        "CNPJ": "",
                                        "IE": "",
                                        "UF": "",
                                        "fone": ""
                                    }
                                }
                            }
                        }
                    },
                    "autXML": {
                        "CNPJ": ""
                    },
                    "infRespTec": {
                        "CNPJ": "",
                        "xContato": "",
                        "email": "",
                        "fone": ""
                    }
                },
                "infCTeSupl": {
                    "qrCodCTe": ""
                }
            }
        }
    }

    try:
        xml = fitz.open(stream=xml_content, filetype="xml")
        texto = ""
        for page in xml:
            texto += page.get_text()

        prompt = f"""
IMPORTANTE: Retorne apenas o JSON puro, sem nenhum texto, explicação, comentário ou código antes ou depois do JSON.
O JSON deve ser válido, sem comentários, sem vírgulas a mais ou a menos.
Use esta estrutura exata, preenchendo os campos com os dados do xml:

{json.dumps(JSON_TEMPLATE, ensure_ascii=False, indent=4)}
REGRAS:
1. Utilize exatamente a estrutura e a ordem dos campos do template JSON fornecido, sem alterar a sequência dos campos e sem adicionar ou remover campos.
2. Para cada campo do JSON, busque exatamente o valor correspondente no XML enviado. Não invente, não preencha com exemplos, não deixe campos em branco se houver valor no XML.
3. Separe corretamente os dados do EMISSOR e do TOMADOR, preenchendo cada um com suas respectivas informações. Não repita, copie ou misture dados entre eles.
4. Caso algum campo não seja encontrado no XML, preencha com uma string vazia ("").
5. Todos os campos do template devem estar presentes no JSON final, mesmo que vazios.
6. Não repita, duplique, aninhe ou adicione campos fora da estrutura do template.

TEXTO DA CTe:
\"\"\"{texto}\"\"\"
"""

        response = requests.post(
            LLAMA_API_URL,
            json={
                "model": "llama3",
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "temperature": 0.0,
                "format": "json"
            },
            timeout=30
        )
        response.raise_for_status()
        resposta_llama = response.json()
        json_llama = resposta_llama["choices"][0]["message"]["content"]

        # Debug: ver o que o Llama retornou
        print("Resposta Llama:", json_llama)

        # Tentar carregar o JSON, se falhar, retorna erro detalhado
        try:
            dados_llama = json.loads(json_llama)
        except Exception as e:
            # Tentar formatar o JSON bruto para facilitar a visualização
            try:
                json_llama_formatado = json.dumps(json.loads(json_llama), indent=4, ensure_ascii=False)
            except Exception:
                json_llama_formatado = json_llama  # Caso não consiga, mostrar como veio
            return {
                "sucesso": False,
                "mensagem": f"JSON inválido retornado pelo Llama: {str(e)}",
                "json_llama": json_llama_formatado
            }

        # Garantir a ordem do template
        return manter_ordem_json(JSON_TEMPLATE, dados_llama)
    except Exception as e:
        return {"sucesso": False, "mensagem": f"Erro ao processar: {str(e)}"}

@app.route('/ctetojson', methods=['POST'])
def converter_cte():
    """
    Converte um arquivo CTE (XML) para JSON
    ---
    consumes:
      - multipart/form-data
    parameters:
      - name: file
        in: formData
        type: file
        required: true
        description: Arquivo CTE em xml
    responses:
      200:
        description: JSON convertido
        examples:
          application/json: 
            CTeOS:
              versao: ""
              infCte: {}
    """
    file = request.files.get('file')
    if not file:
        return jsonify({'erro': 'Arquivo não enviado'}), 400
    xml_content = file.read()
    resultado = cte_to_json(xml_content)
    # Retornar o JSON formatado e na ordem correta
    return app.response_class(
        response=json.dumps(resultado, ensure_ascii=False, indent=4),
        status=200,
        mimetype='application/json'
    )

if __name__ == '__main__':
    app.run(debug=True, port=5050)

# http://localhost:5050/apidocs endpoint para converter CTE para JSON