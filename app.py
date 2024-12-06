from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
from weasyprint import HTML
import os

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Alterar para um valor seguro

# Definir o diretório onde os arquivos gerados serão salvos
GENERATED_DIR = "generated"
os.makedirs(GENERATED_DIR, exist_ok=True)

# Formulário para preenchimento dos dados do contrato
class ContractForm(FlaskForm):
    cliente_nome = StringField("Nome do Cliente", validators=[DataRequired()])
    cliente_endereco = StringField("Endereço do Cliente", validators=[DataRequired()])
    empresa_nome = StringField("Nome da Empresa", validators=[DataRequired()])
    data_contrato = StringField("Data do Contrato", validators=[DataRequired()])
    submit = SubmitField("Pré-visualizar Contrato")

@app.route("/", methods=["GET", "POST"])
def form():
    form = ContractForm()
    if form.validate_on_submit():
        session["cliente_nome"] = form.cliente_nome.data
        session["cliente_endereco"] = form.cliente_endereco.data
        session["empresa_nome"] = form.empresa_nome.data
        session["data_contrato"] = form.data_contrato.data
        return redirect(url_for("preview"))
    return render_template("form.html", form=form)


@app.route("/preview")
def preview():
    """Exibe a pré-visualização do contrato."""
    cliente_nome = session.get("cliente_nome")
    cliente_endereco = session.get("cliente_endereco")
    empresa_nome = session.get("empresa_nome")
    data_contrato = session.get("data_contrato")

    if not (cliente_nome and cliente_endereco and empresa_nome and data_contrato):
        return redirect(url_for("form"))

    # Carregar o template de contrato
    with open("contratos/contrato_padrao.txt", "r", encoding="utf-8") as f:
        contrato_template = f.read()

    # Substituir as variáveis no template
    contrato = contrato_template.format(
        cliente_nome=cliente_nome,
        cliente_endereco=cliente_endereco,
        empresa_nome=empresa_nome,
        data_contrato=data_contrato
    )
    return render_template("preview.html", contrato=contrato)

@app.route("/generate", methods=["POST"])
def generate():
    """Gera o PDF após a pré-visualização."""
    cliente_nome = session.get("cliente_nome")
    cliente_endereco = session.get("cliente_endereco")
    data_contrato = session.get("data_contrato")

    if not (cliente_nome and cliente_endereco and data_contrato):
        return "Erro: Dados do contrato estão incompletos.", 400

    try:
        # Carregar o template de contrato
        with open("contratos/contrato_padrao.txt", "r") as f:
            contrato_template = f.read()

        # Substituir as variáveis no template
        contrato = contrato_template.format(
            cliente_nome=cliente_nome,
            cliente_endereco=cliente_endereco,
            data_contrato=data_contrato
        )

        # Salvar como arquivo HTML temporário
        contrato_html_path = os.path.join(GENERATED_DIR, f"contrato_{cliente_nome}.html")
        with open(contrato_html_path, "w", encoding="utf-8") as f:
            f.write(contrato)

        # Converter para PDF
        pdf_path = os.path.join(GENERATED_DIR, f"contrato_{cliente_nome}.pdf")
        HTML(contrato_html_path).write_pdf(pdf_path)

        return redirect(url_for("contracts"))

    except Exception as e:
        return f"Erro ao gerar o contrato: {e}", 500

@app.route("/contracts")
def contracts():
    """Exibe a lista de contratos gerados."""
    files = [
        f for f in os.listdir(GENERATED_DIR)
        if f.endswith(".pdf")
    ]
    return render_template("contratos.html", files=files)


@app.route("/download/<filename>")
def download(filename):
    """Serve o arquivo PDF gerado."""
    file_path = os.path.join(GENERATED_DIR, filename)
    if os.path.exists(file_path):
        return send_from_directory(GENERATED_DIR, filename, as_attachment=True)
    return "Arquivo não encontrado", 404

if __name__ == "__main__":
    app.run(debug=True)
