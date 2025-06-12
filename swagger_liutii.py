from flask import Flask, jsonify, request
from flasgger import Swagger

app = Flask(__name__)

# Configuração do Swagger
app.config['SWAGGER'] = {
    'title': 'Minha API de conversão de NFSE to Json',
    'uiversion': 3
}
swagger = Swagger(app)

@app.route('/conversor', methods=['GET'])
def soma():
    """
    Soma dois números
    ---
    parameters:
      - name: a
        in: query
        type: number
        required: true
        description: Primeiro número
      - name: b
        in: query
        type: number
        required: true
        description: Segundo número
    responses:
      200:
        description: Resultado da soma
        examples:
          application/json: { "resultado": 3 }
    """
    a = float(request.args.get('a'))
    b = float(request.args.get('b'))
    return jsonify({'resultado': a + b})

if __name__ == '__main__':
    app.run(debug=True, port=5050)
    
# http://localhost:5050/apidocs link para acessar a documentação da API
# http://localhost:5050/soma?a=1&b=2 link para acessar a rota de soma