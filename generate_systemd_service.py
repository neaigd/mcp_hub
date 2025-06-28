import yaml
import os

# Caminhos
template_file = 'mcp-hub.service.template'
config_file = 'config.yaml'
output_file = 'mcp-hub.service' # O nome final do arquivo de serviço

# Carregar configurações do YAML
with open(config_file, 'r') as f:
    config = yaml.safe_load(f)

# Carregar o template
with open(template_file, 'r') as f:
    template_content = f.read()

# Substituir placeholders
generated_content = template_content.replace('{{PROJECT_ROOT}}', config['project_root'])

# Escrever o arquivo de saída
with open(output_file, 'w') as f:
    f.write(generated_content)

print(f"Arquivo '{output_file}' gerado com sucesso.")