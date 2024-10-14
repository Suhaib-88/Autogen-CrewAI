from flask import Flask
from .cli import PraisonAI
import markdown

app= Flask(__name__)

def basic():
    praiseon_ai= PraisonAI(agent_file= "agents/basic.yaml")
    return praiseon_ai.run()

def home():
    output= basic()
    html_output= markdown.markdown(output)
    return f"<html> <body> {html_output} </body> </html>"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)

